import copy
from vrp_viz.local_search.util import *
from vrp_viz.map_viz.stepwise_map import VRPResult

def two_opt_star_local_search(
        D: np.ndarray,
        demands: List[float],
        vehicle_capacity: float,
        max_stops_per_route,  # Ignored
        num_vehicles,  # Ignored
        depot_idx,  # Ignored
        current_solution: VRPResult
) -> List[VRPResult]:
    """
    2-opt* move: Inter-route move that exchanges tails of two routes
    """
    solutions = [current_solution]
    current = copy.deepcopy(current_solution)

    while True:
        best_delta = float('inf')
        best_move = None

        # Try all possible 2-opt* moves between different routes
        for route_i in range(len(current.routes)):
            route1 = current.routes[route_i]
            for route_j in range(route_i + 1, len(current.routes)):
                route2 = current.routes[route_j]

                # Try all cut points
                for cut_i in range(1, len(route1) - 1):
                    for cut_j in range(1, len(route2) - 1):

                        # Check capacity constraints
                        # New route1: route1[:cut_i+1] + route2[cut_j+1:-1] + [0]
                        # New route2: route2[:cut_j+1] + route1[cut_i+1:-1] + [0]

                        new_demand1 = sum(demands[c] for c in route1[1:cut_i + 1]) + \
                                      sum(demands[c] for c in route2[cut_j + 1:-1])
                        new_demand2 = sum(demands[c] for c in route2[1:cut_j + 1]) + \
                                      sum(demands[c] for c in route1[cut_i + 1:-1])

                        if new_demand1 > vehicle_capacity or new_demand2 > vehicle_capacity:
                            continue

                        # Calculate delta
                        delta = calculate_two_opt_star_delta(D, current.routes, route_i, cut_i, route_j, cut_j)

                        # Verify correctness. Comment this out when done testing for a BOOM speed up.
                        if not check_two_opt_star_delta_correctness(D, current, route_i, cut_i, route_j, cut_j, delta):
                            raise ValueError("2-opt* delta calculation error")

                        if delta < best_delta:
                            best_delta = delta
                            best_move = (route_i, cut_i, route_j, cut_j)

        # If no improving move found, stop
        if best_delta >= 0:
            break

        # Apply the best move
        route_i, cut_i, route_j, cut_j = best_move

        # Store original routes
        route1 = current.routes[route_i][:]
        route2 = current.routes[route_j][:]

        # Create new routes by exchanging tails
        current.routes[route_i] = route1[:cut_i + 1] + route2[cut_j + 1:]
        current.routes[route_j] = route2[:cut_j + 1] + route1[cut_i + 1:]

        # Update route lengths
        current.route_lengths[route_i] = calculate_route_length(D, current.routes[route_i])
        current.route_lengths[route_j] = calculate_route_length(D, current.routes[route_j])

        # Add to solutions list
        solutions.append(copy.deepcopy(current))

    return solutions


def check_two_opt_star_delta_correctness(D: np.ndarray, current: VRPResult,
                                            route_i: int, cut_i: int, route_j: int, cut_j: int, delta: float) -> bool:
        """Verify the correctness of the 2-opt* delta calculation by reconstructing the solution"""
        # Store original routes
        route1 = current.routes[route_i][:]
        route2 = current.routes[route_j][:]

        # Create new routes by exchanging tails
        new_route1 = route1[:cut_i + 1] + route2[cut_j + 1:]
        new_route2 = route2[:cut_j + 1] + route1[cut_i + 1:]

        # Calculate new lengths
        new_length1 = calculate_route_length(D, new_route1)
        new_length2 = calculate_route_length(D, new_route2)

        # Original lengths
        old_length1 = current.route_lengths[route_i]
        old_length2 = current.route_lengths[route_j]

        # Check if the delta matches the change in lengths
        return abs((new_length1 + new_length2) - (old_length1 + old_length2) - delta) < 1e-6