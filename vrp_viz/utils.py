import matplotlib.pyplot as plt

def calculate_total_distance(routes, dist_matrix):
    """Tính tổng khoảng cách của tất cả các tuyến đường."""
    total_dist = 0
    depot = 0
    for route in routes:
        if not route:
            continue
        route_dist = dist_matrix[depot][route[0]]
        for i in range(len(route) - 1):
            route_dist += dist_matrix[route[i]][route[i + 1]]
        route_dist += dist_matrix[route[-1]][depot]
        total_dist += route_dist
    return total_dist


def visualize_routes(routes, locations, title):
    """Vẽ các tuyến đường lên đồ thị."""
    plt.figure(figsize=(12, 12))
    depot_loc = locations[0]
    plt.scatter(
        depot_loc[0],
        depot_loc[1],
        c="black",
        marker="s",
        s=150,
        zorder=5,
        label="Kho (Depot)",
    )
    customer_locs = locations[1:]
    plt.scatter(*zip(*customer_locs), c="gray", zorder=3, label="Khách hàng")
    for i, loc in enumerate(locations):
        if i > 0:
            plt.text(loc[0] + 0.5, loc[1] + 0.5, str(i))

    colors = plt.get_cmap("tab10", len(routes))
    for i, route in enumerate(routes):
        if not route:
            continue
        route_locs = [locations[0]] + [locations[c] for c in route] + [locations[0]]
        x_coords, y_coords = zip(*route_locs)
        plt.plot(x_coords, y_coords, color=colors(i), marker="o", label=f"Tuyến {i+1}")
    plt.title(title, fontsize=16)
    plt.xlabel("Tọa độ X")
    plt.ylabel("Tọa độ Y")
    plt.legend()
    plt.grid(True)
    plt.show()
    
def visualize_step_streamlit(locations, routes, title, total_distance, special_colors=None, highlighted_edges=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    depot_loc = locations[0]
    serviced_customers = set(customer for route in routes for customer in route)

    for i, loc in enumerate(locations[1:], 1):
        if i in serviced_customers:
            ax.scatter(loc[0], loc[1], c='lightblue', zorder=3, label='Đã phục vụ' if i == 1 else "")
        else:
            ax.scatter(loc[0], loc[1], c='gray', zorder=3, label='Chưa phục vụ' if i == 1 else "")
        ax.text(loc[0] + 0.8, loc[1] + 0.8, str(i), fontsize=10)

    ax.scatter(depot_loc[0], depot_loc[1], c='black', marker='s', s=150, zorder=5, label='Kho (Depot)')

    colors = plt.get_cmap('tab10', 10)
    for i, route in enumerate(routes):
        if not route: continue
        route_locs = [locations[0]] + [locations[c] for c in route] + [locations[0]]
        x_coords, y_coords = zip(*route_locs)
        ax.plot(x_coords, y_coords, color=colors(i % 10), marker='o', alpha=0.7)

    if highlighted_edges:
        for edge in highlighted_edges:
            u, v = edge
            if u < len(locations) and v < len(locations):
                loc_u, loc_v = locations[u], locations[v]
                ax.plot([loc_u[0], loc_v[0]], [loc_u[1], loc_v[1]], 'g--', linewidth=2.5, zorder=10)

    if special_colors:
        for node_id, color in special_colors.items():
            if node_id > 0 and node_id < len(locations):
                loc = locations[node_id]
                ax.scatter(loc[0], loc[1], c=color, s=200, zorder=10, alpha=0.8, edgecolors='black')

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())
    ax.set_title(f"{title}\nTổng quãng đường hiện tại: {total_distance:.2f}", fontsize=16)
    ax.set_xlabel("Tọa độ X")
    ax.set_ylabel("Tọa độ Y")
    ax.grid(True)
    return fig