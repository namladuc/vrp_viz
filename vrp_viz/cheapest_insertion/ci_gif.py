import os
from ..gif_utils import save_gif_frame


def cheapest_insertion(dist_matrix, demands, capacity, locations=None, frames_dir=None):
    num_customers = len(demands) - 1
    unvisited = list(range(1, num_customers + 1))
    frame_count = 0

    # Bắt đầu bằng 1 tuyến với khách hàng xa nhất
    farthest_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
    routes = [[farthest_cust]]
    route_loads = [demands[farthest_cust]]
    unvisited.remove(farthest_cust)

    if frames_dir:
        title = f"Bắt đầu với KH xa nhất: {farthest_cust}"
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            title,
            locations,
            routes,
            unvisited,
        )
        frame_count += 1

    while unvisited:
        best_insertion = {"cost": float("inf")}
        for u in unvisited:
            for r_idx, route in enumerate(routes):
                if route_loads[r_idx] + demands[u] > capacity:
                    continue
                for pos in range(len(route) + 1):
                    if pos == 0:
                        i, j = 0, route[0]
                    elif pos == len(route):
                        i, j = route[-1], 0
                    else:
                        i, j = route[pos - 1], route[pos]
                    cost = dist_matrix[i][u] + dist_matrix[u][j] - dist_matrix[i][j]
                    if cost < best_insertion["cost"]:
                        best_insertion = {
                            "cost": cost,
                            "customer": u,
                            "route_idx": r_idx,
                            "pos": pos,
                            "route": route[:],
                        }

        if best_insertion["cost"] != float("inf"):
            u, r_idx, pos = (
                best_insertion["customer"],
                best_insertion["route_idx"],
                best_insertion["pos"],
            )

            if frames_dir:
                title = f"Xem xét chèn KH {u} (chi phí: {best_insertion['cost']:.2f})"
                save_gif_frame(
                    os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                    title,
                    locations,
                    routes,
                    unvisited,
                    highlight_insertion=best_insertion,
                )
                frame_count += 1

            routes[r_idx].insert(pos, u)
            route_loads[r_idx] += demands[u]
            unvisited.remove(u)

            if frames_dir:
                title = f"Đã chèn KH {u} vào Tuyến {r_idx + 1}"
                save_gif_frame(
                    os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                    title,
                    locations,
                    routes,
                    unvisited,
                )
                frame_count += 1
        else:
            if not unvisited:
                break
            next_cust = max(unvisited, key=lambda c: dist_matrix[0][c])
            routes.append([next_cust])
            route_loads.append(demands[next_cust])
            unvisited.remove(next_cust)
            if frames_dir:
                title = f"Không chèn được, tạo Tuyến mới với KH {next_cust}"
                save_gif_frame(
                    os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                    title,
                    locations,
                    routes,
                    unvisited,
                )
                frame_count += 1

    if frames_dir:
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            "Kết quả cuối cùng",
            locations,
            routes,
        )
    return routes
