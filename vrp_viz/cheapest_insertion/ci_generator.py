from ..utils import calculate_total_distance

def cheapest_insertion_generator(dist_matrix, demands, capacity):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    routes = []
    route_loads = []

    while unvisited:
        best_insertion = {"cost": float("inf")}
        # Duyệt tất cả khách hàng chưa phục vụ
        for u in unvisited:
            for r_idx, route in enumerate(routes):
                if route_loads[r_idx] + demands[u] > capacity:
                    continue
                for pos in range(len(route) + 1):
                    if pos == 0:
                        i, j = 0, route[0]
                    elif pos == len(route):
                        i, j = route[-1], 0
                    else:
                        i, j = route[pos - 1], route[pos]
                    cost = dist_matrix[i][u] + dist_matrix[u][j] - dist_matrix[i][j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                            "edge": (i, j),
                        }

            # Kiểm tra nếu tạo tuyến mới là tốt nhất
            cost_new_route = dist_matrix[0][u] + dist_matrix[u][0]
            if cost_new_route < best_insertion["cost"]:
                best_insertion = {
                    "cost": cost_new_route,
                    "customer": u,
                    "route_idx": None,
                    "pos": 0,
                }

        u = best_insertion["customer"]
        special_colors = {u: "green"}

        if best_insertion["route_idx"] is None:
            # Tạo tuyến mới
            routes.append([u])
            route_loads.append(demands[u])
            message = f"Tạo tuyến mới với khách hàng {u} (chi phí {best_insertion['cost']:.2f})."
            highlighted_edges = [(0, u), (u, 0)]
        else:
            # Chèn vào tuyến hiện có
            r_idx = best_insertion["route_idx"]
            pos = best_insertion["pos"]
            routes[r_idx].insert(pos, u)
            route_loads[r_idx] += demands[u]
            i, j = best_insertion["edge"]
            message = f"Chèn khách hàng {u} vào giữa ({i}, {j}) (chi phí {best_insertion['cost']:.2f})."
            highlighted_edges = [(i, u), (u, j)]

        unvisited.remove(u)

        yield {
            "routes": routes,
            "message": message,
            "total_distance": calculate_total_distance(routes, dist_matrix),
            "special_colors": special_colors,
            "highlighted_edges": highlighted_edges,
        }

    yield {
        "routes": routes,
        "message": "Hoàn thành tất cả khách hàng!",
        "total_distance": calculate_total_distance(routes, dist_matrix),
    }
