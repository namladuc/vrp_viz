import numpy as np
from typing import List, Optional
from ..map_viz.stepwise_map import VRPResult

def cheapest_insertion(
    D: np.ndarray,
    demands: Optional[List[float]] = None,
    vehicle_capacity: Optional[float] = None,
    max_stops_per_route: Optional[int] = None,  # giữ để đồng bộ signature
    num_vehicles: Optional[int] = None,         # giữ để đồng bộ signature
    depot_idx: int = 0,
) -> List[VRPResult]:
    """
    Cheapest Insertion heuristic for CVRP (stepwise).
    Trả về List[VRPResult]:
      - Step 0: rỗng (chưa có tuyến nào).
      - Sau đó, mỗi step ứng với việc chèn 1 khách hàng mới vào solution.
    """
    n = D.shape[0]
    if demands is None:
        demands = [0.0] * n

    unvisited = [i for i in range(n) if i != depot_idx]
    routes: List[List[int]] = []
    route_loads: List[float] = []
    steps: List[dict] = []
    snapshots: List[VRPResult] = []

    # ========== Helpers ==========
    def closed_route_and_len(path: List[int]):
        """Đóng tuyến với depot và tính độ dài."""
        if not path:
            return [depot_idx, depot_idx], 0.0
        length = float(D[depot_idx, path[0]])
        for u, v in zip(path[:-1], path[1:]):
            length += float(D[u, v])
        length += float(D[path[-1], depot_idx])
        return [depot_idx] + path + [depot_idx], length

    def snapshot_all_routes():
        rs, lens = [], []
        for p in routes:
            r, L = closed_route_and_len(p)
            rs.append(r)
            lens.append(L)
        snapshots.append(VRPResult(routes=rs, route_lengths=lens, steps=list(steps)))

    # Step 0: rỗng
    snapshots.append(VRPResult(routes=[], route_lengths=[], steps=list(steps)))

    # ========== Main Loop ==========
    while unvisited:
        best_insertion = {"cost": float("inf")}
        for u in unvisited:
            # thử chèn vào các tuyến hiện tại
            for r_idx, route in enumerate(routes):
                # kiểm tra capacity
                if vehicle_capacity is not None and route_loads[r_idx] + demands[u] > vehicle_capacity:
                    continue
                # kiểm tra max_stops
                if max_stops_per_route is not None and (len(route) + 1) > max_stops_per_route:
                    continue
                for pos in range(len(route) + 1):
                    if pos == 0:
                        i, j = depot_idx, route[0]
                    elif pos == len(route):
                        i, j = route[-1], depot_idx
                    else:
                        i, j = route[pos - 1], route[pos]
                    cost = D[i, u] + D[u, j] - D[i, j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                            "i": i,
                            "j": j
                        }
            # cân nhắc tạo tuyến mới
            cost_new = D[depot_idx, u] + D[u, depot_idx]
            if cost_new < best_insertion["cost"]:
                best_insertion = {
                    "cost": cost_new,
                    "customer": u,
                    "route_idx": None,
                    "pos": 0,
                    "i": depot_idx,
                    "j": depot_idx
                }

        # thực hiện chèn
        u = best_insertion["customer"]
        if best_insertion["route_idx"] is None:
            routes.append([u])
            route_loads.append(demands[u])
            steps.append({
                "vehicle": len(routes)-1,
                "from": depot_idx,
                "to": u,
                "detail": f"Start new route with {u}, cost={best_insertion['cost']:.3f}"
            })
        else:
            r_idx = best_insertion["route_idx"]
            pos = best_insertion["pos"]
            routes[r_idx].insert(pos, u)
            route_loads[r_idx] += demands[u]
            steps.append({
                "vehicle": r_idx,
                "from": best_insertion["i"],
                "to": u,
                "detail": f"Insert {u} into route {r_idx} at pos {pos}, cost={best_insertion['cost']:.3f}"
            })

        unvisited.remove(u)
        # snapshot sau mỗi chèn
        snapshot_all_routes()

    return snapshots
