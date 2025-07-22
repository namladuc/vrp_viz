import os
import shutil
import imageio
import matplotlib.pyplot as plt


def save_gif_frame(
    frame_path,
    title,
    locations,
    routes,
    unvisited=None,
    current_route=None,
    highlight_insertion=None,
    highlight_merge=None,
):
    """Vẽ trạng thái hiện tại của thuật toán và lưu thành frame cho GIF."""
    plt.figure(figsize=(24, 12))
    depot_loc = locations[0]
    all_customer_indices = set(range(1, len(locations)))

    # Vẽ các điểm khách hàng dựa trên trạng thái
    if unvisited is not None:
        unvisited_locs = [locations[i] for i in unvisited if i < len(locations)]
        visited_indices = all_customer_indices - set(unvisited)
        visited_locs = [locations[i] for i in visited_indices if i < len(locations)]
        if visited_locs:
            plt.scatter(*zip(*visited_locs), c="blue", alpha=0.7, label="Đã thăm")
        if unvisited_locs:
            plt.scatter(*zip(*unvisited_locs), c="gray", alpha=0.5, label="Chưa thăm")
    else:
        customer_locs = locations[1:]
        plt.scatter(*zip(*customer_locs), c="blue", label="Khách hàng")

    # Vẽ Kho
    plt.scatter(
        depot_loc[0],
        depot_loc[1],
        c="black",
        marker="s",
        s=150,
        zorder=5,
        label="Kho (Depot)",
    )

    # Đánh số các điểm
    for i, loc in enumerate(locations):
        if i > 0:
            plt.text(loc[0] + 0.5, loc[1] + 0.5, str(i))

    # Vẽ các tuyến đường đã hoàn thành
    colors = plt.cm.get_cmap("tab10", len(routes) + 5)
    for i, route in enumerate(routes):
        if not route:
            continue
        route_locs = [locations[0]] + [locations[c] for c in route] + [locations[0]]
        x_coords, y_coords = zip(*route_locs)
        plt.plot(x_coords, y_coords, color=colors(i), marker="o", label=f"Tuyến {i+1}")

    # Vẽ tuyến đang xây dựng (Nearest Neighbor)
    if current_route:
        route_locs = [locations[0]] + [locations[c] for c in current_route]
        x_coords, y_coords = zip(*route_locs)
        plt.plot(
            x_coords,
            y_coords,
            color=colors(len(routes)),
            linestyle="--",
            marker="o",
            label=f"Tuyến {len(routes)+1} (WIP)",
        )

    # Highlight hành động chèn (Cheapest Insertion)
    if highlight_insertion:
        u = highlight_insertion["customer"]
        route = highlight_insertion["route"]
        pos = highlight_insertion["pos"]
        loc_u = locations[u]

        if pos == 0:
            i, j = 0, route[0]
        elif pos == len(route):
            i, j = route[-1], 0
        else:
            i, j = route[pos - 1], route[pos]

        loc_i = locations[i]
        loc_j = locations[j]

        plt.plot([loc_i[0], loc_u[0]], [loc_i[1], loc_u[1]], "r--", linewidth=2)
        plt.plot(
            [loc_u[0], loc_j[0]],
            [loc_u[1], loc_j[1]],
            "r--",
            linewidth=2,
            label=f"Chèn {u}",
        )
        plt.plot(
            [loc_i[0], loc_j[0]],
            [loc_i[1], loc_j[1]],
            "k:",
            alpha=0.6,
            linewidth=2,
            label=f"Cạnh bị thay thế",
        )

    # Highlight hành động gộp (Clarke-Wright)
    if highlight_merge:
        u, v = highlight_merge["u"], highlight_merge["v"]
        loc_u = locations[u]
        loc_v = locations[v]
        plt.plot(
            [loc_u[0], loc_v[0]],
            [loc_u[1], loc_v[1]],
            "r--",
            linewidth=2.5,
            label=f"Gộp {u}-{v}",
        )

    plt.title(title, fontsize=16)
    plt.xlabel("Tọa độ X")
    plt.ylabel("Tọa độ Y")
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.savefig(frame_path)
    plt.close()

def create_gif(frames_dir, gif_path, duration=0.5):
    """Tạo file GIF từ một thư mục chứa các frame ảnh."""
    filenames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    images = [imageio.imread(os.path.join(frames_dir, f)) for f in filenames]
    if images:
        for _ in range(int(2/duration)):
             images.append(images[-1])
    imageio.mimsave(gif_path, images, duration=duration * len(images), loop=0)
    print(f"✅ Đã tạo ảnh GIF: {gif_path}")
    shutil.rmtree(frames_dir)