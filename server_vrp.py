from typing import List, Literal, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

from vrp_viz.map_viz.stepwise_map import VRPResult
from vrp_viz.dataloader import get_run_data_from_prefix_path

app = FastAPI(title="VRP API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # cho phép tất cả domain (có thể đổi thành ["http://localhost:3000"] nếu chỉ gọi từ 1 web)
    allow_credentials=True,
    allow_methods=["*"],        # cho phép tất cả method (GET, POST, OPTIONS…)
    allow_headers=["*"],        # cho phép tất cả headers
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
    depot_position: int = Field(..., ge=1, le=4, description="Vị trí kho trong 4 góc (1..4)")
    seed: Optional[int] = Field(None, description="Random seed (tùy chọn)")

class ExplicitDataset(BaseModel):
    type: Literal["explicit"]
    name: Literal["data1", "data2", "data3"] = Field(..., description="Tên dataset")

class SolveRequest(BaseModel):
    algorithm: Algorithm
    dataset: RandomDataset | ExplicitDataset

class SolveResponse(BaseModel):
    received: SolveRequest
    depot: int
    time_ms: Optional[float] = None
    total_distance: float
    solution: List[List[int]]  

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
        print("Generating random dataset...")
        # currently not supported
        raise HTTPException(status_code=400, detail="Random dataset generation not implemented yet.")
    else:
        print("Using explicit dataset...")
        ## print(current location file)
        print("Current location file:", __file__)
        ds: ExplicitDataset = req.dataset

    if req.algorithm not in ["nn", "clarke", "savings"]:
        raise HTTPException(status_code=400, detail="Hiện chỉ hỗ trợ 'nn', 'clarke', 'savings'.")

    

    return SolveResponse(
        received=req,
        depot=2,
        total_distance=123.45,
        time_ms=150.0,
        solution=[[0, 2, 1, 3], [0, 1, 2, 3]],  # ví dụ:
    )
