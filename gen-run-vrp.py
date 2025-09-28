from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np

import requests
import folium
from folium.plugins import MarkerCluster
import urllib.parse, time

from vrp_viz.map_viz.stepwise_map import make_stepwise_map, VRPResult


def nearest_neighbor_vrp(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,
    num_vehicles: int = 1,
    depot_idx: int = 0,
) -> VRPResult:
    """
    Heuristic VRP đơn giản dựa trên nearest neighbor + ràng buộc capacity hoặc max stops.
    - D: ma trận khoảng cách (m), D[i,j] >= 0; D[i,i]=0
    - demands: list demand cho từng node (cùng kích thước với D). depot demand = 0.
    - vehicle_capacity: tổng demand tối đa/xe (nếu None -> bỏ qua)
    - max_stops_per_route: tối đa số khách/xe (không tính depot). None -> bỏ qua
    - num_vehicles: số xe
    - depot_idx: chỉ số depot trong D
    """
    n = D.shape[0]
    unserved = set(range(n)) - {depot_idx}
    if demands is None:
        demands = [0.0] * n

    routes = []
    lengths = []
    steps = []

    for k in range(num_vehicles):
        route = [depot_idx]
        load = 0.0
        used_stops = 0
        current = depot_idx
        route_len = 0.0

        while unserved:
            # Lọc ứng viên hợp lệ theo capacity/max_stops
            candidates = []
            for j in unserved:
                # check capacity
                capacity_ok = True
                if vehicle_capacity is not None:
                    capacity_ok = (load + demands[j]) <= vehicle_capacity
                stops_ok = True
                if max_stops_per_route is not None:
                    stops_ok = (used_stops + 1) <= max_stops_per_route
                if capacity_ok and stops_ok and np.isfinite(D[current, j]):
                    candidates.append(j)

            if not candidates:
                # Không còn điểm hợp lệ → đóng tuyến, quay về depot
                if current != depot_idx and np.isfinite(D[current, depot_idx]):
                    route.append(depot_idx)
                    route_len += D[current, depot_idx]
                    steps.append({"vehicle": k, "from": current, "to": depot_idx})
                break

            # Chọn điểm gần nhất
            j_star = min(candidates, key=lambda j: D[current, j])
            route.append(j_star)
            route_len += D[current, j_star]
            steps.append({"vehicle": k, "from": current, "to": j_star})

            # Cập nhật
            load += demands[j_star]
            used_stops += 1
            current = j_star
            unserved.remove(j_star)

        # đảm bảo kết thúc ở depot
        if route[-1] != depot_idx:
            if np.isfinite(D[current, depot_idx]):
                route.append(depot_idx)
                route_len += D[current, depot_idx]
                steps.append({"vehicle": k, "from": current, "to": depot_idx})

        if len(route) > 1:
            routes.append(route)
            lengths.append(route_len)

        # Nếu còn điểm mà hết xe, vòng lặp tiếp xe mới.
        if not unserved:
            break

    # Nếu còn điểm và đã hết xe → cho vào tuyến cuối (không capacity)
    if unserved and routes:
        last = routes[-1]
        current = last[-2] if len(last) >= 2 else depot_idx
        for j in list(unserved):
            if np.isfinite(D[current, j]):
                last.insert(-1, j)  # thêm trước depot
                steps.append({"vehicle": len(routes) - 1, "from": current, "to": j})
                lengths[-1] += D[current, j] + D[j, depot_idx] - D[current, depot_idx]
                current = j
                unserved.remove(j)
        # đảm bảo kết thúc depot (đã có)

    return VRPResult(routes=routes, route_lengths=lengths, steps=steps)


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
    distance_matrix_df = pd.read_csv("data/map-viz/vrp_distances_dev.csv")

    USE_MARKER_CLUSTER = True  # Đổi về False nếu muốn hiển thị tất cả marker riêng lẻ
    DRAW_SAMPLE_ROUTES = True  # Vẽ một số tuyến đường thực tế từ kho tới khách
    SAMPLE_ROUTES_MAX = 5  # Số tuyến tối đa để tránh spam API OSRM
    ROUTE_SELECTION_MODE = "nearest"  # 'nearest' hoặc 'random'
    N_CUSTOMERS = 5  # number_customer + 1 warehouse <= 100 limit of OSRM demo
    RADIUS_KM = 2
    MIN_PACKAGES = 1
    MAX_PACKAGES = 5
    AVERAGE_SPEED_KMH = 25  # fallback travel speed

    D = distance_matrix_df.to_numpy()[:, 1:]
    print(D)
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
    print("Points:", points)

    print("Demands:", demands)
    vehicle_capacity = 10  # tổng gói/xe
    max_stops_per_route = None
    num_vehicles = 3
    depot_idx = 0

    vrp = nearest_neighbor_vrp(
        D,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        max_stops_per_route=max_stops_per_route,
        num_vehicles=num_vehicles,
        depot_idx=depot_idx,
    )

    for k, (route, dist_m) in enumerate(zip(vrp.routes, vrp.route_lengths)):
        print(f"Vehicle {k}: route {route}, length = {dist_m/1000:.4f} km")

    out = make_stepwise_map(names, points, node_ids, vrp, out_html="vrp_stepwise_map.html")
    print(f"Map saved to: {out}  (mở file HTML này để xem từng bước)")
