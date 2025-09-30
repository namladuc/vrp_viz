def nearest_neighbor(dist_matrix, demands, capacity):
    """Thuật toán Người láng giềng gần nhất."""
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    # B1: Khởi tạo tuyến đường ban đầu là rỗng
    all_routes = []
    # Thực hiện việc chèn chừng nào còn khách hàng chưa được phục vụ
    while unvisited:
        # B2: Gọi ra 1 một tuyến đường mới
        current_route = []
        current_load = 0
        current_location = 0
        # B3: Ta sẽ liên tục tìm khách hàng gần nhất cho đến khi không còn khách hàng nào có thể thêm vào tuyến đường
        while True:
            best_candidate = None
            min_dist = float("inf")
            for customer in unvisited:
                if current_load + demands[customer] <= capacity:
                    dist = dist_matrix[current_location][customer]
                    if dist < min_dist:
                        min_dist = dist
                        best_candidate = customer
            if best_candidate is not None:
                current_route.append(best_candidate)
                current_load += demands[best_candidate]
                current_location = best_candidate
                unvisited.remove(best_candidate)
            else:
                break
        # B4: Thêm tuyến đường vào danh sách tất cả các tuyến đường
        if current_route:
            all_routes.append(current_route)
    return all_routes


def nearest_neighbor_v2(dist_matrix, demands, capacity):
    """Thuật toán Người láng giềng gần nhất."""
    num_customers = len(demands) - 1
    unvisited = [True] * num_customers
    # B1: Khởi tạo tuyến đường ban đầu là rỗng
    all_routes = []
    no_visited = 0
    current_route = []
    current_load = 0
    current_location = 0
    # Thực hiện việc chèn chừng nào còn khách hàng chưa được phục vụ
    while no_visited < num_customers:
        best_candidate = None
        min_dist = float("inf")
        # Nếu tuyến đường rỗng thì tìm khách hàng gần nhất với kho
        if len(current_route) == 0:
            for customer in unvisited:
                if unvisited:
                    dist = dist_matrix[current_location][customer]
                    if dist < min_dist:
                        min_dist = dist
                        best_candidate = customer
            current_route.append(best_candidate)
            current_load += demands[best_candidate]
            current_location = best_candidate
            unvisited[best_candidate] = False

        # Nếu tuyến đường không rỗng thì tìm khách hàng gần nhất với khách hàng cuối cùng trong tuyến đường
        else:
            current_location = current_route[-1]
            min_dist = float("inf")
            best_candidate = None
            for customer in unvisited:
                if current_load + demands[customer] <= capacity:
                    dist = dist_matrix[current_location][customer]
                    if dist < min_dist:
                        min_dist = dist
                        best_candidate = customer
            if best_candidate is not None:
                current_route.append(best_candidate)
                current_load += demands[best_candidate]
                current_location = best_candidate
                unvisited[best_candidate] = False
            else:
                # B4: Thêm tuyến đường vào danh sách tất cả các tuyến đường
                all_routes.append(current_route)
                current_route = []

    if current_route:
        all_routes.append(current_route)
    return all_routes

