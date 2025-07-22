import os
from ..gif_utils import save_gif_frame


def clarke_wright_smallest_saving_first(
    dist_matrix, demands, capacity, locations=None, frames_dir=None
):
    num_customers = len(demands) - 1
    depot, frame_count = 0, 0
    routes = {
        i: {"path": [i], "demand": demands[i]} for i in range(1, num_customers + 1)
    }

    if frames_dir:
        title = "Bắt đầu: Mỗi KH một tuyến"
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            title,
            locations,
            [r["path"] for r in routes.values()],
        )
        frame_count += 1

    while len(routes) > 1:
        best_merge = {"saving": float("inf")}
        current_route_ids = list(routes.keys())
        if len(current_route_ids) < 2:
            break

        for i in range(len(current_route_ids)):
            for j in range(i + 1, len(current_route_ids)):
                r1_id, r2_id = current_route_ids[i], current_route_ids[j]
                r1, r2 = routes[r1_id], routes[r2_id]
                if r1["demand"] + r2["demand"] > capacity:
                    continue

                # Chỉ xét các điểm cuối
                u, v = r1["path"][-1], r2["path"][0]
                saving = (
                    dist_matrix[depot][u] + dist_matrix[depot][v] - dist_matrix[u][v]
                )
                if saving < best_merge["saving"]:
                    best_merge = {
                        "saving": saving,
                        "r1_id": r1_id,
                        "r2_id": r2_id,
                        "u": u,
                        "v": v,
                        "case": "end-start",
                    }

        if best_merge["saving"] == float("inf"):
            break

        r1_id, r2_id, u, v = (
            best_merge["r1_id"],
            best_merge["r2_id"],
            best_merge["u"],
            best_merge["v"],
        )

        if frames_dir:
            title = f"Gộp (saving nhỏ nhất): {u}-{v} ({best_merge['saving']:.2f})"
            save_gif_frame(
                os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                title,
                locations,
                [r["path"] for r in routes.values()],
                highlight_merge={"u": u, "v": v},
            )
            frame_count += 1

        routes[r1_id]["path"].extend(routes[r2_id]["path"])
        routes[r1_id]["demand"] += routes[r2_id]["demand"]
        del routes[r2_id]

        if frames_dir:
            title = f"Đã gộp Tuyến({r1_id}) và Tuyến({r2_id})"
            save_gif_frame(
                os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                title,
                locations,
                [r["path"] for r in routes.values()],
            )
            frame_count += 1

    if frames_dir:
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            "Kết quả cuối cùng",
            locations,
            [r["path"] for r in routes.values()],
        )
    return [r["path"] for r in routes.values()]


def clarke_wright_savings_nlog(
    dist_matrix, demands, capacity, locations=None, frames_dir=None
):
    """
    HÀM ĐÃ ĐƯỢC CẬP NHẬT THEO LOGIC CỦA BẠN (SỬ DỤNG ENDPOINT_STATUS)
    """
    num_customers, depot, frame_count = len(demands) - 1, 0, 0

    # Bước 1: Tính toán và sắp xếp savings
    savings = []
    for i in range(1, num_customers + 1):
        for j in range(i + 1, num_customers + 1):
            s_ij = dist_matrix[depot][i] + dist_matrix[depot][j] - dist_matrix[i][j]
            if s_ij > 0:
                savings.append({"i": i, "j": j, "saving": s_ij})
    savings.sort(key=lambda x: x["saving"], reverse=True)

    # Bước 2: Khởi tạo tuyến và trạng thái điểm cuối (endpoint_status)
    routes = {
        i: {"path": [i], "demand": demands[i]} for i in range(1, num_customers + 1)
    }
    endpoint_status = [None] * (len(demands))
    for i in range(1, num_customers + 1):
        endpoint_status[i] = (
            i  # Mỗi KH ban đầu là điểm cuối của tuyến mang ID của chính nó
        )

    if frames_dir:
        title = "Bắt đầu: Mỗi KH một tuyến"
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            title,
            locations,
            [r["path"] for r in routes.values()],
        )
        frame_count += 1

    # Bước 3: Lặp qua savings để hợp nhất
    for s in savings:
        i, j = s["i"], s["j"]
        route_id_i = endpoint_status[i]
        route_id_j = endpoint_status[j]

        # Kiểm tra điều kiện hợp nhất theo logic của bạn
        if (
            route_id_i is not None
            and route_id_j is not None
            and route_id_i != route_id_j
        ):
            route_i = routes[route_id_i]
            route_j = routes[route_id_j]

            if route_i["demand"] + route_j["demand"] > capacity:
                continue

            # Lưu frame trước khi hợp nhất
            if frames_dir:
                title = f"Xét gộp {i}-{j} (saving: {s['saving']:.2f})"
                save_gif_frame(
                    os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                    title,
                    locations,
                    [r["path"] for r in routes.values()],
                    highlight_merge={"u": i, "v": j},
                )
                frame_count += 1

            path_i, path_j = route_i["path"], route_j["path"]

            # Hợp nhất tuyến j vào tuyến i
            if path_i[-1] == i and path_j[0] == j:
                route_i["path"].extend(path_j)
            elif path_i[0] == i and path_j[-1] == j:
                path_j.extend(path_i)
                route_i["path"] = path_j
            elif path_i[-1] == i and path_j[-1] == j:
                path_j.reverse()
                route_i["path"].extend(path_j)
            elif path_i[0] == i and path_j[0] == j:
                path_i.reverse()
                path_i.extend(path_j)
            else:
                continue  # Không hợp lệ (sẽ không xảy ra nếu logic endpoint đúng)

            # Cập nhật thông tin sau khi hợp nhất thành công
            route_i["demand"] += route_j["demand"]

            # Cập nhật endpoint_status
            endpoint_status[i] = None
            endpoint_status[j] = None
            new_start, new_end = route_i["path"][0], route_i["path"][-1]
            endpoint_status[new_start] = route_id_i
            endpoint_status[new_end] = route_id_i

            # Xóa tuyến đã được hợp nhất
            del routes[route_id_j]

            # Lưu frame sau khi hợp nhất
            if frames_dir:
                title = f"Đã gộp {i}-{j}"
                save_gif_frame(
                    os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
                    title,
                    locations,
                    [r["path"] for r in routes.values()],
                )
                frame_count += 1

    final_routes = [r["path"] for r in routes.values()]
    if frames_dir:
        save_gif_frame(
            os.path.join(frames_dir, f"f_{frame_count:03d}.png"),
            "Kết quả cuối cùng",
            locations,
            final_routes,
        )
    return final_routes
