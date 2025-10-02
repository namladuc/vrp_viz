from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np

import time
import requests
import folium
from folium.plugins import (
    MiniMap,
    Fullscreen,
    MeasureControl,
    MousePosition,
    MarkerCluster,
    BeautifyIcon,
    AntPath,
)
from branca.element import MacroElement, Template

BASE_URL = "https://router.project-osrm.org"
PROFILE = "driving"

_VEHICLE_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def _veh_color(veh_id: int) -> str:
    return _VEHICLE_COLORS[veh_id % len(_VEHICLE_COLORS)]


def _html_overlay_box(title: str, html_body: str) -> MacroElement:
    """Tạo ô mô tả cố định góc phải, có thể ẩn/hiện bằng layer control."""
    tmpl = Template(
        f"""
    {{% macro html(this, kwargs) %}}
    <div id="vrp-info-box" style="
        position: fixed; 
        top: 10px; right: 10px; 
        z-index: 1000; 
        background: rgba(255,255,255,0.95); 
        padding: 12px 14px; 
        border-radius: 10px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 360px; font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
        ">
      <div style="font-weight:600; margin-bottom:6px;">{title}</div>
      <div style="font-size: 13px; line-height: 1.35;">{html_body}</div>
    </div>
    {{% endmacro %}}
    """
    )
    el = MacroElement()
    el._template = tmpl
    return el


def get_route_from_api(coords, names: List[str]):
    route_url = f"{BASE_URL}/route/v1/{PROFILE}/{coords}?overview=full&geometries=geojson&steps=false"
    try:
        r = requests.get(
            route_url, headers={"User-Agent": "VRP-MapDemo/1.0"}, timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                geo = data["routes"][0]["geometry"]
                if geo and geo.get("type") == "LineString":
                    return geo, data
            else:
                print(f"Route API không trả Ok cho {names[1]}")
        else:
            print(f"HTTP {r.status_code} khi gọi route {names[1]}")
    except Exception as ex:
        print("Lỗi route:", ex)
    return None, None


class VRPResult:
    def __init__(
        self, routes: List[List[int]], route_lengths: List[float], steps: List[Dict]
    ):
        """
        routes: danh sách tuyến, mỗi tuyến là danh sách chỉ số điểm (theo input points, 0=depot).
        route_lengths: tổng độ dài (m) mỗi tuyến.
        steps: danh sách các bước để visualize (edge thêm theo thứ tự).
              Mỗi step: {"vehicle": k, "from": i, "to": j}
        """
        self.routes = routes
        self.route_lengths = route_lengths
        self.steps = steps


def make_stepwise_map(
    names: List[str],
    points_latlon: List[Tuple[float, float]],
    node_ids: List[int],
    vrp: VRPResult,
    out_html: str = "vrp_stepwise_map.html",
) -> str:
    """
    Tạo bản đồ Folium với:
      - markers cho depot & khách hàng
      - layer theo từng 'step' của heuristic
      - layer gộp theo từng 'route'
    """
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(
        location=center, zoom_start=12, control_scale=True, prefer_canvas=True
    )

    # Markers
    folium.Marker(
        points_latlon[0], tooltip="Depot", icon=folium.Icon(color="green")
    ).add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker(
            (lat, lon), radius=5, tooltip=f"Point {idx}", fill=True
        ).add_to(m)

    # Layer per route
    for r_id, route in enumerate(vrp.routes):
        fg = folium.FeatureGroup(name=f"Route #{r_id}")
        # vẽ từng edge trong route
        for a, b in zip(route[:-1], route[1:]):
            u, v = node_ids[a], node_ids[b]
            name_u, name_v = names[u], names[v]
            geom, data_map = get_route_from_api(
                coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
                names=[name_u, name_v],
            )
            if geom is None:
                print(f"Không lấy được route {name_u} -> {name_v}")
                continue
            line_coords = [[latlon[1], latlon[0]] for latlon in geom["coordinates"]]
            folium.PolyLine(
                locations=line_coords,
                color="orange",
                weight=3,
                opacity=0.8,
                tooltip=f"Route {names[0]} -> {names[1]} ({data_map['routes'][0]['distance']/1000:.2f} km)",
            ).add_to(fg)
            time.sleep(0.3)  # tránh spam
        fg.add_to(m)

    # Step-by-step layers
    for s_id, s in enumerate(vrp.steps, start=1):
        fg = folium.FeatureGroup(
            name=f"Step {s_id}: v{ s['vehicle'] } {s['from']}→{s['to']}"
        )
        u, v = node_ids[s["from"]], node_ids[s["to"]]
        name_u, name_v = names[u], names[v]
        geom, data_map = get_route_from_api(
            coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
            names=[name_u, name_v],
        )

        folium.PolyLine(
            locations=line_coords,
            color="orange",
            weight=3,
            opacity=0.8,
            tooltip=f"Route {names[0]} -> {names[1]} ({data_map['routes'][0]['distance']/1000:.2f} km)",
        ).add_to(fg)

        # đánh dấu đầu/cuối
        folium.CircleMarker(
            points_latlon[s["from"]], radius=6, tooltip=f"from {s['from']}", color="red"
        ).add_to(fg)
        folium.CircleMarker(
            points_latlon[s["to"]], radius=6, tooltip=f"to {s['to']}", color="blue"
        ).add_to(fg)
        fg.add_to(m)
        time.sleep(0.3)  # tránh spam

    folium.LayerControl().add_to(m)
    m.save(out_html)
    return out_html


def make_stepwise_map_v2(
    names: List[str],
    points_latlon: List[Tuple[float, float]],  # (lat, lon)
    node_ids: List[int],  # map index in route -> index in names/points_latlon
    vrp,  # VRPResult có .routes (list of node indices), .steps (list of dicts)
    out_html: str = "vrp_stepwise_map.html",
    description_html: str = None,  # cho phép truyền mô tả tuỳ ý (HTML)
    throttle_s: float = 0.15,  # hạn chế call API dày
) -> str:
    # — Map base —
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(
        location=center,
        zoom_start=12,
        control_scale=True,
        prefer_canvas=True,
        tiles="CartoDB positron",
    )

    # — Plugins tiện ích —
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    Fullscreen().add_to(m)
    MeasureControl(
        primary_length_unit="meters", secondary_length_unit="kilometers"
    ).add_to(m)
    MousePosition(position="bottomleft", separator=" | ", prefix="Lat/Lon").add_to(m)

    # — Overlay mô tả —
    if description_html is None:
        # tạo mô tả mặc định từ vrp
        n_routes = len(getattr(vrp, "routes", []))
        n_steps = len(getattr(vrp, "steps", []))
        description_html = (
            f"<b>Tổng quan:</b> {n_routes} route, {n_steps} bước.<br>"
            f"<span style='opacity:0.7'>Bật/tắt lớp ở góc phải – xem từng Step hoặc toàn bộ Route.</span>"
        )
    # m.get_root().add_child(_html_overlay_box("VRP – Stepwise Viewer", description_html))

    # — Markers: Depot & Customers (cluster) —
    depot_latlon = points_latlon[0]
    folium.Marker(
        depot_latlon,
        tooltip="Depot",
        popup=folium.Popup(f"<b>Depot</b><br>{names[0]}", max_width=260),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(m)

    cluster = MarkerCluster(name="Customers").add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker(
            (lat, lon),
            radius=5,
            fill=True,
            weight=1,
            fill_opacity=0.9,
            tooltip=f"Customer #{idx}: {names[idx]}",
            popup=folium.Popup(
                f"<b>Customer #{idx}</b><br/>{names[idx]}<br/>lat: {lat:.6f}, lon: {lon:.6f}",
                max_width=280,
            ),
        ).add_to(cluster)

    # — Vẽ từng Route (gộp) —
    all_poly_bounds = []
    for r_id, route in enumerate(getattr(vrp, "routes", [])):
        color = _veh_color(r_id)
        fg = folium.FeatureGroup(name=f"Route #{r_id}", show=False)
        total_dist_km = 0.0
        # vẽ từng cạnh theo thứ tự
        for a, b in zip(route[:-1], route[1:]):
            u, v = node_ids[a], node_ids[b]
            name_u, name_v = names[u], names[v]
            # chú ý: API cần lon,lat
            geom, data_map = get_route_from_api(
                coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
                names=[name_u, name_v],
            )
            if geom is None:
                print(f"Không lấy được route {name_u} -> {name_v}")
                continue

            # GeoJSON LineString -> Folium expects list of [lat, lon]
            line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
            all_poly_bounds.extend(line_coords)
            dist_m = data_map["routes"][0].get("distance", 0.0)
            dur_s = data_map["routes"][0].get("duration", 0.0)
            total_dist_km += dist_m / 1000.0

            AntPath(
                locations=line_coords,
                tooltip=f"{name_u} → {name_v} • {dist_m/1000:.2f} km • {dur_s/60:.1f} min",
                delay=600,
                dash_array=[10, 20],
                weight=4,
                opacity=0.85,
                color=color,
            ).add_to(fg)
            time.sleep(throttle_s)

        # nhãn tổng kết route
        if route:
            first_idx = node_ids[route[0]]
            folium.Marker(
                points_latlon[first_idx],
                icon=BeautifyIcon(
                    icon="route",
                    icon_shape="marker",
                    border_color=color,
                    text_color=color,
                    number=r_id,
                ),
                tooltip=f"Route #{r_id} • ~{total_dist_km:.2f} km",
                popup=f"<b>Route #{r_id}</b><br/>Tổng chiều dài ~{total_dist_km:.2f} km",
            ).add_to(fg)
        fg.add_to(m)

    # — Step-by-Step layers (từng bước heuristic) —
    for s_id, s in enumerate(getattr(vrp, "steps", []), start=1):
        veh = s.get("vehicle", 0)
        color = _veh_color(veh)
        from_idx, to_idx = s["from"], s["to"]
        fg = folium.FeatureGroup(
            name=f"Step {s_id}: v{veh} • {from_idx} → {to_idx}",
            show=(s_id == 1),  # bật sẵn step 1 cho rõ
        )

        u, v = node_ids[from_idx], node_ids[to_idx]
        name_u, name_v = names[u], names[v]
        geom, data_map = get_route_from_api(
            coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
            names=[name_u, name_v],
        )
        if geom is None:
            print(f"Không lấy được step {name_u} -> {name_v}")
            continue
        line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
        all_poly_bounds.extend(line_coords)

        dist_m = data_map["routes"][0].get("distance", 0.0)
        dur_s = data_map["routes"][0].get("duration", 0.0)

        # đường nhấn mạnh + animate
        AntPath(
            locations=line_coords,
            tooltip=f"Step {s_id} • v{veh} • {name_u} → {name_v} • {dist_m/1000:.2f} km • {dur_s/60:.1f} min",
            delay=400,
            dash_array=[1, 8],
            weight=6,
            opacity=0.95,
            color=color,
        ).add_to(fg)

        # đánh dấu from/to với số thứ tự step
        folium.Marker(
            points_latlon[u],
            tooltip=f"from #{from_idx}: {name_u}",
            icon=BeautifyIcon(
                icon="play",
                number=s_id,
                border_color=color,
                text_color=color,
                background_color="white",
            ),
        ).add_to(fg)
        folium.Marker(
            points_latlon[v],
            tooltip=f"to #{to_idx}: {name_v}",
            icon=BeautifyIcon(
                icon="flag",
                border_color=color,
                text_color=color,
                background_color="white",
            ),
        ).add_to(fg)

        # popup chi tiết
        folium.Popup(
            html=f"<b>Step {s_id}</b><br/>Vehicle: v{veh}<br/>{name_u} → {name_v}<br/>{dist_m/1000:.2f} km • {dur_s/60:.1f} min",
            max_width=300,
        ).add_to(fg)

        fg.add_to(m)
        time.sleep(throttle_s)

    # — Fit to bounds (bao trọn mọi polyline/điểm) —
    if all_poly_bounds:
        lats = [p[0] for p in all_poly_bounds] + [lat for lat, _ in points_latlon]
        lons = [p[1] for p in all_poly_bounds] + [lon for _, lon in points_latlon]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(out_html)
    return out_html

if __name__ == "__main__":
    # --- Thay chuỗi coords dưới đây bằng chuỗi "lon,lat;lon,lat;..." bạn muốn test ---
    coords = "100.5018,13.7563;100.5130,13.7367"  # ví dụ: hai điểm ở Bangkok (lon,lat;lon,lat)
    names = ["start", "end"]

    geo, full = get_route_from_api(coords, names)
    print("Full response:", full)
    if geo is None:
        print("Không có geometry trả về.")
    else:
        coords_list = geo.get("coordinates", [])
        print("Geometry type:", geo.get("type"))
        print("Tổng điểm trong geometry:", len(coords_list))
        if coords_list:
            print("First coordinate:", coords_list[0])
            print("Last coordinate:", coords_list[-1])
        # nếu cần, in toàn bộ geo (cẩn thận nếu dài)
        # print("Full geometry:", geo)
        # in tóm tắt response nếu muốn debug
        # import json; print(json.dumps(full, indent=2))