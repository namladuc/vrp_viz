from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np

import time
import requests
import folium
from folium.plugins import MiniMap, Fullscreen, MeasureControl, MousePosition, MarkerCluster, BeautifyIcon, AntPath
from branca.element import MacroElement, Template

BASE_URL = "https://router.project-osrm.org"
PROFILE = "driving"

_VEHICLE_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]

def _veh_color(veh_id: int) -> str:
    return _VEHICLE_COLORS[veh_id % len(_VEHICLE_COLORS)]

def _html_overlay_box(title: str, html_body: str) -> MacroElement:
    """Tạo ô mô tả cố định góc phải, có thể ẩn/hiện bằng layer control."""
    tmpl = Template(f"""
    {{% macro html(this, kwargs) %}}
    <div id="vrp-info-box" style="
        position: fixed; 
        top: 10px; right: 10px; 
        z-index: 1000; 
        background: rgba(255,255,255,0.95); 
        padding: 12px 14px; 
        border-radius: 10px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 360px; font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
        ">
      <div style="font-weight:600; margin-bottom:6px;">{title}</div>
      <div style="font-size: 13px; line-height: 1.35;">{html_body}</div>
    </div>
    {{% endmacro %}}
    """)
    el = MacroElement()
    el._template = tmpl
    return el


def get_route_from_api(coords, names: List[str]):
    route_url = f"{BASE_URL}/route/v1/{PROFILE}/{coords}?overview=full&geometries=geojson&steps=false"
    try:
        r = requests.get(
            route_url, headers={"User-Agent": "VRP-MapDemo/1.0"}, timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == "Ok" and data.get("routes"):
                geo = data["routes"][0]["geometry"]
                if geo and geo.get("type") == "LineString":
                    return geo, data
            else:
                print(f"Route API không trả Ok cho {names[1]}")
        else:
            print(f"HTTP {r.status_code} khi gọi route {names[1]}")
    except Exception as ex:
        print("Lỗi route:", ex)
    return None, None


class VRPResult:
    def __init__(
        self, routes: List[List[int]], route_lengths: List[float], steps: List[Dict]
    ):
        """
        routes: danh sách tuyến, mỗi tuyến là danh sách chỉ số điểm (theo input points, 0=depot).
        route_lengths: tổng độ dài (m) mỗi tuyến.
        steps: danh sách các bước để visualize (edge thêm theo thứ tự).
              Mỗi step: {"vehicle": k, "from": i, "to": j}
        """
        self.routes = routes
        self.route_lengths = route_lengths
        self.steps = steps


def make_stepwise_map(
    names: List[str],
    points_latlon: List[Tuple[float, float]],
    node_ids: List[int],
    vrp: VRPResult,
    out_html: str = "vrp_stepwise_map.html",
) -> str:
    """
    Tạo bản đồ Folium với:
      - markers cho depot & khách hàng
      - layer theo từng 'step' của heuristic
      - layer gộp theo từng 'route'
    """
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(
        location=center, zoom_start=12, control_scale=True, prefer_canvas=True
    )

    # Markers
    folium.Marker(
        points_latlon[0], tooltip="Depot", icon=folium.Icon(color="green")
    ).add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker(
            (lat, lon), radius=5, tooltip=f"Point {idx}", fill=True
        ).add_to(m)

    # Layer per route
    for r_id, route in enumerate(vrp.routes):
        fg = folium.FeatureGroup(name=f"Route #{r_id}")
        # vẽ từng edge trong route
        for a, b in zip(route[:-1], route[1:]):
            u, v = node_ids[a], node_ids[b]
            name_u, name_v = names[u], names[v]
            geom, data_map = get_route_from_api(
                coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
                names=[name_u, name_v],
            )
            if geom is None:
                print(f"Không lấy được route {name_u} -> {name_v}")
                continue
            line_coords = [[latlon[1], latlon[0]] for latlon in geom["coordinates"]]
            folium.PolyLine(
                locations=line_coords,
                color="orange",
                weight=3,
                opacity=0.8,
                tooltip=f"Route {names[0]} -> {names[1]} ({data_map['routes'][0]['distance']/1000:.2f} km)",
            ).add_to(fg)
            time.sleep(0.3)  # tránh spam
        fg.add_to(m)

    # Step-by-step layers
    for s_id, s in enumerate(vrp.steps, start=1):
        fg = folium.FeatureGroup(
            name=f"Step {s_id}: v{ s['vehicle'] } {s['from']}→{s['to']}"
        )
        u, v = node_ids[s["from"]], node_ids[s["to"]]
        name_u, name_v = names[u], names[v]
        geom, data_map = get_route_from_api(
            coords=f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}",
            names=[name_u, name_v],
        )

        folium.PolyLine(
            locations=line_coords,
            color="orange",
            weight=3,
            opacity=0.8,
            tooltip=f"Route {names[0]} -> {names[1]} ({data_map['routes'][0]['distance']/1000:.2f} km)",
        ).add_to(fg)

        # đánh dấu đầu/cuối
        folium.CircleMarker(
            points_latlon[s["from"]], radius=6, tooltip=f"from {s['from']}", color="red"
        ).add_to(fg)
        folium.CircleMarker(
            points_latlon[s["to"]], radius=6, tooltip=f"to {s['to']}", color="blue"
        ).add_to(fg)
        fg.add_to(m)
        time.sleep(0.3)  # tránh spam

    folium.LayerControl().add_to(m)
    m.save(out_html)
    return out_html
