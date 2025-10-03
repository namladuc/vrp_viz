from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np

import json
import time
import requests
import folium
from folium.plugins import MarkerCluster
import urllib.parse

from vrp_viz.cheapest_insertion.viz_cheapest_insertion import cheapest_insertion
from vrp_viz.local_search.shift import shift_local_search
from vrp_viz.local_search.two_opt_star import two_opt_star_local_search
from vrp_viz.map_viz.stepwise_map import make_stepwise_map, VRPResult
from vrp_viz.map_viz.stepwise_map import make_stepwise_map_v2
from vrp_viz.map_viz.stepwise_mapv2 import make_stepwise_map as make_stepwise_map_v3
from vrp_viz.nearest_neighbor.viz_nearnest_neighbor import nearest_neighbor_v2


if __name__ == "__main__":
    warehouse_info = {
        "name": "Điểm dịch vụ SPX Hà Nội - Đống Đa 5",
        "address": "530 Láng, P. Láng Hạ",
        "lat": 21.011257,
        "lng": 105.810770,
        "ward": "Phường Đống Đa",
        "post_office": "Bưu cục shopee",
    }
    read_time = time.time()
    customers_df = pd.read_csv("data/map-viz/data20/vrp_customers_dev.csv")
    all_locations_df = pd.read_csv("data/map-viz/data20/vrp_locations_dev.csv")
    distance_matrix_df = pd.read_csv("data/map-viz/data20/vrp_distances_dev.csv")
    end_read_time = time.time()
    print(f"Đọc dữ liệu xong trong {end_read_time - read_time:.2f} giây")
    
    # USE_MARKER_CLUSTER = True  # Đổi về False nếu muốn hiển thị tất cả marker riêng lẻ
    # DRAW_SAMPLE_ROUTES = True  # Vẽ một số tuyến đường thực tế từ kho tới khách
    # SAMPLE_ROUTES_MAX = 999  # Số tuyến tối đa để tránh spam API OSRM
    # ROUTE_SELECTION_MODE = "nearest"  # 'nearest' hoặc 'random'
    # N_CUSTOMERS = 5  # number_customer + 1 warehouse <= 100 limit of OSRM demo
    # RADIUS_KM = 2
    # MIN_PACKAGES = 1
    # MAX_PACKAGES = 5
    # AVERAGE_SPEED_KMH = 25  # fallback travel speed

    process_time = time.time()
    D = distance_matrix_df.to_numpy()[:, 1:]
    D = np.array(D, dtype=float)
    list_customer = distance_matrix_df.columns.tolist()[2:]
    demands = [
        0,
        *[
            int(
                customers_df.loc[customers_df["customer_id"] == cid, "packages"].values[
                    0
                ]
            )
            for cid in list_customer
        ],
    ]
    points = [
        (float(warehouse_info["lat"]), float(warehouse_info["lng"])),
        *[
            (
                float(customers_df.loc[customers_df["customer_id"] == cid, "lat"].values[0]),
                float(customers_df.loc[customers_df["customer_id"] == cid, "lng"].values[0]),
            )
            for cid in list_customer
        ],
    ]
    names = [
        warehouse_info["name"],
        *[
            customers_df.loc[customers_df["customer_id"] == cid, "name"].values[0]
            for cid in list_customer
        ],
    ]
    node_ids = list(range(len(points)))  # Giả sử
    print("Distance matrix shape:", D.shape)
    print("Distance matrix type:", D.dtype)
    print("Demands:", demands)
    vehicle_capacity = 5  # tổng gói/xef
    max_stops_per_route = None
    num_vehicles = 9999
    depot_idx = 0

    vrp = cheapest_insertion(
        D,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        max_stops_per_route=max_stops_per_route,
        num_vehicles=num_vehicles,
        depot_idx=depot_idx,
    )
    end_process_time = time.time()
    print(f"Xử lý VRP xong trong {end_process_time - process_time:.2f} giây")
    print("Cost after Cheapest Insertion:", sum(vrp[-1].route_lengths))
    # print(vrp[-1].routes)

    vrp = two_opt_star_local_search(
        D,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        max_stops_per_route=max_stops_per_route,
        num_vehicles=num_vehicles,
        depot_idx=depot_idx,
        current_solution=vrp[-1],
    )

    print("Cost after 2-opt*:", sum(vrp[-1].route_lengths))

    vrp = shift_local_search(
        D,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        max_stops_per_route=max_stops_per_route,
        num_vehicles=num_vehicles,
        depot_idx=depot_idx,
        current_solution=vrp[-1],
    )

    print("Cost after shift:", sum(vrp[-1].route_lengths))

    # draw_time = time.time()
    # for k, (route, dist_m) in enumerate(zip(vrp.routes, vrp.route_lengths)):
    #     print(f"Vehicle {k}: route {route}, length = {dist_m/1000:.4f} km")
    #
    # time_load_json = time.time()
    # cache_location = json.load(
    #     open("data/map-viz/vrp_routes_dev.json", "r", encoding="utf-8"))
    # end_load_json = time.time()
    # print(f"Đọc JSON cache xong trong {end_load_json - time_load_json:.2f} giây")
    #
    # print("key cache_location sample:", list(cache_location.keys())[:5])
    #
    # out = make_stepwise_map_v3(names, points, node_ids, vrp, cache_location, out_html="vrp_stepwise_map.html")
    # print(f"Map saved to: {out}  (mở file HTML này để xem từng bước)")
    # end_draw_time = time.time()
    # print(f"Vẽ bản đồ xong trong {end_draw_time - draw_time:.2f} giây")
    
    
