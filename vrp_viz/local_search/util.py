# Helper functions for delta calculations
from typing import List
import numpy as np


def calculate_shift_delta_intra(D: np.ndarray, route: List[int], pos_i: int, pos_j: int) -> float:
    """Calculate delta for intra-route shift move"""
    customer = route[pos_i]
    delta = 0.0

    # Remove customer from position i
    prev_i = route[pos_i - 1]
    next_i = route[pos_i + 1]
    delta -= D[prev_i, customer] + D[customer, next_i]
    delta += D[prev_i, next_i]

    # Insert customer at position j (after removal, so adjust index)
    actual_pos_j = pos_j #if pos_j < pos_i else pos_j - 1

    if actual_pos_j == len(route) - 1:  # Insert at end
        prev_j = route[actual_pos_j - 1]
        delta -= D[prev_j, route[-1]]  # route[-1] is depot
        delta += D[prev_j, customer] + D[customer, route[-1]]
    else:
        prev_j = route[actual_pos_j - 1]
        next_j = route[actual_pos_j]
        delta -= D[prev_j, next_j]
        delta += D[prev_j, customer] + D[customer, next_j]

    return delta


def calculate_swap_delta_intra(D: np.ndarray, route: List[int], pos_i: int, pos_j: int) -> float:
    """Calculate delta for intra-route swap move"""
    customer1 = route[pos_i]
    customer2 = route[pos_j]
    delta = 0.0

    if abs(pos_i - pos_j) == 1:
        # Adjacent customers
        if pos_i < pos_j:
            prev_c1 = route[pos_i - 1]
            next_c2 = route[pos_j + 1]
            # Remove: prev->c1 + c1->c2 + c2->next
            # Add: prev->c2 + c2->c1 + c1->next
            delta -= D[prev_c1, customer1] + D[customer1, customer2] + D[customer2, next_c2]
            delta += D[prev_c1, customer2] + D[customer2, customer1] + D[customer1, next_c2]
        else:
            prev_c2 = route[pos_j - 1]
            next_c1 = route[pos_i + 1]
            delta -= D[prev_c2, customer2] + D[customer2, customer1] + D[customer1, next_c1]
            delta += D[prev_c2, customer1] + D[customer1, customer2] + D[customer2, next_c1]
    else:
        # Non-adjacent customers
        prev_c1 = route[pos_i - 1]
        next_c1 = route[pos_i + 1]
        prev_c2 = route[pos_j - 1]
        next_c2 = route[pos_j + 1]

        # Remove old connections
        delta -= D[prev_c1, customer1] + D[customer1, next_c1]
        delta -= D[prev_c2, customer2] + D[customer2, next_c2]

        # Add new connections
        delta += D[prev_c1, customer2] + D[customer2, next_c1]
        delta += D[prev_c2, customer1] + D[customer1, next_c2]

    return delta


def calculate_two_opt_star_delta(D: np.ndarray, routes: List[List[int]],
                                 route_i: int, cut_i: int, route_j: int, cut_j: int) -> float:
    """Calculate delta for 2-opt* move without reconstructing the entire solution"""
    # Current connections at cut points
    # Route i: ... -> routes[route_i][cut_i] -> routes[route_i][cut_i+1] -> ...
    # Route j: ... -> routes[route_j][cut_j] -> routes[route_j][cut_j+1] -> ...

    node_i = routes[route_i][cut_i]
    node_i_next = routes[route_i][cut_i + 1]
    node_j = routes[route_j][cut_j]
    node_j_next = routes[route_j][cut_j + 1]

    # Remove old connections
    delta = -D[node_i, node_i_next] - D[node_j, node_j_next]

    # Add new connections
    delta += D[node_i, node_j_next] + D[node_j, node_i_next]

    return delta


def calculate_route_length(D: np.ndarray, route: List[int]) -> float:
    """Calculate the total length of a route"""
    if len(route) < 2:
        return 0.0

    total_length = 0.0
    for i in range(len(route) - 1):
        total_length += D[route[i], route[i + 1]]

    return total_length