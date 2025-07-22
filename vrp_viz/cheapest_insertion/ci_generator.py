from ..utils import calculate_total_distance

def cheapest_insertion_generator(dist_matrix, demands, capacity):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    farthest_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
    routes = [[farthest_cust]]
    route_loads = [demands[farthest_cust]]
    unvisited.remove(farthest_cust)
    yield {
        "routes": routes,
        "message": f"Khởi tạo: Bắt đầu với khách hàng xa nhất {farthest_cust}.",
        "total_distance": calculate_total_distance(routes, dist_matrix),
    }
    while unvisited:
        best_insertion = {"cost": float("inf")}
        unselectable_nodes = set()
        for u in unvisited:
            can_be_inserted = any(
                route_loads[r_idx] + demands[u] <= capacity
                for r_idx in range(len(routes))
            )
            if not can_be_inserted:
                unselectable_nodes.add(u)
        special_colors = {node: "red" for node in unselectable_nodes}
        for u in unvisited:
            if u in unselectable_nodes:
                continue
            for r_idx, route in enumerate(routes):
                if route_loads[r_idx] + demands[u] > capacity:
                    continue
                for pos in range(len(route) + 1):
                    i = 0 if pos == 0 else route[pos - 1]
                    j = 0 if pos == len(route) else route[pos]
                    cost = dist_matrix[i][u] + dist_matrix[u][j] - dist_matrix[i][j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                            "edge": (i, j),
                        }
        if best_insertion["cost"] != float("inf"):
            u = best_insertion["customer"]
            edge = best_insertion["edge"]
            special_colors[u] = "green"
            message = f"Tìm thấy lựa chọn tốt nhất: Chèn khách hàng {u} vào giữa ({edge[0]}, {edge[1]})."
            yield {
                "routes": routes,
                "message": message,
                "total_distance": calculate_total_distance(routes, dist_matrix),
                "special_colors": special_colors,
                "highlighted_edges": [(edge[0], u), (u, edge[1])],
            }
            routes[best_insertion["route_idx"]].insert(best_insertion["pos"], u)
            route_loads[best_insertion["route_idx"]] += demands[u]
            unvisited.remove(u)
        else:
            if not unvisited:
                break
            next_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
            routes.append([next_cust])
            route_loads.append(demands[next_cust])
            unvisited.remove(next_cust)
            yield {
                "routes": routes,
                "message": f"Không thể chèn. Tạo tuyến mới với khách hàng {next_cust}.",
                "total_distance": calculate_total_distance(routes, dist_matrix),
            }
    yield {
        "routes": routes,
        "message": "Hoàn thành!",
        "total_distance": calculate_total_distance(routes, dist_matrix),
    }
