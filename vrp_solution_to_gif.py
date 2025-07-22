import math
import time
import matplotlib.pyplot as plt
import vrplib
import os
import imageio
import shutil

from vrp_viz.utils import calculate_total_distance
from vrp_viz.gif_utils import create_gif
from vrp_viz.nearest_neighbor.nn_gif import nearest_neighbor
from vrp_viz.cheapest_insertion.ci_gif import cheapest_insertion
from vrp_viz.clark_saving.cs_gif import clarke_wright_smallest_saving_first
from vrp_viz.clark_saving.cs_gif import clarke_wright_savings_nlog


def run_on_instance(instance_name, create_gifs=False):
    """Hàm chính để chạy các thuật toán và tùy chọn tạo GIF."""
    print(f"\n\n{'='*20} ĐANG XỬ LÝ: {instance_name} {'='*20}")
    instance = vrplib.read_instance(instance_name)
    locations = [list(c) for c in instance["node_coord"]]
    demands = [d for d in instance["demand"]]
    capacity = instance["capacity"]
    dist_matrix = instance["edge_weight"]
    
    print(f"Thông tin: {len(locations)-1} khách hàng, tải trọng xe: {capacity}")
    print("-" * 60)

    algorithms = {
        "Nearest_Neighbor": nearest_neighbor,
        "Cheapest_Insertion": cheapest_insertion,
        "Clarke-Wright_Smallest_Saving_First": clarke_wright_smallest_saving_first,
        "Clarke-Wright_Savings_nlogn": clarke_wright_savings_nlog,
    }

    for name, func in algorithms.items():
        print(f"--> Chạy thuật toán: {name}")
        
        frames_dir, gif_path = None, None
        if create_gifs:
            frames_dir = f"frames_{name}"
            gif_path = f"gif/animation_{name}.gif"
            if os.path.exists(frames_dir): shutil.rmtree(frames_dir)
            os.makedirs(frames_dir)
            print(f"    Tạo thư mục frame: {frames_dir}")

        start_time = time.time()
        routes = func(dist_matrix, demands, capacity, locations=locations, frames_dir=frames_dir)
        end_time = time.time()

        total_dist = calculate_total_distance(routes, dist_matrix)
        print(f"    Tổng quãng đường: {total_dist:.2f}")
        print(f"    Thời gian thực thi: {end_time - start_time:.4f} giây")
        
        if create_gifs:
            print(f"    🎬 Đang tạo GIF, vui lòng chờ...")
            create_gif(frames_dir, gif_path, duration=10)
        print("-" * 40)


if __name__ == "__main__":
    # Chạy trên bộ dữ liệu nhỏ và tạo GIF cho tất cả thuật toán
    run_on_instance("data/P-n16-k8.vrp", create_gifs=True)