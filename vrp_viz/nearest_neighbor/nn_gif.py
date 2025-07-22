import os
from ..gif_utils import save_gif_frame

def nearest_neighbor(dist_matrix, demands, capacity, locations=None, frames_dir=None):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    all_routes, frame_count = [], 0

    if frames_dir:
        save_gif_frame(os.path.join(frames_dir, f"f_{frame_count:03d}.png"), "Bắt đầu", locations, [], unvisited=unvisited)
        frame_count += 1
        
    while unvisited:
        current_route, current_load, current_location = [], 0, 0
        route_num = len(all_routes) + 1
        
        while True:
            best_candidate, min_dist = None, float("inf")
            for customer in unvisited:
                if current_load + demands[customer] <= capacity:
                    if dist_matrix[current_location][customer] < min_dist:
                        min_dist = dist_matrix[current_location][customer]
                        best_candidate = customer
            if best_candidate is not None:
                current_route.append(best_candidate)
                current_load += demands[best_candidate]
                current_location = best_candidate
                unvisited.remove(best_candidate)
                if frames_dir:
                    title = f"Tuyến {route_num}: Thêm KH {best_candidate}"
                    save_gif_frame(os.path.join(frames_dir, f"f_{frame_count:03d}.png"), title, locations, all_routes, unvisited, current_route)
                    frame_count += 1
            else:
                break
        if current_route:
            all_routes.append(current_route)
            if frames_dir:
                title = f"Hoàn thành Tuyến {route_num}"
                save_gif_frame(os.path.join(frames_dir, f"f_{frame_count:03d}.png"), title, locations, all_routes, unvisited)
                frame_count += 1
    
    if frames_dir:
        save_gif_frame(os.path.join(frames_dir, f"f_{frame_count:03d}.png"), "Kết quả cuối cùng", locations, all_routes)
    return all_routes