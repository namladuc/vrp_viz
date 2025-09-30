import copy
from vrp_viz.local_search.util import *
from vrp_viz.map_viz.stepwise_map import VRPResult


def swap_local_search(
        D: np.ndarray,
        demands: List[float],
        vehicle_capacity: float,
        max_stops_per_route,  # Ignored
        num_vehicles,  # Ignored
        depot_idx,  # Ignored
        current_solution: VRPResult
) -> List[VRPResult]:
    """
    Swap move: Exchange positions of two customers
    (intra-route only - same route)
    """
    solutions = [current_solution]
    current = copy.deepcopy(current_solution)

    while True:
        best_delta = float('inf')
        best_move = None

        # Try all possible swap moves within each route
        for route_idx in range(len(current.routes)):
            route = current.routes[route_idx]
            # Skip routes with less than 4 nodes (depot-customer1-customer2-depot minimum)
            if len(route) < 4:
                continue

            # Skip depot nodes
            for pos_i in range(1, len(route) - 1):
                for pos_j in range(pos_i + 1, len(route) - 1):

                    # Calculate delta
                    delta = calculate_swap_delta_intra(D, route, pos_i, pos_j)

                    # Verify correctness. Comment this out when done testing for a BOOM speed up.
                    if not check_swap_delta_correctness(D, current, route_idx, pos_i, pos_j, delta):
                        raise ValueError("Swap delta calculation error")

                    if delta < best_delta:
                        best_delta = delta
                        best_move = (route_idx, pos_i, pos_j)

        # If no improving move found, stop
        if best_delta >= 0:
            break

        # Apply the best move
        route_idx, pos_i, pos_j = best_move

        # Swap customers
        current.routes[route_idx][pos_i], current.routes[route_idx][pos_j] = \
            current.routes[route_idx][pos_j], current.routes[route_idx][pos_i]

        # Update route length
        current.route_lengths[route_idx] += best_delta

        # Add to solutions list
        solutions.append(copy.deepcopy(current))

    return solutions


def check_swap_delta_correctness(D: np.ndarray, current: VRPResult, route_idx: int, pos_i: int, pos_j: int, delta: float) -> bool:
    """Utility to verify correctness of swap delta calculation"""
    clone_sol = copy.deepcopy(current)
    original_length = clone_sol.route_lengths[route_idx]
    route = clone_sol.routes[route_idx][:]

    # Perform swap
    route[pos_i], route[pos_j] = route[pos_j], route[pos_i]
    new_length = calculate_route_length(D, route)

    return abs((original_length + delta) - new_length) < 1e-6