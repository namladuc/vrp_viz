from typing import List, Tuple
import time
import json
import numpy as np
import folium
from folium.plugins import (
    MiniMap,
    Fullscreen,
    MeasureControl,
    MousePosition,
    MarkerCluster,
    BeautifyIcon,
    AntPath,
)

from folium.plugins import (
    MiniMap,
    Fullscreen,
    MeasureControl,
    MousePosition,
    MarkerCluster,
    BeautifyIcon,
    AntPath,
    PolyLineTextPath,
)
from branca.element import MacroElement, Template

from .stepwise_map import get_route_from_api, VRPResult

# ===== Helpers =====

_VEHICLE_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def _veh_color(veh_id: int) -> str:
    return _VEHICLE_COLORS[veh_id % len(_VEHICLE_COLORS)]


def _html_overlay_box_bottom_right(title: str, html_body: str) -> MacroElement:
    """Hộp mô tả có nút Hide/Show ở góc phải-dưới, tránh đè LayerControl."""
    tmpl = Template(
        f"""
    {{% macro html(this, kwargs) %}}
    <div id="vrp-info-box" style="
        position: fixed; bottom: 12px; right: 12px; z-index: 1000;
        background: rgba(255,255,255,0.96); padding: 12px 14px; border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 360px;
        font-family: system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
        <div style="font-weight:600;">{title}</div>
        <button id="vrp-info-toggle" style="border:none;background:#f2f2f2;padding:4px 8px;border-radius:6px;cursor:pointer;">Hide</button>
      </div>
      <div id="vrp-info-body" style="font-size:13px;line-height:1.35;margin-top:6px;">{html_body}</div>
    </div>
    <script>
      (function(){{
        const btn  = document.getElementById('vrp-info-toggle');
        const body = document.getElementById('vrp-info-body');
        let shown = true;
        btn.addEventListener('click', function(){{
          shown = !shown;
          body.style.display = shown ? 'block' : 'none';
          btn.textContent = shown ? 'Hide' : 'Show';
        }});
      }})();
    </script>
    {{% endmacro %}}
    """
    )
    el = MacroElement()
    el._template = tmpl
    return el


def _add_step_controller(
    map_obj: folium.Map, step_vars, step_labels, play_interval_ms=900, cumulative=False
):
    import json

    map_var = map_obj.get_name()  # ví dụ: map_123456
    js_layers = json.dumps(step_vars)  # ["feature_group_xxx", ...]
    js_labels = json.dumps(step_labels)
    cum_js = "true" if cumulative else "false"

    tmpl = Template(
        f"""
    {{% macro html(this, kwargs) %}}
    <div id="vrp-step-ctrl" style="
        position: fixed; top: 12px; right: 12px; z-index: 1100;
        background: rgba(255,255,255,0.96); padding: 10px 12px; border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15); width: 320px;
        font-family: system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
      <div style="font-weight:600; margin-bottom:8px;">Step Controller</div>
      <div style="display:flex; gap:6px; flex-wrap:wrap;">
        <button id="btnPrev"  style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer;">Prev</button>
        <button id="btnNext"  style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer;">Next</button>
        <button id="btnPlay"  style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer;">Play</button>
        <button id="btnPause" style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer;">Pause</button>
        <button id="btnReset" style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;background:#fafafa;cursor:pointer;">Reset</button>
      </div>
      <div style="margin-top:8px;">
        <input id="stepRange" type="range" min="0" max="0" value="0" style="width:100%;">
        <div id="stepLabel" style="font-size:12px;margin-top:4px;color:#666;">—</div>
      </div>
    </div>
    <script>
      (function(){{
        // map thực sự (biến global do Folium tạo)
        var mapRef = {map_var};
        var stepVars   = {js_layers};
        var stepLabels = {js_labels};
        var cumulative = {cum_js};

        function getLayerByVarName(varName) {{
          // Folium đặt từng FeatureGroup vào window[varName]
          var l = window[varName];
          // đôi khi chưa sẵn sàng; chỉ nhận nếu có addTo/remove
          if (l && (typeof l.addTo === 'function' || typeof l.addLayer === 'function')) return l;
          return null;
        }}

        function safeHasLayer(map, layer) {{
          if (!map || !layer) return false;
          if (typeof map.hasLayer === 'function') return map.hasLayer(layer);
          var id = layer._leaflet_id;
          return !!(map._layers && id && map._layers[id]);
        }}

        function safeAddLayer(map, layer) {{
          if (!map || !layer) return;
          if (!safeHasLayer(map, layer)) {{
            try {{ map.addLayer(layer); }} catch(e) {{ console.warn(e); }}
          }}
        }}

        function safeRemoveLayer(map, layer) {{
          if (!map || !layer) return;
          if (safeHasLayer(map, layer)) {{
            try {{ map.removeLayer(layer); }} catch(e) {{ console.warn(e); }}
          }}
        }}

        function showIndex(idx) {{
          for (var i=0; i<stepVars.length; i++) {{
            var layer = getLayerByVarName(stepVars[i]);
            if (!layer) continue; // bỏ qua layer chưa khởi tạo
            if (cumulative ? (i <= idx) : (i === idx)) {{
              safeAddLayer({map_var}, layer);
            }} else {{
              safeRemoveLayer({map_var}, layer);
            }}
          }}
          var labEl = document.getElementById('stepLabel');
          if (labEl) labEl.textContent = stepLabels[idx] || ("Step " + (idx+1));
          var rngEl = document.getElementById('stepRange');
          if (rngEl) rngEl.value = idx;
        }}

        // slider
        var rangeEl = document.getElementById('stepRange');
        if (rangeEl) {{
          rangeEl.max = Math.max(0, stepVars.length - 1);
          rangeEl.addEventListener('input', function() {{
            cur = clamp(parseInt(this.value || "0", 10));
            showIndex(cur);
          }});
        }}

        var cur = 0;
        var timer = null;
        function clamp(v) {{ return Math.max(0, Math.min(stepVars.length-1, isNaN(v)?0:v)); }}
        function next()  {{ cur = clamp(cur+1); showIndex(cur); }}
        function prev()  {{ cur = clamp(cur-1); showIndex(cur); }}
        function play()  {{
          if (timer) return;
          timer = setInterval(function(){{
            if (cur >= stepVars.length-1) {{ clearInterval(timer); timer = null; return; }}
            cur += 1; showIndex(cur);
          }}, {play_interval_ms});
        }}
        function pause() {{ if (timer) {{ clearInterval(timer); timer = null; }} }}
        function reset() {{ pause(); cur = 0; showIndex(cur); }}

        var bNext  = document.getElementById('btnNext');
        var bPrev  = document.getElementById('btnPrev');
        var bPlay  = document.getElementById('btnPlay');
        var bPause = document.getElementById('btnPause');
        var bReset = document.getElementById('btnReset');
        if (bNext)  bNext.onclick  = next;
        if (bPrev)  bPrev.onclick  = prev;
        if (bPlay)  bPlay.onclick  = play;
        if (bPause) bPause.onclick = pause;
        if (bReset) bReset.onclick = reset;

        // khởi tạo: tìm step nào đang bật; nếu không có thì chọn 0
        (function initFindCurrent(){{
          var found = -1;
          for (var i=0; i<stepVars.length; i++) {{
            var layer = getLayerByVarName(stepVars[i]);
            if (safeHasLayer({map_var}, layer)) {{ found = i; break; }}
          }}
          cur = (found >= 0) ? found : 0;
          showIndex(cur);
        }})();
      }})();
    </script>
    {{% endmacro %}}
    """
    )
    el = MacroElement()
    el._template = tmpl
    map_obj.get_root().add_child(el)


# ===== Main function =====


def make_stepwise_map(
    names: List[str],
    points_latlon: List[Tuple[float, float]],  # (lat, lon)
    node_ids: List[int],  # map index in route -> index in names/points_latlon
    vrp,  # VRPResult có .routes, .steps
    cache_location: dict = None,  # cache JSON từ OSRM/GraphHopper
    out_html: str = "vrp_stepwise_map.html",
    description_html: str = None,  # mô tả tự do (HTML)
    throttle_s: float = 0.15,  # hạn chế gọi API dày
    cumulative: bool = False,  # giữ vệt step đã đi
    play_interval_ms: int = 900,  # tốc độ Play
) -> str:
    """
    Vẽ bản đồ Folium cho VRP:
      - Layer gộp theo từng Route (animate AntPath, màu theo vehicle)
      - Layer từng Step (mặc định bật Step 1)
      - Hộp mô tả ở góc phải-dưới (Hide/Show)
      - Step Controller (Prev/Next/Play/Pause/Reset + slider) ở góc phải-trên
      - Plugins: MiniMap, Fullscreen, Measure, MousePosition, MarkerCluster

    Yêu cầu bên ngoài:
      - get_route_from_api(coords="lon1,lat1;lon2,lat2", names=[name_u, name_v]) -> (geom, data_map)
        * geom: GeoJSON LineString {"coordinates": [[lon,lat], ...]}
        * data_map["routes"][0]["distance"], ["duration"] (đơn vị m, s)
    """
    # — Base map —
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(
        location=center,
        zoom_start=12,
        control_scale=True,
        prefer_canvas=True,
        tiles="CartoDB positron",
    )

    # — Utilities plugins —
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    Fullscreen().add_to(m)
    MeasureControl(
        primary_length_unit="meters", secondary_length_unit="kilometers"
    ).add_to(m)
    MousePosition(position="bottomleft", separator=" | ", prefix="Lat/Lon").add_to(m)

    # — Description overlay —
    if description_html is None:
        n_routes = len(getattr(vrp, "routes", []))
        n_steps = len(getattr(vrp, "steps", []))
        description_html = (
            f"<b>Tổng quan:</b> {n_routes} route, {n_steps} bước.<br>"
            f"<span style='opacity:0.7'>Dùng Step Controller (góc phải-trên) để duyệt step.</span>"
        )
    m.get_root().add_child(
        _html_overlay_box_bottom_right("VRP – Stepwise Viewer", description_html)
    )

    # — Markers: Depot & Customers —
    depot_latlon = points_latlon[0]
    folium.Marker(
        depot_latlon,
        tooltip="Depot",
        popup=folium.Popup(f"<b>Depot</b><br>{names[0]}", max_width=260),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(m)

    cluster = MarkerCluster(name="Customers").add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker(
            (lat, lon),
            radius=5,
            fill=True,
            weight=1,
            fill_opacity=0.9,
            tooltip=f"Customer #{idx}: {names[idx]}",
            popup=folium.Popup(
                f"<b>Customer #{idx}</b><br/>{names[idx]}<br/>lat: {lat:.6f}, lon: {lon:.6f}",
                max_width=280,
            ),
        ).add_to(cluster)

    # — Draw per-route layers —
    all_poly_bounds = []
    for r_id, route in enumerate(getattr(vrp, "routes", [])):
        color = _veh_color(r_id)
        fg = folium.FeatureGroup(name=f"Route #{r_id}", show=False)
        total_dist_km = 0.0

        for a, b in zip(route[:-1], route[1:]):
            u, v = node_ids[a], node_ids[b]
            name_u, name_v = names[u], names[v]
            key_name = f"{u}:{v}"
            key_loc = f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}"
            geom, data_map = cache_location.get(
                key_name
            )
            
            if geom is None:
                print(f"Không lấy được route {name_u} -> {name_v}")
                continue

            line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
            all_poly_bounds.extend(line_coords)

            dist_m = data_map["routes"][0].get("distance", 0.0)
            dur_s = data_map["routes"][0].get("duration", 0.0)
            total_dist_km += dist_m / 1000.0

            AntPath(
                locations=line_coords,
                tooltip=f"{name_u} → {name_v} • {dist_m/1000:.2f} km • {dur_s/60:.1f} min",
                delay=600,
                dash_array=[10, 20],
                weight=4,
                opacity=0.85,
                color=color,
            ).add_to(fg)

        if route:
            first_idx = node_ids[route[0]]
            folium.Marker(
                points_latlon[first_idx],
                icon=BeautifyIcon(
                    icon="route",
                    icon_shape="marker",
                    border_color=color,
                    text_color=color,
                    number=r_id,
                ),
                tooltip=f"Route #{r_id} • ~{total_dist_km:.2f} km",
                popup=f"<b>Route #{r_id}</b><br/>Tổng chiều dài ~{total_dist_km:.2f} km",
            ).add_to(fg)

        fg.add_to(m)

    # — Draw step-by-step layers —
    step_vars, step_labels = [], []
    for s_id, s in enumerate(getattr(vrp, "steps", []), start=1):
        veh = s.get("vehicle", 0)
        color = _veh_color(veh)
        from_idx, to_idx = s["from"], s["to"]

        fg = folium.FeatureGroup(
            name=f"Step {s_id}: v{veh} • {from_idx}→{to_idx}",
            show=(s_id == 1),  # bật sẵn Step 1
        )

        u, v = node_ids[from_idx], node_ids[to_idx]
        name_u, name_v = names[u], names[v]
        key_name = f"{u}:{v}"
        key_loc = f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}"
        geom, data_map = cache_location.get(
            key_name,
        )
        if geom is None:
            print(f"Không lấy được step {name_u} -> {name_v}")
            continue

        line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
        all_poly_bounds.extend(line_coords)

        dist_m = data_map["routes"][0].get("distance", 0.0)
        dur_s = data_map["routes"][0].get("duration", 0.0)

        AntPath(
            locations=line_coords,
            tooltip=f"Step {s_id} • v{veh} • {name_u} → {name_v} • {dist_m/1000:.2f} km • {dur_s/60:.1f} min",
            delay=400,
            dash_array=[1, 8],
            weight=6,
            opacity=0.95,
            color=color,
        ).add_to(fg)

        folium.Marker(
            points_latlon[u],
            tooltip=f"from #{from_idx}: {name_u}",
            icon=BeautifyIcon(
                icon="play",
                number=s_id,
                border_color=color,
                text_color=color,
                background_color="white",
            ),
        ).add_to(fg)
        folium.Marker(
            points_latlon[v],
            tooltip=f"to #{to_idx}: {name_v}",
            icon=BeautifyIcon(
                icon="flag",
                border_color=color,
                text_color=color,
                background_color="white",
            ),
        ).add_to(fg)

        folium.Popup(
            html=(
                f"<b>Step {s_id}</b><br/>Vehicle: v{veh}<br/>{name_u} → {name_v}"
                f"<br/>{dist_m/1000:.2f} km • {dur_s/60:.1f} min"
            ),
            max_width=300,
        ).add_to(fg)

        fg.add_to(m)
        # thu thập tên biến JS và nhãn
        step_vars.append(fg.get_name())
        step_labels.append(f"Step {s_id}: v{veh} • {from_idx}→{to_idx}")


    # — Fit bounds —
    if all_poly_bounds:
        lats = [p[0] for p in all_poly_bounds] + [lat for lat, _ in points_latlon]
        lons = [p[1] for p in all_poly_bounds] + [lon for _, lon in points_latlon]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    # — Layer control sang góc trái-trên để tránh chồng Step Controller —
    folium.LayerControl(collapsed=False, position="topleft").add_to(m)

    # — Step Controller (không cần tick checkbox) —
    if step_vars:
        _add_step_controller(
            m,
            step_vars,
            step_labels,
            play_interval_ms=play_interval_ms,
            cumulative=cumulative,
        )

    m.save(out_html)
    return out_html


def make_stepwise_map_vrps(
    names: List[str],
    points_latlon: List[Tuple[float, float]],
    node_ids: List[int],
    vrps: List[VRPResult],
    cache_location: dict = None,
    out_html: str = "vrp_stepwise_map.html",
    description_html: str = None,
    throttle_s: float = 0.1,
    cumulative: bool = False,
    play_interval_ms: int = 900,
) -> str:
    """
    - Chỉ vẽ routes hoàn chỉnh cho vrps[-1]
    - Các vrp[:-1] vẽ như Step trong Step Controller
      (mỗi route trong step đó có màu khác nhau)
    """
    # Base map
    center = np.mean(np.array(points_latlon), axis=0).tolist()
    m = folium.Map(
        location=center,
        zoom_start=12,
        control_scale=True,
        prefer_canvas=True,
        tiles="CartoDB positron",
    )

    # Plugins
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    Fullscreen().add_to(m)
    MeasureControl(
        primary_length_unit="meters", secondary_length_unit="kilometers"
    ).add_to(m)
    MousePosition(position="bottomleft", separator=" | ", prefix="Lat/Lon").add_to(m)

    # Description
    if description_html is None:
        description_html = (
            f"<b>Tổng quan:</b> {len(vrps)} nghiệm pháp, "
            f"{len(vrps[-1].routes)} routes trong nghiệm pháp cuối.<br>"
            f"<span style='opacity:0.7'>Step Controller: duyệt qua từng VRP trước đó.</span>"
        )
    m.get_root().add_child(
        _html_overlay_box_bottom_right("VRP – Multi Result Viewer", description_html)
    )

    # Depot + customers
    folium.Marker(
        points_latlon[0], tooltip="Depot", icon=folium.Icon(color="green", icon="home")
    ).add_to(m)
    cluster = MarkerCluster(name="Customers").add_to(m)
    for idx, (lat, lon) in enumerate(points_latlon[1:], start=1):
        folium.CircleMarker(
            (lat, lon),
            radius=5,
            fill=True,
            weight=1,
            fill_opacity=0.9,
            tooltip=f"Customer #{idx}: {names[idx]}",
        ).add_to(cluster)

    all_poly_bounds = []

    # ----------- Vẽ routes cho nghiệm pháp cuối cùng ------------
    # for r_id, route in enumerate(vrps[-1].routes):
    #     color = _veh_color(r_id)
    #     fg = folium.FeatureGroup(name=f"Route #{r_id}", show=True)
    #     for a, b in zip(route[:-1], route[1:]):
    #         u, v = node_ids[a], node_ids[b]
    #         name_u, name_v = names[u], names[v]
    #         key_name = f"{u}:{v}"
    #         key_loc = f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}"
    #         geom, _ = cache_location.get(
    #             key_name,
    #         )
    #         if not geom:
    #             continue
    #         line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
    #         all_poly_bounds.extend(line_coords)
    #         AntPath(
    #             line_coords,
    #             color=color,
    #             weight=4,
    #             opacity=0.9,
    #             delay=600,
    #             dash_array=[10, 20],
    #             tooltip=f"Final Route {r_id}: {name_u}→{name_v}",
    #         ).add_to(fg)
    #     fg.add_to(m)

    # ----------- Vẽ các VRP trước đó như Step -----------------
    step_vars, step_labels = [], []
    for step_idx, vrp in enumerate(vrps, start=1):
        fg = folium.FeatureGroup(
            name=f"Step {step_idx}: VRP with {len(vrp.routes)} routes",
            show=(step_idx == 1),
        )
        # mỗi route có màu riêng
        for r_id, route in enumerate(vrp.routes):
            color = _veh_color(r_id)
            for a, b in zip(route[:-1], route[1:]):
                u, v = node_ids[a], node_ids[b]
                name_u, name_v = names[u], names[v]
                key_name = f"{u}:{v}"
                key_loc = f"{points_latlon[u][1]},{points_latlon[u][0]};{points_latlon[v][1]},{points_latlon[v][0]}"
                geom, _ = cache_location.get(
                    key_name,
                )
                if not geom:
                    continue
                line_coords = [[xy[1], xy[0]] for xy in geom["coordinates"]]
                all_poly_bounds.extend(line_coords)
                AntPath(
                    line_coords,
                    color=color,
                    weight=4,
                    opacity=0.7,
                    delay=600,
                    tooltip=f"Step {step_idx} • Route {r_id}: {name_u}→{name_v}",
                ).add_to(fg)
        # add một marker để dễ nhận biết step
        folium.Marker(
            points_latlon[0],
            tooltip=f"VRP Step {step_idx}",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(fg)

        fg.add_to(m)
        step_vars.append(fg.get_name())
        step_labels.append(f"VRP Step {step_idx}: {len(vrp.routes)} routes")

    # Fit bounds
    if all_poly_bounds:
        lats = [p[0] for p in all_poly_bounds] + [lat for lat, _ in points_latlon]
        lons = [p[1] for p in all_poly_bounds] + [lon for _, lon in points_latlon]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    folium.LayerControl(collapsed=False, position="topleft").add_to(m)

    if step_vars:
        _add_step_controller(
            m,
            step_vars,
            step_labels,
            play_interval_ms=play_interval_ms,
            cumulative=cumulative,
        )

    m.save(out_html)
    return out_html
