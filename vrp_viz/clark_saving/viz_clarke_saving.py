import numpy as np
from typing import List, Optional, Dict, Tuple

from ..map_viz.stepwise_map import VRPResult
# Giả sử bạn đã có dataclass VRPResult
# from dataclasses import dataclass
# @dataclass
# class VRPResult:
#     routes: List[List[int]]
#     route_lengths: List[float]
#     steps: List[dict]

def clarke_wright_savings_vrp(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,  # tuỳ chọn
    num_vehicles: Optional[int] = None,         # nếu None: không ép số xe
    depot_idx: int = 0,
) -> List[VRPResult]:
    """
    Clarke–Wright Savings (cơ bản) — trả về danh sách VRPResult dạng stepwise.
    - Snapshot #0: mỗi tuyến tương ứng 1 customer (đều đóng depot).
    - Mỗi lần merge:
        * Snapshot A (pre-merge): chỉ 2 tuyến sẽ gộp (đều đóng depot).
        * Snapshot B (post-merge): chỉ tuyến mới sau khi gộp (đã đóng depot).
    steps[] vẫn giữ 3 key: vehicle/from/to + 'detail' mô tả.
    """
    n = int(D.shape[0])
    assert D.shape[0] == D.shape[1], "D must be square"
    if demands is None:
        demands = [0.0] * n
    else:
        assert len(demands) == n, "demands length must match D"

    customers = [i for i in range(n) if i != depot_idx]

    # routes_dict: rid -> {"path": [customers...], "demand": float}
    routes_dict: Dict[int, Dict] = {}
    endpoint_owner: Dict[int, int] = {}
    next_route_id = 1

    # Các bước diễn giải (cộng dồn)
    steps: List[dict] = []

    # ========== Helpers ==========
    def closed_route_and_len(path: List[int]) -> Tuple[List[int], float]:
        """Trả về route đóng depot [depot, ...path..., depot] và tổng độ dài."""
        if not path:
            return [depot_idx, depot_idx], 0.0
        # kiểm tra hữu hạn
        if not (np.isfinite(D[depot_idx, path[0]]) and np.isfinite(D[path[-1], depot_idx])):
            return None, np.inf  # báo không khả thi
        length = float(D[depot_idx, path[0]])
        for u, v in zip(path[:-1], path[1:]):
            if not np.isfinite(D[u, v]):
                return None, np.inf
            length += float(D[u, v])
        length += float(D[path[-1], depot_idx])
        return [depot_idx] + path + [depot_idx], length

    def snapshot_from_paths(paths: List[List[int]]) -> VRPResult:
        """Tạo VRPResult từ danh sách path (chưa đóng). Route sẽ đóng depot và tính length."""
        routes: List[List[int]] = []
        lens: List[float] = []
        for p in paths:
            r, L = closed_route_and_len(p)
            if r is None:  # nếu có cạnh vô hạn -> bỏ qua snapshot cho tuyến đó
                continue
            routes.append(r)
            lens.append(L)
        return VRPResult(routes=routes, route_lengths=lens, steps=list(steps))

    def stops_ok_after_merge(path_a: List[int], path_b: List[int]) -> bool:
        if max_stops_per_route is None:
            return True
        return (len(path_a) + len(path_b)) <= max_stops_per_route

    # ========== Khởi tạo singleton ==========
    for i in customers:
        rid = next_route_id
        next_route_id += 1
        routes_dict[rid] = {"path": [i], "demand": float(demands[i])}
        endpoint_owner[i] = rid

        # Ghi step init
        steps.append({
            "vehicle": rid - 1,
            "from": depot_idx,
            "to": i,
            "detail": f"Init route #{rid}: singleton at customer {i} (demand={demands[i]:.3f})"
        })

    # Snapshot #0: mỗi tuyến là một customer (đều đóng depot)
    snapshots: List[VRPResult] = []
    snapshots.append(snapshot_from_paths([r["path"] for r in routes_dict.values()]))

    # ========== Tính & sắp xếp Savings ==========
    savings: List[Tuple[float, int, int]] = []
    for idx_i, i in enumerate(customers):
        di = D[depot_idx, i]
        if not np.isfinite(di):
            continue
        for j in customers[idx_i + 1:]:
            dj = D[depot_idx, j]
            dij = D[i, j]
            if np.isfinite(dj) and np.isfinite(dij):
                s_ij = float(di + dj - dij)
                savings.append((s_ij, i, j))
                steps.append({
                    "vehicle": -1,
                    "from": i,
                    "to": j,
                    "detail": f"Compute saving S({i},{j}) = D({depot_idx},{i}) + D({depot_idx},{j}) - D({i},{j}) = {s_ij:.3f}"
                })

    savings.sort(key=lambda t: t[0], reverse=True)
    steps.append({
        "vehicle": -1,
        "from": depot_idx,
        "to": depot_idx,
        "detail": f"Sort savings descending; total pairs={len(savings)}"
    })

    # ========== Hợp nhất theo Savings ==========
    for s, i, j in savings:
        rid_i = endpoint_owner.get(i)
        rid_j = endpoint_owner.get(j)
        if rid_i is None or rid_j is None or rid_i == rid_j:
            continue

        r_i = routes_dict[rid_i]
        r_j = routes_dict[rid_j]
        path_i = r_i["path"]
        path_j = r_j["path"]

        new_demand = r_i["demand"] + r_j["demand"]
        if (vehicle_capacity is not None) and (new_demand > vehicle_capacity):
            steps.append({
                "vehicle": -1, "from": i, "to": j,
                "detail": f"Skip merge ({i},{j}) due to capacity: {new_demand:.3f} > {vehicle_capacity:.3f}"
            })
            continue

        if not stops_ok_after_merge(path_i, path_j):
            steps.append({
                "vehicle": -1, "from": i, "to": j,
                "detail": f"Skip merge ({i},{j}) due to max_stops: {len(path_i)}+{len(path_j)}>{max_stops_per_route}"
            })
            continue

        merged_path = None
        case = None

        if (path_i and path_j) and (path_i[-1] == i and path_j[0] == j):
            merged_path, case = (path_i + path_j), "case1_tail(i)+head(j)"
        elif (path_i and path_j) and (path_j[-1] == j and path_i[0] == i):
            merged_path, case = (path_j + path_i), "case2_tail(j)+head(i)"
        elif (path_i and path_j) and (path_i[-1] == i and path_j[-1] == j):
            merged_path, case = (path_i + list(reversed(path_j))), "case3_tail(i)+tail(j)_rev(j)"
        elif (path_i and path_j) and (path_i[0] == i and path_j[0] == j):
            merged_path, case = (list(reversed(path_i)) + path_j), "case4_head(i)_rev(i)+head(j)"
        else:
            steps.append({
                "vehicle": -1, "from": i, "to": j,
                "detail": f"Skip merge ({i},{j}) because they are not at endpoints"
            })
            continue

        # --- Snapshot A: chỉ 2 tuyến sẽ gộp (đều đóng depot) ---
        steps.append({
            "vehicle": -1, "from": i, "to": j,
            "detail": f"Preview merge ({i},{j}) via {case}: show 2 routes before merge"
        })
        snapshots.append(snapshot_from_paths([path_i, path_j]))

        # Ghi step “thử merge”
        steps.append({
            "vehicle": -1, "from": i, "to": j,
            "detail": f"Merge ({i},{j}) via {case} | routes #{rid_i} + #{rid_j} -> demand={new_demand:.3f}"
        })

        # Cập nhật endpoint_owner: gỡ endpoints cũ
        for end_node in (path_i[0], path_i[-1], path_j[0], path_j[-1]):
            if endpoint_owner.get(end_node) in (rid_i, rid_j):
                endpoint_owner.pop(end_node, None)

        # Giữ rid_i làm id sau merge
        r_i["path"] = merged_path
        r_i["demand"] = new_demand
        new_head, new_tail = merged_path[0], merged_path[-1]
        endpoint_owner[new_head] = rid_i
        endpoint_owner[new_tail] = rid_i

        routes_dict.pop(rid_j, None)

        # --- Snapshot B: chỉ tuyến mới sau khi gộp (đã đóng depot) ---
        steps.append({
            "vehicle": -1, "from": new_head, "to": new_tail,
            "detail": f"Show merged route (rid={rid_i}) after merge"
        })
        snapshots.append(snapshot_from_paths([merged_path]))

        if (num_vehicles is not None) and (len(routes_dict) <= num_vehicles):
            steps.append({
                "vehicle": -1, "from": depot_idx, "to": depot_idx,
                "detail": f"Stop merging early: open routes={len(routes_dict)} <= num_vehicles={num_vehicles}"
            })
            break

    # ========== (Tuỳ chọn) Đóng tuyến thật sự & bước di chuyển ==========
    # Nếu bạn muốn thêm một snapshot cuối hiển thị toàn bộ tuyến sau khi dừng merge:
    snapshots.append(snapshot_from_paths([r["path"] for r in routes_dict.values()]))

    # (Giữ nguyên phần "đi tuyến" nếu bạn cần steps di chuyển chi tiết, có thể bật sau.)
    final_routes: List[List[int]] = []
    route_lengths: List[float] = []
    for k, (rid, r) in enumerate(routes_dict.items()):
        path = r["path"]
        full, L = closed_route_and_len(path)
        if full is None or not np.isfinite(L):
            steps.append({"vehicle": k, "from": depot_idx, "to": depot_idx,
                          "detail": f"Drop route #{rid} due to non-finite edge(s)"})
            continue
        final_routes.append(full)
        route_lengths.append(L)
    # # Có thể thêm 1 snapshot tổng kết cuối:
    snapshots.append(VRPResult(routes=final_routes, route_lengths=route_lengths, steps=list(steps)))

    return snapshots

def clarke_wright_smallest_saving_first(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,  # để tương thích với signature
    num_vehicles: Optional[int] = None,         # để tương thích với signature
    depot_idx: int = 0,
) -> List[VRPResult]:
    """
    Clarke–Wright Savings (smallest saving first).
    Trả về danh sách VRPResult stepwise:
      - Bước 0: mỗi customer là một tuyến riêng [depot, i, depot].
      - Mỗi merge:
          * Snapshot A: chỉ 2 tuyến chuẩn bị gộp
          * Snapshot B: tuyến mới sau gộp
    """

    n = D.shape[0]
    if demands is None:
        demands = [0.0] * n

    # ========== Helpers ==========
    def closed_route_and_len(path: List[int]) -> Tuple[List[int], float]:
        """Trả về route đóng depot và độ dài"""
        if not path:
            return [depot_idx, depot_idx], 0.0
        length = float(D[depot_idx, path[0]])
        for u, v in zip(path[:-1], path[1:]):
            length += float(D[u, v])
        length += float(D[path[-1], depot_idx])
        return [depot_idx] + path + [depot_idx], length

    def snapshot_from_paths(paths: List[List[int]], steps: List[dict]) -> VRPResult:
        routes, lens = [], []
        for p in paths:
            r, L = closed_route_and_len(p)
            routes.append(r)
            lens.append(L)
        return VRPResult(routes=routes, route_lengths=lens, steps=list(steps))

    # ========== Init singletons ==========
    routes: Dict[int, Dict] = {
        i: {"path": [i], "demand": float(demands[i])} for i in range(n) if i != depot_idx
    }
    steps: List[dict] = []

    # Snapshot #0: mỗi khách là một tuyến riêng
    snapshots: List[VRPResult] = []
    steps.append({"vehicle": -1, "from": depot_idx, "to": depot_idx,
                  "detail": f"Init {len(routes)} singleton routes"})
    snapshots.append(snapshot_from_paths([r["path"] for r in routes.values()], steps))

    # ========== Merge loop ==========
    while True:
        best_merge = {"saving": float("inf")}
        current_route_ids = list(routes.keys())

        # tìm cặp có saving nhỏ nhất
        for i in range(len(current_route_ids)):
            for j in range(i + 1, len(current_route_ids)):
                r1_id = current_route_ids[i]
                r2_id = current_route_ids[j]
                r1 = routes[r1_id]
                r2 = routes[r2_id]

                if vehicle_capacity is not None and (r1["demand"] + r2["demand"] > vehicle_capacity):
                    continue

                endpoints1 = [r1["path"][0], r1["path"][-1]]
                endpoints2 = [r2["path"][0], r2["path"][-1]]

                for u in endpoints1:
                    for v in endpoints2:
                        saving = D[depot_idx, u] + D[depot_idx, v] - D[u, v]
                        if saving < best_merge["saving"]:
                            best_merge = {
                                "saving": saving,
                                "route1_id": r1_id,
                                "route2_id": r2_id,
                                "endpoint1": u,
                                "endpoint2": v,
                            }

        if best_merge["saving"] == float("inf"):
            break

        r1_id, r2_id = best_merge["route1_id"], best_merge["route2_id"]
        u, v = best_merge["endpoint1"], best_merge["endpoint2"]
        path1, path2 = routes[r1_id]["path"], routes[r2_id]["path"]

        # --- Merge logic ---
        if path1[-1] == u and path2[0] == v:
            merged_path = path1 + path2
        elif path1[0] == u and path2[-1] == v:
            merged_path = path2 + path1
        elif path1[-1] == u and path2[-1] == v:
            merged_path = path1 + list(reversed(path2))
        elif path1[0] == u and path2[0] == v:
            merged_path = list(reversed(path1)) + path2
        else:
            # không merge được -> bỏ
            continue
        
        # --- Snapshot A: hai tuyến chuẩn bị gộp ---
        steps.append({
            "vehicle": -1, "from": u, "to": v,
            "detail": f"Prepare merge: route {r1_id} and {r2_id}, saving={best_merge['saving']:.3f}"
        })
        snapshots.append(snapshot_from_paths([path1, path2], steps))

        routes[r1_id]["path"] = merged_path
        routes[r1_id]["demand"] += routes[r2_id]["demand"]
        del routes[r2_id]

        steps.append({
            "vehicle": -1, "from": u, "to": v,
            "detail": f"Merged route {r1_id}+{r2_id} -> new demand={routes[r1_id]['demand']:.3f}"
        })

        # --- Snapshot B: tuyến mới sau khi gộp ---
        snapshots.append(snapshot_from_paths([merged_path], steps))
        
        snapshots.append(snapshot_from_paths([r["path"] for r in routes.values()], steps))

    return snapshots
