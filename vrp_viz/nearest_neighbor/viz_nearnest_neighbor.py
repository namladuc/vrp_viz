from ..map_viz.stepwise_map import VRPResult

import copy
import numpy as np
from typing import List, Optional


def nearest_neighbor_v2(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,
    num_vehicles: int = 1,
    depot_idx: int = 0,
) -> List[VRPResult]:
    """
    Trả về: List[VRPResult], mỗi VRPResult ứng với 1 step (một cung 'from' -> 'to' được thêm).
    Tại mỗi step, routes trong snapshot gồm:
      - Tất cả các tuyến đã chốt (đã kết thúc ở depot)
      - Cộng thêm tuyến hiện tại đang đi dở (nếu có), để bạn vẽ được trạng thái tức thời.
    """

    n = int(D.shape[0])
    assert D.shape[0] == D.shape[1], "D must be square"
    if demands is None:
        demands = [0.0] * n
    else:
        assert len(demands) == n, "demands length must match D"

    # Các node chưa phục vụ (bỏ depot)
    unserved = set(range(n))
    unserved.discard(depot_idx)

    # Tuyến đã chốt
    routes: List[List[int]] = []
    lengths: List[float] = []
    # Toàn bộ steps đã diễn ra (cộng dồn)
    steps: List[dict] = []

    # Danh sách kết quả stepwise
    results: List[VRPResult] = []

    def snapshot(partial_route: Optional[List[int]], partial_len: float, vehicle_idx_for_partial: Optional[int]):
        """
        Lấy ảnh chụp trạng thái hiện tại:
          - routes_chot: bản sao các tuyến đã chốt
          - nếu đang có tuyến dở (partial_route != None), thêm vào cuối danh sách như một tuyến tạm
        """
        routes_chot = copy.deepcopy(routes)
        lengths_chot = copy.deepcopy(lengths)

        if partial_route is not None and len(partial_route) >= 1:
            routes_chot.append(copy.deepcopy(partial_route))
            lengths_chot.append(float(partial_len))

        results.append(
            VRPResult(
                routes=routes_chot,
                route_lengths=lengths_chot,
                steps=copy.deepcopy(steps),
            )
        )

    for k in range(num_vehicles):
        if not unserved:
            break

        # Khởi tạo tuyến mới cho xe k (chưa chốt vào routes cho tới khi kết thúc)
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
                    cap_ok = (load + float(demands[j])) <= vehicle_capacity
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
                    # Snapshot sau khi thêm cạnh quay về depot
                    snapshot(partial_route=route, partial_len=route_len, vehicle_idx_for_partial=k)
                # Kết thúc tuyến này -> chốt vào routes
                if len(route) > 1:
                    routes.append(copy.deepcopy(route))
                    lengths.append(float(route_len))
                break

            # Chọn khách gần nhất
            j_star = min(candidates, key=lambda j: D[current, j])
            route.append(j_star)
            route_len += float(D[current, j_star])
            steps.append({"vehicle": k, "from": current, "to": j_star})
            # Snapshot ngay sau khi đi tới j_star
            snapshot(partial_route=route, partial_len=route_len, vehicle_idx_for_partial=k)

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
                    # Snapshot sau khi quay về depot để hoàn tất
                    snapshot(partial_route=route, partial_len=route_len, vehicle_idx_for_partial=k)
                # Chốt tuyến
                if len(route) > 1:
                    routes.append(copy.deepcopy(route))
                    lengths.append(float(route_len))
                break

        # (Không snapshot thêm ở đây, vì đã snapshot trong vòng while tại những điểm có cạnh mới.)

    # Nếu vẫn còn khách và đã hết xe → nhét vào tuyến cuối (bỏ qua capacity/max_stops)
    if unserved and routes:
        last_idx = len(routes) - 1
        last = routes[last_idx]
        last_len = lengths[last_idx]

        # current node là node trước depot cuối của tuyến
        if last[-1] == depot_idx and len(last) >= 2:
            current = last[-2]
        else:
            current = last[-1]

        # Nếu tuyến cuối chưa kết thúc ở depot, đảm bảo có depot cuối
        if last[-1] != depot_idx and np.isfinite(D[current, depot_idx]):
            last.append(depot_idx)
            last_len += float(D[current, depot_idx])
            steps.append({"vehicle": last_idx, "from": current, "to": depot_idx})
            # Snapshot sau khi ép quay về depot để dễ chèn khách vào trước depot
            snapshot(partial_route=None, partial_len=0.0, vehicle_idx_for_partial=None)
            current = depot_idx  # điểm tham chiếu sẽ cập nhật lại ngay sau đây

        # Chèn từng khách còn lại trước vị trí depot cuối
        # current ở đây sẽ là node cuối trước depot trong quá trình chèn dần
        current = last[-2] if len(last) >= 2 else depot_idx

        for j in list(unserved):
            if np.isfinite(D[current, j]) and np.isfinite(D[j, depot_idx]):
                # vị trí chèn trước depot
                insert_pos = len(last) - 1  # trước phần tử depot cuối
                # cập nhật độ dài: bỏ đoạn current->depot, thêm current->j + j->depot
                delta = float(D[current, j] + D[j, depot_idx] - D[current, depot_idx])
                last_len += delta
                # steps: current -> j
                steps.append({"vehicle": last_idx, "from": current, "to": j})
                last.insert(insert_pos, j)
                current = j
                unserved.remove(j)
                # Cập nhật chiều dài tuyến trong mảng lengths
                lengths[last_idx] = last_len
                # Snapshot sau mỗi lần chèn 1 khách (coi là một step di chuyển current->j)
                snapshot(partial_route=None, partial_len=0.0, vehicle_idx_for_partial=None)

        # Bảo đảm kết thúc ở depot (trường hợp chưa có)
        if last[-1] != depot_idx and np.isfinite(D[last[-1], depot_idx]):
            steps.append({"vehicle": last_idx, "from": last[-1], "to": depot_idx})
            last_len += float(D[last[-1], depot_idx])
            last.append(depot_idx)
            lengths[last_idx] = last_len
            # Snapshot kết thúc tuyến
            snapshot(partial_route=None, partial_len=0.0, vehicle_idx_for_partial=None)

    # Nếu không có step nào (ví dụ không có cạnh hợp lệ), vẫn trả về rỗng
    return results
