from ..map_viz.stepwise_map import VRPResult

import numpy as np
from typing import List, Optional

# Giả sử bạn đã có dataclass này:
# from .stepwise_map import VRPResult
# from dataclasses import dataclass
# @dataclass
# class VRPResult:
#     routes: List[List[int]]
#     route_lengths: List[float]
#     steps: List[dict]

def nearest_neighbor_v2(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,
    num_vehicles: int = 1,
    depot_idx: int = 0,
) -> VRPResult:
    """
    Nearest Neighbor VRP với ràng buộc capacity / max stops, nhiều xe.
    - D: ma trận khoảng cách (m), D[i,j] >= 0; D[i,i]=0
    - demands: list demand cho từng node (cùng kích thước với D). depot demand = 0.
    - vehicle_capacity: tổng demand tối đa/xe (nếu None -> bỏ qua)
    - max_stops_per_route: tối đa số khách/xe (không tính depot). None -> bỏ qua
    - num_vehicles: số xe
    - depot_idx: chỉ số depot trong D
    """
    n = int(D.shape[0])
    assert D.shape[0] == D.shape[1], "D must be square"
    if demands is None:
        demands = [0.0] * n
    else:
        assert len(demands) == n, "demands length must match D"

    # Tập các node chưa phục vụ (bỏ depot)
    unserved = set(range(n))
    unserved.discard(depot_idx)

    routes: List[List[int]] = []
    lengths: List[float] = []
    steps: List[dict] = []

    for k in range(num_vehicles):
        if not unserved:
            break

        route = [depot_idx]
        load = 0.0
        used_stops = 0
        current = depot_idx
        route_len = 0.0

        while True:
            # Ứng viên hợp lệ theo capacity/max_stops + cạnh hữu hạn
            candidates = []
            for j in unserved:
                cap_ok = True
                if vehicle_capacity is not None:
                    cap_ok = (load + demands[j]) <= vehicle_capacity
                stops_ok = True
                if max_stops_per_route is not None:
                    stops_ok = (used_stops + 1) <= max_stops_per_route
                if cap_ok and stops_ok and np.isfinite(D[current, j]):
                    candidates.append(j)

            if not candidates:
                # Không còn điểm hợp lệ: nếu đang ở khách thì quay về depot
                if route[-1] != depot_idx and np.isfinite(D[current, depot_idx]):
                    route.append(depot_idx)
                    route_len += float(D[current, depot_idx])
                    steps.append({"vehicle": k, "from": current, "to": depot_idx})
                break

            # Chọn khách gần nhất
            j_star = min(candidates, key=lambda j: D[current, j])
            route.append(j_star)
            route_len += float(D[current, j_star])
            steps.append({"vehicle": k, "from": current, "to": j_star})

            # Cập nhật
            load += float(demands[j_star])
            used_stops += 1
            current = j_star
            unserved.remove(j_star)

            # Nếu đã phục vụ hết thì đóng tuyến về depot
            if not unserved:
                if route[-1] != depot_idx and np.isfinite(D[current, depot_idx]):
                    route.append(depot_idx)
                    route_len += float(D[current, depot_idx])
                    steps.append({"vehicle": k, "from": current, "to": depot_idx})
                break

        # Lưu tuyến (bỏ tuyến rỗng chỉ có depot)
        if len(route) > 1:
            routes.append(route)
            lengths.append(route_len)

    # Nếu vẫn còn khách và đã hết xe → nhét vào tuyến cuối (bỏ qua capacity/max_stops)
    if unserved and routes:
        last_idx = len(routes) - 1
        last = routes[last_idx]
        # current node là node trước depot cuối của tuyến
        if last[-1] == depot_idx and len(last) >= 2:
            current = last[-2]
        else:
            current = last[-1]

        for j in list(unserved):
            if np.isfinite(D[current, j]) and np.isfinite(D[j, depot_idx]):
                # chèn trước depot
                if last[-1] == depot_idx:
                    insert_pos = len(last) - 1
                else:
                    # đảm bảo cuối cùng có depot
                    last.append(depot_idx)
                    lengths[last_idx] += float(D[current, depot_idx])
                    steps.append({"vehicle": last_idx, "from": current, "to": depot_idx})
                    insert_pos = len(last) - 1

                # cập nhật độ dài: bỏ đoạn current->depot, thêm current->j + j->depot
                lengths[last_idx] += float(D[current, j] + D[j, depot_idx] - D[current, depot_idx])
                # steps: current -> j
                steps.append({"vehicle": last_idx, "from": current, "to": j})
                last.insert(insert_pos, j)
                current = j
                unserved.remove(j)

        # bảo đảm kết thúc ở depot
        if last[-1] != depot_idx and np.isfinite(D[last[-1], depot_idx]):
            steps.append({"vehicle": last_idx, "from": last[-1], "to": depot_idx})
            lengths[last_idx] += float(D[last[-1], depot_idx])
            last.append(depot_idx)

    return VRPResult(routes=routes, route_lengths=lengths, steps=steps)
