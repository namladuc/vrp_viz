import copy
from vrp_viz.local_search.util import *
from vrp_viz.map_viz.stepwise_map import VRPResult


def shift_local_search(
        D: np.ndarray,
        demands: List[float],
        vehicle_capacity: float,
        max_stops_per_route,  # Ignored
        num_vehicles,  # Ignored
        depot_idx,  # Ignored
        current_solution: VRPResult
) -> List[VRPResult]:
    """
    Shift move: Remove a customer from one position and insert it at another position
    (intra-route only - same route)
    """
    solutions = [current_solution]
    current = copy.deepcopy(current_solution)

    while True:
        best_delta = float('inf')
        best_move = None

        # Try all possible shift moves within each route
        for route_idx in range(len(current.routes)):
            route = current.routes[route_idx]
            # Skip routes with less than 4 nodes (depot-customer1-customer2-depot minimum)
            if len(route) < 4:
                continue

            # Skip depot nodes (first and last are always depot)
            for pos_i in range(1, len(route) - 1):

                # Try inserting to all other positions in the same route
                for pos_j in range(1, len(route)):
                    # Skip the same position and adjacent positions
                    if abs(pos_i - pos_j) <= 1:
                        continue

                    # Calculate delta
                    delta = calculate_shift_delta_intra(D, route, pos_i, pos_j)

                    # Verify correctness. Comment this out when done testing for a BOOM speed up.
                    # if not check_shift_delta_correctness(D, current, route_idx, pos_i, pos_j, delta):
                    #     raise ValueError("Shift delta calculation error")

                    if delta < best_delta:
                        best_delta = delta
                        best_move = (route_idx, pos_i, pos_j)

        # If no improving move found, stop
        if best_delta >= 0:
            break

        # Apply the best move
        route_idx, pos_i, pos_j = best_move
        customer = current.routes[route_idx][pos_i]

        # Remove customer from original position
        current.routes[route_idx].pop(pos_i)

        # Adjust insertion position if inserting after removal point
        if pos_j > pos_i:
            pos_j -= 1

        # Insert customer at new position
        current.routes[route_idx].insert(pos_j, customer)

        # Update route length
        current.route_lengths[route_idx] = calculate_route_length(D, current.routes[route_idx])
        # current.route_lengths[route_idx] += best_delta

        # Add to solutions list
        solutions.append(copy.deepcopy(current))

    return solutions


def check_shift_delta_correctness(
        D: np.ndarray,
        current: VRPResult,
        route_idx: int,
        pos_i: int,
        pos_j: int,
        delta: float,
) -> bool:
    """Utility to check if calculated shift delta is correct"""
    customer = current.routes[route_idx][pos_i]
    # Check delta correctness
    clone_sol = copy.deepcopy(current)
    # Remove customer from original position
    clone_sol.routes[route_idx].pop(pos_i)
    # Adjust insertion position if inserting after removal point
    if pos_j > pos_i:
        pos_j -= 1
    # Insert customer at new position
    clone_sol.routes[route_idx].insert(pos_j, customer)
    old_length = clone_sol.route_lengths[route_idx]
    # Update route length
    clone_sol.route_lengths[route_idx] = calculate_route_length(D, clone_sol.routes[route_idx])
    new_length = clone_sol.route_lengths[route_idx]
    if abs(new_length - old_length - delta) > 0.1:
        print("Calc error")
        print("New: ", new_length)
        print("Old: ", old_length)
        print("Delta: ", delta)
        print("Pos i, j: ", pos_i, pos_j)

    # Check if delta matches the actual length difference
    return abs(new_length - old_length - delta) < 0.1