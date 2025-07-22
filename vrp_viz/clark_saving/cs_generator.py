from ..utils import calculate_total_distance


def clarke_wright_refined_generator(dist_matrix, demands, capacity):
    num_customers = len(demands) - 1
    depot = 0
    savings = []
    for i in range(1, num_customers + 1):
        for j in range(i + 1, num_customers + 1):
            s_ij = dist_matrix[depot][i] + dist_matrix[depot][j] - dist_matrix[i][j]
            savings.append({"i": i, "j": j, "saving": s_ij})
    savings.sort(key=lambda x: x["saving"], reverse=True)
    routes_dict = {
        i: {"path": [i], "demand": demands[i]} for i in range(1, num_customers + 1)
    }
    endpoint_status = [None] * (num_customers + 1)
    for i in range(1, num_customers + 1):
        endpoint_status[i] = i
    initial_routes = [r["path"] for r in routes_dict.values()]
    yield {
        "routes": initial_routes,
        "message": f"Khởi tạo: {num_customers} tuyến. Bắt đầu xem xét {len(savings)} cặp tiết kiệm.",
        "total_distance": calculate_total_distance(initial_routes, dist_matrix),
    }

    for s in savings:
        i, j = s["i"], s["j"]
        route_id_i = endpoint_status[i]
        route_id_j = endpoint_status[j]

        can_merge = False
        if (
            route_id_i is not None
            and route_id_j is not None
            and route_id_i != route_id_j
        ):
            route_i = routes_dict[route_id_i]
            route_j = routes_dict[route_id_j]
            if route_i["demand"] + route_j["demand"] <= capacity:
                can_merge = True

        if can_merge:
            message = f"Đang xét cặp ({i}, {j}) với saving = {s['saving']:.2f}. "
            message += f"Thành công! Hợp nhất tuyến của {i} và {j}."
            special_colors = {i: "green", j: "green"}

            yield {
                "routes": [r["path"] for r in routes_dict.values()],
                "message": message,
                "total_distance": calculate_total_distance(
                    [r["path"] for r in routes_dict.values()], dist_matrix
                ),
                "special_colors": special_colors,
            }

            path_i, path_j = route_i["path"], route_j["path"]
            absorbing_route_id = route_id_j

            if path_i[-1] == i and path_j[0] == j:
                path_i.extend(path_j)
            elif path_j[-1] == j and path_i[0] == i:
                path_j.extend(path_i)
                routes_dict[route_id_i] = routes_dict[route_id_j]
                absorbing_route_id = route_id_i
            elif path_i[-1] == i and path_j[-1] == j:
                path_j.reverse()
                path_i.extend(path_j)
            elif path_i[0] == i and path_j[0] == j:
                path_i.reverse()
                path_i.extend(path_j)

            merged_route_id = (
                route_id_i if absorbing_route_id == route_id_j else route_id_j
            )
            merged_route = routes_dict[merged_route_id]
            merged_route["demand"] += routes_dict[absorbing_route_id]["demand"]

            endpoint_status[i], endpoint_status[j] = None, None
            new_start, new_end = merged_route["path"][0], merged_route["path"][-1]
            endpoint_status[new_start] = merged_route_id
            endpoint_status[new_end] = merged_route_id

            del routes_dict[absorbing_route_id]

    final_routes = [r["path"] for r in routes_dict.values()]
    yield {
        "routes": final_routes,
        "message": "Hoàn thành!",
        "total_distance": calculate_total_distance(final_routes, dist_matrix),
    }
