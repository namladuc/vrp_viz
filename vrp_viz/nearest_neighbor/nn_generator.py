from ..utils import calculate_total_distance

def nearest_neighbor_generator(dist_matrix, demands, capacity):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    all_routes = []
    yield {"routes": [], "message": "Bắt đầu thuật toán.", "total_distance": 0}
    route_idx = 1
    while unvisited:
        current_route = []
        current_load = 0
        current_location = 0
        yield {
            "routes": all_routes,
            "message": f"Bắt đầu tuyến mới #{route_idx} từ kho.",
            "total_distance": calculate_total_distance(all_routes, dist_matrix),
        }
        while True:
            unselectable_nodes = {
                c for c in unvisited if current_load + demands[c] > capacity
            }
            special_colors = {node: "red" for node in unselectable_nodes}
            best_candidate = None
            min_dist = float("inf")
            for customer in unvisited:
                if customer not in unselectable_nodes:
                    dist = dist_matrix[current_location][customer]
                    if dist < min_dist:
                        min_dist = dist
                        best_candidate = customer
            if best_candidate:
                special_colors[best_candidate] = "green"
                message = f"Tuyến #{route_idx}: Từ {current_location}, chọn láng giềng gần nhất là {best_candidate}."
                yield {
                    "routes": all_routes + [current_route],
                    "message": message,
                    "total_distance": calculate_total_distance(
                        all_routes + [current_route], dist_matrix
                    ),
                    "special_colors": special_colors,
                    "highlighted_edges": [(current_location, best_candidate)],
                }
                current_route.append(best_candidate)
                current_load += demands[best_candidate]
                current_location = best_candidate
                unvisited.remove(best_candidate)
            else:
                message = f"Tuyến #{route_idx}: Không thể thêm khách hàng. Quay về kho."
                yield {
                    "routes": all_routes + [current_route],
                    "message": message,
                    "total_distance": calculate_total_distance(
                        all_routes + [current_route], dist_matrix
                    ),
                    "special_colors": special_colors,
                    "highlighted_edges": [(current_location, 0)],
                }
                break
        if current_route:
            all_routes.append(current_route)
        route_idx += 1
    yield {
        "routes": all_routes,
        "message": "Hoàn thành!",
        "total_distance": calculate_total_distance(all_routes, dist_matrix),
    }
