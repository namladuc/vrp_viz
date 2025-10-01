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
) -> "VRPResult":
    """
    Clarke–Wright Savings (cơ bản).
    Trả về VRPResult với steps có 3 key chính: vehicle, from, to (giữ nguyên).
    Thêm 'detail' để giải thích (không thay đổi 3 key cốt lõi).
    """
    n = int(D.shape[0])
    assert D.shape[0] == D.shape[1], "D must be square"
    if demands is None:
        demands = [0.0] * n
    else:
        assert len(demands) == n, "demands length must match D"

    customers = [i for i in range(n) if i != depot_idx]

    routes_dict: Dict[int, Dict] = {}
    endpoint_owner: Dict[int, int] = {}
    next_route_id = 1

    steps: List[dict] = []

    # ===== Khởi tạo tuyến mở (singleton) =====
    for i in customers:
        rid = next_route_id
        next_route_id += 1
        routes_dict[rid] = {"path": [i], "demand": float(demands[i])}
        endpoint_owner[i] = rid

        # Ghi step “khởi tạo” (depot -> i) để người xem thấy nếu không merge thì sẽ là 2-chặng
        steps.append({
            "vehicle": rid - 1,      # tạm coi mỗi singleton là 1 xe trong giai đoạn init
            "from": depot_idx,
            "to": i,
            "detail": f"Init route #{rid}: start singleton at customer {i} (demand={demands[i]:.3f})"
        })

    # ===== Tính & sắp xếp Savings =====
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
                # Step giải thích “tính saving”
                steps.append({
                    "vehicle": -1,       # -1: bước tính toán/logic, không thuộc xe cụ thể
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

    def stops_ok_after_merge(path_a: List[int], path_b: List[int]) -> bool:
        if max_stops_per_route is None:
            return True
        return (len(path_a) + len(path_b)) <= max_stops_per_route

    # ===== Hợp nhất theo Savings =====
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
                "detail": f"Skip merge ({i},{j}) due to max_stops constraint: {len(path_i)}+{len(path_j)}>{max_stops_per_route}"
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

        if (num_vehicles is not None) and (len(routes_dict) <= num_vehicles):
            steps.append({
                "vehicle": -1, "from": depot_idx, "to": depot_idx,
                "detail": f"Stop merging early: current open routes={len(routes_dict)} <= num_vehicles={num_vehicles}"
            })
            break

    # ===== Đóng tuyến với depot, tính độ dài & steps “di chuyển” =====
    final_routes: List[List[int]] = []
    route_lengths: List[float] = []

    for k, (rid, r) in enumerate(routes_dict.items()):
        path = r["path"]
        if not path:
            continue

        # Kiểm tra tính hữu hạn của toàn bộ chặng (depot->head, giữa các khách, tail->depot)
        feasible = np.isfinite(D[depot_idx, path[0]]) and np.isfinite(D[path[-1], depot_idx])
        for u, v in zip(path[:-1], path[1:]):
            if not np.isfinite(D[u, v]):
                feasible = False
                break
        if not feasible:
            steps.append({
                "vehicle": k, "from": depot_idx, "to": depot_idx,
                "detail": f"Drop route #{rid} due to non-finite edge(s)"
            })
            continue

        full_route = [depot_idx] + path + [depot_idx]
        final_routes.append(full_route)

        # Ghi step “ràng buộc đóng tuyến”: depot -> head
        steps.append({
            "vehicle": k, "from": depot_idx, "to": path[0],
            "detail": f"Vehicle {k}: depart depot to {path[0]}"
        })

        length = 0.0
        cur = depot_idx
        # Di chuyển qua các khách
        for nxt in path:
            length += float(D[cur, nxt])
            steps.append({
                "vehicle": k, "from": cur, "to": nxt,
                "detail": f"Move {cur}->{nxt}, add {float(D[cur, nxt]):.3f}"
            })
            cur = nxt

        # Quay về depot
        length += float(D[cur, depot_idx])
        steps.append({
            "vehicle": k, "from": cur, "to": depot_idx,
            "detail": f"Return {cur}->{depot_idx}, add {float(D[cur, depot_idx]):.3f}"
        })

        route_lengths.append(length)

    return VRPResult(routes=final_routes, route_lengths=route_lengths, steps=steps)
