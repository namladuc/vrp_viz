import os
from typing import List, Literal, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

from vrp_viz.map_viz.stepwise_map import VRPResult
from vrp_viz.dataloader import get_run_data_from_prefix_path
from vrp_viz.dataloader import get_run_data_from_local_search
from vrp_viz.nearest_neighbor.viz_nearnest_neighbor import nearest_neighbor_v2
from vrp_viz.clark_saving.viz_clarke_saving import clarke_wright_savings_vrp

from vrp_viz.local_search.shift import shift_local_search
from vrp_viz.local_search.swap import swap_local_search
from vrp_viz.local_search.two_opt_star import two_opt_star_local_search

app = FastAPI(title="VRP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # cho phép tất cả domain (có thể đổi thành ["http://localhost:3000"] nếu chỉ gọi từ 1 web)
    allow_credentials=True,
    allow_methods=["*"],  # cho phép tất cả method (GET, POST, OPTIONS…)
    allow_headers=["*"],  # cho phép tất cả headers
)


# =====================
# Pydantic Schemas
# =====================

Algorithm = Literal["nn", "clarke", "savings"]
DatasetType = Literal["random", "explicit"]


class Coord(BaseModel):
    x: float = Field(..., description="Tọa độ X")
    y: float = Field(..., description="Tọa độ Y")


class RandomDataset(BaseModel):
    type: Literal["random"]
    n_customers: int = Field(..., gt=0, description="Số khách hàng > 0")
    depot_position: int = Field(
        ..., ge=1, le=4, description="Vị trí kho trong 4 góc (1..4)"
    )
    seed: Optional[int] = Field(None, description="Random seed (tùy chọn)")


class ExplicitDataset(BaseModel):
    type: Literal["explicit"]
    name: Literal["data1", "data2", "data3"] = Field(..., description="Tên dataset")


class SolveRequest(BaseModel):
    algorithm: Algorithm
    dataset: RandomDataset | ExplicitDataset


class SolveResponse(BaseModel):
    received: SolveRequest
    time_ms: Optional[float] = None
    total_distance: float
    solution: List[List[int]]
    html_res: Optional[str] = None

class LocalSearchRequest(BaseModel):
    base_solution: SolveResponse
    improvement_type: Literal["2-opt", "shift", "swap"]

# =====================
# Validators
# =====================


@field_validator("dataset")
def validate_dataset(cls, v):
    # Pydantic v2: ta không cần nhiều ở đây; giữ chỗ cho mở rộng
    return v


# =====================
# API Endpoints
# =====================


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    print("Received request:", req.dataset)
    if req.dataset.type == "random":
        raise HTTPException(
            status_code=400, detail="Random dataset generation not implemented yet."
        )
    else:
        ds: ExplicitDataset = req.dataset

    if req.algorithm not in ["nn", "clarke", "savings"]:
        raise HTTPException(
            status_code=400, detail="Hiện chỉ hỗ trợ 'nn', 'clarke', 'savings'."
        )

    prefix_path = os.path.join("data", f"{ds.name}")
    if req.algorithm == "nn":
        solver_name = "nearest_neighbor"
        function_solver = nearest_neighbor_v2
    elif req.algorithm == "clarke":
        solver_name = "clarke_wright"
        function_solver = clarke_wright_savings_vrp

    dict_vrp, solution_name = get_run_data_from_prefix_path(
        prefix_path, function_solver, solver_name
    )

    total_distance = np.sum(dict_vrp["route_lengths"])

    return SolveResponse(
        received=req,
        total_distance=total_distance,
        time_ms=dict_vrp.get("duration_seconds", 0) * 1000,
        solution=dict_vrp.get("routes", []),
        html_res=solution_name,
    )


@app.post("/local-search", response_model=SolveResponse)
def local_search(req: LocalSearchRequest):
    print("Received local search request:", req)

    # take data info
    base_req = req.base_solution
    if base_req.received.dataset.type == "random":
        raise HTTPException(
            status_code=400, detail="Random dataset generation not implemented yet."
        )
    elif base_req.received.dataset.type == "explicit":
        ds: ExplicitDataset = base_req.received.dataset

    if req.improvement_type not in ["2-opt", "shift", "swap"]:
        raise HTTPException(
            status_code=400, detail="Hiện chỉ hỗ trợ '2-opt', 'shift', 'swap'."
        )

    prefix_path = os.path.join("data", f"{ds.name}")
    if req.improvement_type == "2-opt":
        solver_name = "2-opt"
        function_solver = two_opt_star_local_search
    elif req.improvement_type == "shift":
        solver_name = "shift"
        function_solver = shift_local_search
    elif req.improvement_type == "swap":
        solver_name = "swap"
        function_solver = swap_local_search

    dict_vrp, solution_name = get_run_data_from_local_search(
        prefix_path,
        function_solver,
        solver_name,
        base_solution=base_req.solution
    )

    total_distance = np.sum(dict_vrp[-1]["route_lengths"])

    # Implement local search logic here
    return SolveResponse(
        received=req.base_solution.received,
        total_distance=total_distance,
        time_ms=dict_vrp[-1].get("duration_seconds", 0) * 1000,
        solution=dict_vrp[-1].get("routes", []),
        html_res=solution_name,
    )
