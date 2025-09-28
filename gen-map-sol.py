import pandas as pd
import numpy as np

import requests
import folium
from folium.plugins import MarkerCluster
import urllib.parse, time

if __name__ == "__main__":
    warehouse_info = {
        "name": "Điểm dịch vụ SPX Hà Nội - Đống Đa 5",
        "address": "530 Láng, P. Láng Hạ",
        "lat": 21.011257,
        "lng": 105.810770,
        "ward": "Phường Đống Đa",
        "post_office": "Bưu cục shopee",
    }
    customers_df = pd.read_csv("data/map-viz/vrp_customers_dev.csv")
    all_locations_df = pd.read_csv("data/map-viz/vrp_locations_dev.csv")

    USE_MARKER_CLUSTER = True  # Đổi về False nếu muốn hiển thị tất cả marker riêng lẻ
    DRAW_SAMPLE_ROUTES = True  # Vẽ một số tuyến đường thực tế từ kho tới khách
    SAMPLE_ROUTES_MAX = 5  # Số tuyến tối đa để tránh spam API OSRM
    ROUTE_SELECTION_MODE = "nearest"  # 'nearest' hoặc 'random'
    N_CUSTOMERS = 5  # number_customer + 1 warehouse <= 100 limit of OSRM demo
    RADIUS_KM = 2
    MIN_PACKAGES = 1
    MAX_PACKAGES = 5
    AVERAGE_SPEED_KMH = 25  # fallback travel speed

    customers_for_map = all_locations_df[
        all_locations_df["customer_id"] != "WAREHOUSE"
    ].copy()
    center_lat = warehouse_info["lat"]
    center_lng = warehouse_info["lng"]

    m = folium.Map(
        location=[center_lat, center_lng], zoom_start=13, tiles="OpenStreetMap"
    )

    folium.Marker(
        location=[warehouse_info["lat"], warehouse_info["lng"]],
        popup=f"<b>{warehouse_info['name']}</b><br>{warehouse_info['address']}",
        tooltip="Kho hàng",
        icon=folium.Icon(color="red", icon="home"),
    ).add_to(m)

    folium.Circle(
        location=[center_lat, center_lng],
        radius=RADIUS_KM * 1000,  # Chuyển km thành mét
        popup=f"Bán kính {RADIUS_KM} km",
        color="green",
        fill=False,
        dash_array="5, 5",
    ).add_to(m)

    # Container cho marker khách hàng
    if USE_MARKER_CLUSTER and len(customers_for_map) > 20:
        marker_container = MarkerCluster(name="Khách hàng").add_to(m)
    else:
        marker_container = m

    # Thêm marker cho khách hàng
    for _, customer in customers_for_map.iterrows():
        # Chọn khoảng cách hiển thị: ưu tiên road nếu đã có, fallback Haversine
        road_val = customer.get("road_from_warehouse_km")
        if pd.notna(road_val):
            dist_label = f"{float(road_val):.2f} km (road)"
        else:
            dist_label = f"{customer['distance_from_warehouse_km']:.2f} km (hav)"
        popup_content = (
            f"<b>{customer['name']}</b><br>"
            f"<b>ID:</b> {customer['customer_id']}<br>"
            f"<b>Địa chỉ:</b> {customer['address']}<br>"
            f"<b>Thành phố:</b> {customer['city']}<br>"
            f"<b>Gói hàng:</b> {customer['packages']}<br>"
            f"<b>Khoảng cách:</b> {dist_label}"
            + (
                f"<br><b>Haversine:</b> {customer['distance_from_warehouse_km']:.2f} km"
                if pd.notna(road_val)
                else ""
            )
        )
        folium.Marker(
            location=[customer["lat"], customer["lng"]],
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=f"{customer['customer_id']}: {customer['packages']} gói",
            icon=folium.Icon(color="blue", icon="shopping-cart"),
        ).add_to(marker_container)

    if DRAW_SAMPLE_ROUTES and len(customers_for_map):
        base_url = "https://router.project-osrm.org"  # public demo
        profile = "driving"
        # Chọn tập khách
        if (
            ROUTE_SELECTION_MODE == "nearest"
            and "road_from_warehouse_km" in customers_for_map.columns
            and customers_for_map["road_from_warehouse_km"].notna().any()
        ):
            # Sắp xếp theo road nếu có; nếu nhiều null sẽ rơi về haversine
            customers_for_map = customers_for_map.copy()
            customers_for_map["__order_metric"] = customers_for_map[
                "road_from_warehouse_km"
            ].fillna(customers_for_map["distance_from_warehouse_km"])
            sample_customers = customers_for_map.nsmallest(
                SAMPLE_ROUTES_MAX, "__order_metric"
            )
        else:
            sample_customers = customers_for_map.sample(
                min(SAMPLE_ROUTES_MAX, len(customers_for_map)), random_state=42
            )

        for _, cust in sample_customers.iterrows():
            coords = f"{warehouse_info['lng']},{warehouse_info['lat']};{cust['lng']},{cust['lat']}"
            # Dùng geometries=geojson để khỏi decode polyline
            route_url = f"{base_url}/route/v1/{profile}/{coords}?overview=full&geometries=geojson&steps=false"
            try:
                r = requests.get(
                    route_url, headers={"User-Agent": "VRP-MapDemo/1.0"}, timeout=20
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        geo = data["routes"][0]["geometry"]
                        if geo and geo.get("type") == "LineString":
                            line_coords = [
                                [latlon[1], latlon[0]] for latlon in geo["coordinates"]
                            ]  # lon,lat -> lat,lon
                            folium.PolyLine(
                                locations=line_coords,
                                color="orange",
                                weight=3,
                                opacity=0.8,
                                tooltip=f"Route {warehouse_info['name']} -> {cust['customer_id']} ({data['routes'][0]['distance']/1000:.2f} km)",
                            ).add_to(m)
                    else:
                        print(f"Route API không trả Ok cho {cust['customer_id']}")
                else:
                    print(f"HTTP {r.status_code} khi gọi route {cust['customer_id']}")
                time.sleep(0.3)  # tránh spam
            except Exception as ex:
                print("Lỗi route:", ex)

    
    # Thêm lớp điều khiển nếu có cluster
    folium.LayerControl().add_to(m)

    # Lưu bản đồ
    map_file = f"maps/vrp_locations_dev.html"
    m.save(map_file)
    print(f"Đã tạo bản đồ minh họa: {map_file}")
    print("Mở file HTML để xem bản đồ tương tác hoặc xem trực tiếp bên dưới.")
    print(f"Đã vẽ {min(len(customers_for_map), SAMPLE_ROUTES_MAX) if DRAW_SAMPLE_ROUTES else 0} tuyến mẫu (nếu không bị lỗi).")