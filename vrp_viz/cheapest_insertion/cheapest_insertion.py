def cheapest_insertion(dist_matrix, demands, capacity):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))

    farthest_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
    routes = [[farthest_cust]]
    route_loads = [demands[farthest_cust]]
    unvisited.remove(farthest_cust)

    while unvisited:
        best_insertion = {"cost": float("inf")}

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
                    cost = dist_matrix[i][u] + dist_matrix[u][j] - dist_matrix[i][j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                        }
        if best_insertion["cost"] != float("inf"):
            # Thực hiện chèn
            u = best_insertion["customer"]
            r_idx = best_insertion["route_idx"]
            pos = best_insertion["pos"]
            routes[r_idx].insert(pos, u)
            route_loads[r_idx] += demands[u]
            unvisited.remove(u)
        else:
            # Nếu không chèn được vào đâu (do quá tải), tạo tuyến mới
            if not unvisited:
                break
            next_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
            routes.append([next_cust])
            route_loads.append(demands[next_cust])
            unvisited.remove(next_cust)
    return routes
