def clarke_wright_smallest_saving_first(dist_matrix, demands, capacity):
    """
    Biến thể của Clarke-Wright: ở mỗi bước, hợp nhất cặp có saving NHỎ NHẤT.
    """
    num_customers = len(demands) - 1
    depot = 0

    routes = {
        i: {"path": [i], "demand": demands[i]} for i in range(1, num_customers + 1)
    }

    while True:
        best_merge = {"saving": float("inf")}
        current_route_ids = list(routes.keys())

        # Bước 2a: Duyệt qua tất cả các cặp tuyến đường hiện có
        for i in range(len(current_route_ids)):
            for j in range(i + 1, len(current_route_ids)):
                route_id_1 = current_route_ids[i]
                route_id_2 = current_route_ids[j]

                route1 = routes[route_id_1]
                route2 = routes[route_id_2]

                # Kiểm tra điều kiện tải trọng trước tiên
                if route1["demand"] + route2["demand"] > capacity:
                    continue

                # Lấy ra các điểm cuối của 2 tuyến
                endpoints1 = (
                    [route1["path"][0], route1["path"][-1]]
                    if len(route1["path"]) > 1
                    else [route1["path"][0], route1["path"][0]]
                )
                endpoints2 = (
                    [route2["path"][0], route2["path"][-1]]
                    if len(route2["path"]) > 1
                    else [route2["path"][0], route2["path"][0]]
                )

                # Xem xét 4 khả năng nối
                for u in endpoints1:
                    for v in endpoints2:
                        saving = (
                            dist_matrix[depot][u]
                            + dist_matrix[depot][v]
                            - dist_matrix[u][v]
                        )

                        # Bước 2b: Nếu saving này nhỏ hơn saving nhỏ nhất đã tìm thấy
                        if saving < best_merge["saving"]:
                            best_merge = {
                                "saving": saving,
                                "route1_id": route_id_1,
                                "route2_id": route_id_2,
                                "endpoint1": u,
                                "endpoint2": v,
                            }

        # Bước 3: Nếu không tìm thấy cặp nào để hợp nhất trong vòng lặp, hãy dừng lại
        if best_merge["saving"] == float("inf"):
            break

        # Bước 2c: Thực hiện hợp nhất tốt nhất (tức là tệ nhất) đã tìm thấy
        r1_id = best_merge["route1_id"]
        r2_id = best_merge["route2_id"]
        u = best_merge["endpoint1"]
        v = best_merge["endpoint2"]

        path1 = routes[r1_id]["path"]
        path2 = routes[r2_id]["path"]

        # Logic hợp nhất
        if path1[-1] == u and path2[0] == v:
            path1.extend(path2)
        elif path1[0] == u and path2[-1] == v:
            path2.extend(path1)
            routes[r1_id]["path"] = path2  # Gán lại đường đi cho tuyến 1
        elif path1[-1] == u and path2[-1] == v:
            path2.reverse()
            path1.extend(path2)
        elif path1[0] == u and path2[0] == v:
            path1.reverse()
            path1.extend(path2)

        # Cập nhật demand và xóa tuyến đã được gộp
        routes[r1_id]["demand"] += routes[r2_id]["demand"]
        del routes[r2_id]

    return [r["path"] for r in routes.values()]


def clarke_wright_savings_nlog(dist_matrix, demands, capacity):
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

    for s in savings:
        i, j = s["i"], s["j"]
        route_id_i = endpoint_status[i]
        route_id_j = endpoint_status[j]

        if (
            route_id_i is not None
            and route_id_j is not None
            and route_id_i != route_id_j
        ):
            route_i = routes_dict[route_id_i]
            route_j = routes_dict[route_id_j]

            if route_i["demand"] + route_j["demand"] > capacity:
                continue

            path_i, path_j = route_i["path"], route_j["path"]
            absorbing_route_id = route_id_j

            # Case 1: ... -> i  +  j -> ...
            if path_i[-1] == i and path_j[0] == j:
                route_i["path"].extend(path_j)

            # Case 2: ... -> j  +  i -> ...
            elif path_j[-1] == j and path_i[0] == i:
                route_j["path"].extend(path_i)
                routes_dict[route_id_i] = routes_dict[route_id_j]
                absorbing_route_id = route_id_i

            # Case 3: ... -> i  +  ... -> j
            elif path_i[-1] == i and path_j[-1] == j:
                path_j.reverse()
                route_i["path"].extend(path_j)

            # Case 4: i -> ...  +  j -> ...
            elif path_i[0] == i and path_j[0] == j:
                path_i.reverse()
                route_i["path"].extend(path_j)
            else:
                continue

            # Cập nhật thông tin sau khi hợp nhất thành công
            merged_route_id = (
                route_id_i if absorbing_route_id == route_id_j else route_id_j
            )
            merged_route = routes_dict[merged_route_id]
            merged_route["demand"] += routes_dict[absorbing_route_id]["demand"]

            # cap nhat trang thai
            endpoint_status[i] = None
            endpoint_status[j] = None
            new_start, new_end = merged_route["path"][0], merged_route["path"][-1]
            endpoint_status[new_start] = merged_route_id
            endpoint_status[new_end] = merged_route_id
            del routes_dict[absorbing_route_id]
    return [r["path"] for r in routes_dict.values()]
