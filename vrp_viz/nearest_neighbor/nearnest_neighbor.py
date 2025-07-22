def nearest_neighbor(dist_matrix, demands, capacity):
    """Thuật toán Người láng giềng gần nhất."""
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    all_routes = []
    while unvisited:
        current_route = []
        current_load = 0
        current_location = 0
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
        if current_route:
            all_routes.append(current_route)
    return all_routes
