def cheapest_insertion(dist_matrix, demands, capacity):
    # Khởi tạo: Các tuyến đường ban đầu rỗng
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    routes = []
    route_loads = []

    # Chừng nào còn khách hàng chưa được phục vụ
    while unvisited:
        best_insertion = {"cost": float("inf")}
        # Tại đây, ta chọn "khách hàng" nào vào "vị trí" nào đem lại chi phí thấp nhất
        for u in unvisited:
            for r_idx, route in enumerate(routes):
                if route_loads[r_idx] + demands[u] > capacity:
                    continue
                # Chèn vào đầu hoặc cuối tuyến
                for pos in range(len(route) + 1):
                    if pos == 0:  # Chèn vào đầu
                        i, j = 0, route[0]
                    elif pos == len(route):  # Chèn vào cuối
                        i, j = route[-1], 0
                    else:  # Chèn vào giữa
                        i, j = route[pos - 1], route[pos]
                    # Đây là chi phí thay cạnh (i, j) = (i, u) + (u, j)
                    cost = dist_matrix[i][u] + dist_matrix[u][j] - dist_matrix[i][j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                        }
            # Ngoài ra cũng cân nhắc trường hợp lập thêm 1 tuyến đường mới
            cost_construct_route = dist_matrix[0][u] + dist_matrix[u][0]
            if cost_construct_route < best_insertion["cost"]:
                best_insertion = {
                    "cost": cost_construct_route,
                    "customer": u,
                    "route_idx": None,  # Đánh dấu là tạo tuyến mới
                    "pos": 0
                }

        if best_insertion["route_idx"] is None:
            routes.append([best_insertion["customer"]])
            route_loads.append(demands[best_insertion["customer"]])
            unvisited.remove(best_insertion["customer"])
        else:
            # Thực hiện chèn
            u = best_insertion["customer"]
            r_idx = best_insertion["route_idx"]
            pos = best_insertion["pos"]
            routes[r_idx].insert(pos, u)
            route_loads[r_idx] += demands[u]
            unvisited.remove(u)
    return routes
