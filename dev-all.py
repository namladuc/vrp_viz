# ==== requirements ====
# pip install osmnx networkx folium numpy pandas shapely tqdm

from __future__ import annotations
import os
from typing import List, Tuple, Dict, Optional
import numpy as np
import networkx as nx
import osmnx as ox
import folium
from shapely.geometry import LineString, Point
from tqdm import tqdm
import geopandas as gpd
from shapely.geometry import box
import pyproj

# -----------------------------
# 1) TẢI GRAPH & CHUẨN BỊ DỮ LIỆU
# -----------------------------

def build_road_graph(points_latlon, buffer_m=3000):
    """
    Tạo road graph (OSM) bao quanh bbox các điểm với phần đệm chuẩn theo mét.
    buffer_m: khoảng cách đệm (m)
    """
    # 1. Lấy bbox (lat, lon)
    lats = [lat for lat, lon in points_latlon]
    lons = [lon for lat, lon in points_latlon]
    north, south = max(lats), min(lats)
    east, west = max(lons), min(lons)

    bbox_poly = box(west, south, east, north)
    gdf = gpd.GeoDataFrame(geometry=[bbox_poly], crs="EPSG:4326")

    # 2. Chuyển sang UTM gần nhất
    gdf_utm = gdf.to_crs(gdf.estimate_utm_crs())

    # 3. Buffer theo mét
    gdf_buffered = gdf_utm.buffer(buffer_m)

    # 4. Quay về WGS84
    gdf_wgs = gdf_buffered.to_crs("EPSG:4326")
    minx, miny, maxx, maxy = gdf_wgs.total_bounds
    west, south, east, north = minx, miny, maxx, maxy

    # 5. Tải graph đường
    G = ox.graph_from_bbox((north, south, east, west), network_type="drive")
    # G = ox.add_edge_lengths(G)
    return G

def snap_points_to_graph(G: nx.MultiDiGraph, points_latlon: List[Tuple[float, float]]) -> List[int]:
    """
    Ánh xạ (lat, lon) sang id nút gần nhất trên graph.
    """
    nodes = []
    for lat, lon in points_latlon:
        node = ox.nearest_nodes(G, X=lon, Y=lat)
        nodes.append(node)
    return nodes

def road_distance(G: nx.MultiDiGraph, u: int, v: int) -> float:
    """
    Khoảng cách đường đi ngắn nhất (m) giữa 2 node, theo trọng số 'length'.
    """
    try:
        dist = nx.shortest_path_length(G, u, v, weight="length")
    except nx.NetworkXNoPath:
        dist = np.inf
    return dist

def build_distance_matrix(G: nx.MultiDiGraph, node_ids: List[int]) -> np.ndarray:
    """
    Tạo ma trận khoảng cách (m) giữa mọi cặp node theo đường đi thực tế.
    """
    n = len(node_ids)
    D = np.zeros((n, n), dtype=float)
    for i in tqdm(range(n), desc="Distance matrix rows"):
        for j in range(n):
            if i == j:
                D[i, j] = 0.0
            else:
                D[i, j] = road_distance(G, node_ids[i], node_ids[j])
    return D

# -----------------------------
# 2) VRP NEAREST NEIGHBOR (ĐƠN GIẢN)
# -----------------------------

class VRPResult:
    def __init__(self, routes: List[List[int]], route_lengths: List[float], steps: List[Dict]):
        """
        routes: danh sách tuyến, mỗi tuyến là danh sách chỉ số điểm (theo input points, 0=depot).
        route_lengths: tổng độ dài (m) mỗi tuyến.
        steps: danh sách các bước để visualize (edge thêm theo thứ tự).
              Mỗi step: {"vehicle": k, "from": i, "to": j}
        """
        self.routes = routes
        self.route_lengths = route_lengths
        self.steps = steps

def nearest_neighbor_vrp(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,
    num_vehicles: int = 1,
    depot_idx: int = 0
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

# -----------------------------
# 3) TRUY VẾT HÀNH TRÌNH (HÌNH DẠNG ĐƯỜNG) & VẼ MAP
# -----------------------------

def path_geometry(G: nx.MultiDiGraph, u: int, v: int) -> LineString:
    """
    Trả về hình học đường đi ngắn nhất giữa 2 node trên graph (LineString).
    """
    path = nx.shortest_path(G, u, v, weight="length")
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]  # (lat, lon)
    print(coords)
    return LineString(coords)

def make_stepwise_map(
    G: nx.MultiDiGraph,
    points_latlon: List[Tuple[float, float]],
    node_ids: List[int],
    vrp: VRPResult,
    out_html: str = "vrp_stepwise_map.html"
) -> str:
    """
    Tạo bản đồ Folium với:
      - markers cho depot & khách hàng
      - layer theo từng 'step' của heuristic
      - layer gộp theo từng 'route'
    """
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(location=center, zoom_start=12, control_scale=True, prefer_canvas=True)

    # Markers
    folium.Marker(points_latlon[0], tooltip="Depot", icon=folium.Icon(color="green")).add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker((lat, lon), radius=5, tooltip=f"Point {idx}", fill=True).add_to(m)

    # Layer per route
    for r_id, route in enumerate(vrp.routes):
        fg = folium.FeatureGroup(name=f"Route #{r_id}")
        # vẽ từng edge trong route
        for a, b in zip(route[:-1], route[1:]):
            u, v = node_ids[a], node_ids[b]
            geom = path_geometry(G, u, v)
            folium.PolyLine(locations=[(lat, lon) for lat, lon in geom.coords], weight=5, opacity=0.7).add_to(fg)
        fg.add_to(m)

    # Step-by-step layers
    for s_id, s in enumerate(vrp.steps, start=1):
        fg = folium.FeatureGroup(name=f"Step {s_id}: v{ s['vehicle'] } {s['from']}→{s['to']}")
        u, v = node_ids[s["from"]], node_ids[s["to"]]
        geom = path_geometry(G, u, v)
        folium.PolyLine(locations=[(lat, lon) for lat, lon in geom.coords], weight=6, opacity=0.9).add_to(fg)
        # đánh dấu đầu/cuối
        folium.CircleMarker(points_latlon[s["from"]], radius=6, tooltip=f"from {s['from']}", color="red").add_to(fg)
        folium.CircleMarker(points_latlon[s["to"]], radius=6, tooltip=f"to {s['to']}", color="blue").add_to(fg)
        fg.add_to(m)

    folium.LayerControl().add_to(m)
    m.save(out_html)
    return out_html

# -----------------------------
# 4) VÍ DỤ SỬ DỤNG
# -----------------------------
if __name__ == "__main__":
    # Ví dụ: depot + vài điểm trong HCMC (lat, lon). Thay bằng dữ liệu thực tế của bạn.
    points = [
        (21.011257, 105.810770),  # Depot: Q1
        (20.99612710746094,105.80314544160171),  # Điểm 1
        (21.02311587396859,105.81378808465614),  # Điểm 2
        (21.020717444127552,105.80195581131119),  # Điểm 3
        (21.010249778864818,105.82659301435342),  # Điểm 4
        (21.014740792956715,105.80572059236329),  # Điểm 5
    ]

    # demands (nếu không dùng capacity có thể để None)
    demands = [0, 1, 2, 1, 1, 1]
    vehicle_capacity = 3.0
    max_stops_per_route = None   # hoặc đặt số max khách/xe
    num_vehicles = 2
    depot_idx = 0

    print("Downloading road network from OSM...")
    G = build_road_graph(points)
    node_ids = snap_points_to_graph(G, points)

    print("Building distance matrix (road distance, meters)...")
    D = build_distance_matrix(G, node_ids)
    print("Distance matrix (m):")
    np.set_printoptions(precision=1, suppress=True)
    print(D)

    print("Solving VRP with nearest-neighbor heuristic...")
    vrp = nearest_neighbor_vrp(
        D, demands=demands, vehicle_capacity=vehicle_capacity,
        max_stops_per_route=max_stops_per_route, num_vehicles=num_vehicles, depot_idx=depot_idx
    )

    for k, (route, dist_m) in enumerate(zip(vrp.routes, vrp.route_lengths)):
        print(f"Vehicle {k}: route {route}, length = {dist_m/1000:.2f} km")

    out = make_stepwise_map(G, points, node_ids, vrp, out_html="vrp_stepwise_map.html")
    print(f"Map saved to: {out}  (mở file HTML này để xem từng bước)")
