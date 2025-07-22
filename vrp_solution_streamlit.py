import time

import vrplib
import numpy as np
import streamlit as st

from vrp_viz.utils import calculate_total_distance
from vrp_viz.utils import visualize_step_streamlit as visualize_step
from vrp_viz.nearest_neighbor.nn_generator import nearest_neighbor_generator
from vrp_viz.cheapest_insertion.ci_generator import cheapest_insertion_generator
from vrp_viz.clark_saving.cs_generator import clarke_wright_refined_generator

st.set_page_config(layout="wide", page_title="VRP Algorithm Visualizer")
st.title("Trình trực quan hóa thuật toán VRP từng bước")
st.write(
    "Ứng dụng này cho phép bạn xem cách các thuật toán heuristic phổ biến xây dựng giải pháp cho Bài toán Định tuyến Xe (VRP) từng bước một."
)

if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.algorithm_generator = None
    st.session_state.log_messages = []
    st.session_state.final_routes = None
    st.session_state.instance_data = None
    st.session_state.animating = False


@st.cache_data
def load_instance_data(instance_name):
    try:
        instance = vrplib.read_instance(instance_name)
        locations = [list(coords) for coords in instance["node_coord"].tolist()]
        demands = [d for d in instance["demand"].tolist()]
        capacity = instance["capacity"]
        dist_matrix = instance["edge_weight"]
        solution = instance.get("solution", {}).get("cost", "N/A")
        return {
            "locations": locations,
            "demands": demands,
            "capacity": capacity,
            "dist_matrix": dist_matrix,
            "solution": solution,
        }
    except Exception as e:
        st.error(
            f"Không thể tải dữ liệu '{instance_name}'. Vui lòng kiểm tra lại tên hoặc kết nối mạng. Lỗi: {e}"
        )
        return None


with st.sidebar:
    st.header("Bảng điều khiển")
    instance_name = st.selectbox(
        "Chọn bộ dữ liệu từ VRPLIB",
        ("P-n16-k8.vrp", "A-n32-k5.vrp", "E-n22-k4.vrp", "X-n101-k25.vrp (chậm)"),
    )
    algorithm_choice = st.selectbox(
        "Chọn thuật toán",
        ("Nearest Neighbor", "Cheapest Insertion", "Clarke-Wright Savings"),
    )

    st.header("Điều khiển")
    col1, col2 = st.columns(2)
    start_button = col1.button("Bắt đầu / Đặt lại", use_container_width=True)
    next_step_button = col2.button("Bước tiếp theo", use_container_width=True)

    st.header("Animation")
    BASE_DELAY = 0.8
    speed_options = {
        "Bình thường": 2,
        "Nhanh": 5,
        "Rất Nhanh": 15,
        "Siêu Nhanh": 50,
        "Tên Lửa": 200,
        "Tức thì": 1000,
    }
    selected_speed_label = st.selectbox(
        "Chọn tốc độ Animation", options=list(speed_options.keys()), index=1
    )
    speed_multiplier = speed_options[selected_speed_label]
    actual_delay = BASE_DELAY / speed_multiplier
    animate_button = st.button("Chạy / Dừng Animation", use_container_width=True)

if start_button:
    st.session_state.step = 0
    st.session_state.algorithm_generator = None
    st.session_state.log_messages = []
    st.session_state.final_routes = None
    st.session_state.animating = False
    st.session_state.current_step_data = None


if animate_button:
    st.session_state.animating = not st.session_state.animating

if next_step_button:
    st.session_state.animating = False

if instance_name:
    st.session_state.instance_data = load_instance_data(instance_name)

if (
    st.session_state.instance_data
    and not st.session_state.algorithm_generator
    and st.session_state.final_routes is None
):
    data = st.session_state.instance_data
    generators = {
        "Nearest Neighbor": nearest_neighbor_generator,
        "Cheapest Insertion": cheapest_insertion_generator,
        "Clarke-Wright Savings": clarke_wright_refined_generator,
    }
    st.session_state.algorithm_generator = generators[algorithm_choice](
        data["dist_matrix"], data["demands"], data["capacity"]
    )
    try:
        initial_state = next(st.session_state.algorithm_generator)
        st.session_state.current_step_data = initial_state
        st.session_state.log_messages.append(f"0. {initial_state['message']}")
    except StopIteration:
        st.warning("Thuật toán kết thúc ngay lập tức.")


def advance_step():
    if st.session_state.algorithm_generator:
        try:
            st.session_state.step += 1
            next_state = next(st.session_state.algorithm_generator)
            st.session_state.current_step_data = next_state
            st.session_state.log_messages.append(
                f"{st.session_state.step}. {next_state['message']}"
            )
        except StopIteration:
            st.success("Thuật toán đã hoàn thành!")
            st.session_state.final_routes = st.session_state.current_step_data["routes"]
            st.session_state.algorithm_generator = None
            st.session_state.animating = False


if next_step_button:
    advance_step()

if st.session_state.instance_data:
    data = st.session_state.instance_data
    col1, col2 = st.columns([2, 1])

    with col1:
        plot_placeholder = st.empty()
        with plot_placeholder.container():
            if (
                "current_step_data" in st.session_state
                and st.session_state.current_step_data
            ):
                step_data = st.session_state.current_step_data
                fig = visualize_step(
                    data["locations"],
                    step_data["routes"],
                    f"{algorithm_choice} - Bước {st.session_state.step}",
                    step_data.get("total_distance", 0),
                    special_colors=step_data.get("special_colors"),
                    highlighted_edges=step_data.get("highlighted_edges"),
                )
                st.pyplot(fig)
            else:
                fig = visualize_step(
                    data["locations"], [], f"Sẵn sàng chạy {algorithm_choice}", 0
                )
                st.pyplot(fig)

        st.subheader("Thông tin và dữ liệu bài toán")
        with st.expander("Nhấn để xem chi tiết dữ liệu"):
            st.dataframe(data["demands"])
            st.dataframe(data["locations"])
            st.dataframe(np.array(data["dist_matrix"])[:10, :10].round(2))

    with col2:
        st.subheader("Nhật ký các bước")
        log_container = st.container(height=500)
        with log_container:
            for msg in reversed(st.session_state.log_messages):
                st.text(msg)

        if st.session_state.final_routes:
            st.subheader("Kết quả cuối cùng")
            total_dist = calculate_total_distance(
                st.session_state.final_routes, data["dist_matrix"]
            )
            st.metric(
                "Tổng quãng đường",
                f"{total_dist:.2f}",
                f"So với BKS: {data['solution']}",
            )

else:
    st.info("Vui lòng chọn bộ dữ liệu và nhấn 'Bắt đầu / Đặt lại'.")

if st.session_state.get("animating", False):
    time.sleep(actual_delay)
    advance_step()
    st.rerun()
