import os
import json

import pandas as pd
import numpy as np

from .map_viz.stepwise_map import VRPResult
from .map_viz.stepwise_mapv2 import make_stepwise_map as make_stepwise_map_v3


list_warehouses_infos = [
    {
        "name": "Điểm dịch vụ SPX Hà Nội - Đống Đa 5",
        "address": "530 Láng, P. Láng Hạ",
        "lat": 21.011257,
        "lng": 105.810770,
        "ward": "Phường Đống Đa",
        "district": "Quận Đống Đa",
        "post_office": "Bưu cục Shopee",
    },
    {
        "name": "Điểm dịch vụ SPX Hà Nội - Đống Đa 4",
        "address": "Số 325 phố Tây Sơn, phường Ngã Tư Sở, quận Đống Đa, Hà Nội",
        "lat": 21.0037924,
        "lng": 105.8205416,
        "ward": "Phường Ngã Tư Sở",
        "district": "Quận Đống Đa",
        "post_office": "Bưu cục Shopee",
    },
    {
        "name": "Điểm dịch vụ SPX Hà Nội - Thanh Xuân 5",
        "address": "15 Tố Hữu, Phường Nhân Chính, Quận Thanh Xuân, Hà Nội",
        "lat": 20.9981336,
        "lng": 105.7951245,
        "ward": "Phường Nhân Chính",
        "district": "Quận Thanh Xuân",
        "post_office": "Bưu cục Shopee",
    },
    {
        "name": "Điểm dịch vụ SPX Hà Nội - Từ Liêm 3",
        "address": "Số 8 đường Phạm Hùng, phường Mễ Trì, Quận Nam Từ Liêm, Hà Nội",
        "lat": 21.0097935,
        "lng": 105.7890715,
        "ward": "Phường Mễ Trì",
        "district": "Quận Nam Từ Liêm",
        "post_office": "Bưu cục Shopee",
    },
    {
        "name": "Điểm dịch vụ SPX Hà Nội - Đống Đa 9",
        "address": "Số 42 ngõ 168 Hào Nam, phường Ô Chợ Dừa, quận Đống Đa, Hà Nội",
        "lat": 21.0257701,
        "lng": 105.8287657,
        "ward": "Phường Ô Chợ Dừa",
        "district": "Quận Đống Đa",
        "post_office": "Bưu cục Shopee",
    },
]


def have_run_check_solution(prefix_path: str, solver_name: str) -> bool:
    if not os.path.exists(
        os.path.join(prefix_path, f"vrp_solution_{solver_name}.html")
    ):
        return False
    return True


def get_run_data_from_prefix_path(
    prefix_path: str, function_solver, solver_name: str
):
    if have_run_check_solution(prefix_path, solver_name):
        # read html file and return byte to write to response
        all_byte_html = open(
            os.path.join(prefix_path, f"vrp_solution_{solver_name}.html"),
            "r",
            encoding="utf-8",
        ).read()
        dict_vrp = json.load(
            open(
                os.path.join(prefix_path, f"vrp_solution_{solver_name}.json"),
                "r",
                encoding="utf-8",
            )
        )
        return dict_vrp, all_byte_html
    customers_df = pd.read_csv(os.path.join(prefix_path, "vrp_customers_dev.csv"))
    distance_matrix_df = pd.read_csv(os.path.join(prefix_path, "vrp_distances_dev.csv"))

    warehouse_info = list_warehouses_infos[0]  # chọn kho mặc định
    N_VEHICLES = 9999
    D = distance_matrix_df.to_numpy()[:, 1:]
    D = np.array(D, dtype=float)
    list_customer = distance_matrix_df.columns.tolist()[2:]
    demands = [
        0,
        *[
            int(
                customers_df.loc[customers_df["customer_id"] == cid, "packages"].values[
                    0
                ]
            )
            for cid in list_customer
        ],
    ]
    points = [
        (float(warehouse_info["lat"]), float(warehouse_info["lng"])),
        *[
            (
                float(
                    customers_df.loc[customers_df["customer_id"] == cid, "lat"].values[
                        0
                    ]
                ),
                float(
                    customers_df.loc[customers_df["customer_id"] == cid, "lng"].values[
                        0
                    ]
                ),
            )
            for cid in list_customer
        ],
    ]
    names = [
        warehouse_info["name"],
        *[
            customers_df.loc[customers_df["customer_id"] == cid, "name"].values[0]
            for cid in list_customer
        ],
    ]
    node_ids = list(range(len(points)))

    vehicle_capacity = 5
    max_stops_per_route = None
    depot_idx = 0  # kho là node 0

    vrp: VRPResult = function_solver(
        distance_matrix=D,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=N_VEHICLES,
        depot=depot_idx,
        max_stops_per_route=max_stops_per_route,
    )

    # save sol to json
    with open(
        os.path.join(prefix_path, f"vrp_solution_{solver_name}.json"),
        "w",
        encoding="utf-8",
    ) as f:
        dict_vrp = {
            "routes": vrp.routes,
            "route_lengths": vrp.route_lengths,
            "steps": vrp.steps,
        }
        json.dump(dict_vrp, f, ensure_ascii=False, indent=4)

    out = make_stepwise_map_v3(
        names,
        points,
        node_ids,
        vrp,
        out_html=os.path.join(prefix_path, f"vrp_solution_{solver_name}.html"),
    )

    return dict_vrp, out
