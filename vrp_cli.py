import time

import vrplib

from vrp_viz.utils import calculate_total_distance, visualize_routes
from vrp_viz.nearest_neighbor.nearnest_neighbor import nearest_neighbor
from vrp_viz.cheapest_insertion.cheapest_insertion import cheapest_insertion
from vrp_viz.clark_saving.clarke_saving import clarke_wright_smallest_saving_first
from vrp_viz.clark_saving.clarke_saving import clarke_wright_savings_nlog

def run_on_instance(instance_name, visualize=False):
    """Hàm chính để chạy các thuật toán trên một bộ dữ liệu."""
    print(f"\n\n{'='*20} ĐANG XỬ LÝ: {instance_name} {'='*20}")

    instance = vrplib.read_instance(instance_name)
    solution = vrplib.read_solution(instance_name.split(".")[0] + ".sol")
    locations = [list(coords) for coords in instance["node_coord"].tolist()]
    demands = [d for d in instance["demand"].tolist()]
    capacity = instance["capacity"]
    dist_matrix = instance["edge_weight"]

    print(f"Thông tin: {len(locations)-1} khách hàng, tải trọng xe: {capacity}")
    print(f"Lời giải tối ưu đã biết (BKS): {solution.get('cost', 'N/A')}")
    print("-" * 60)

    algorithms = {
        "Nearest Neighbor": nearest_neighbor,
        "Cheapest Insertion": cheapest_insertion,
        "Clarke-Wright Savings (n^3)": clarke_wright_smallest_saving_first,
        "Clarke-Wright Savings (nlogn)": clarke_wright_savings_nlog,
    }

    for name, func in algorithms.items():
        print(f"--> Chạy thuật toán: {name}")
        start_time = time.time()
        routes = func(dist_matrix, demands, capacity)
        end_time = time.time()

        total_dist = calculate_total_distance(routes, dist_matrix)

        print(f"    Tổng quãng đường: {total_dist:.2f}")
        print(f"    Thời gian thực thi: {end_time - start_time:.4f} giây")
        print(f"    Số tuyến đường: {len(routes)}")

        if visualize:
            visualize_routes(routes, locations, f"{name} - {instance_name} - {total_dist:.2f}")


if __name__ == "__main__":
    run_on_instance("data/P-n16-k8.vrp", visualize=True)
    # run_on_instance("data/A-n32-k5.vrp", visualize=True)
