from typing import List, Literal, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

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

Algorithm = Literal["nearest_neighbor"]
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
    customers: List[Coord] = Field(..., min_items=1)

class SolveRequest(BaseModel):
    algorithm: Algorithm
    dataset: RandomDataset | ExplicitDataset

class SolveResponse(BaseModel):
    received: SolveRequest
    depot: int
    time_ms: Optional[float] = None
    total_distance: float

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
    else:
        ds: ExplicitDataset = ExplicitDataset(**req.dataset)
        depot = ds.depot
        customers = ds.customers
        if len(customers) == 0:
            raise HTTPException(status_code=400, detail="Danh sách khách hàng rỗng.")

    if req.algorithm != "nearest_neighbor":
        raise HTTPException(status_code=400, detail="Hiện chỉ hỗ trợ 'nearest_neighbor'.")

    return SolveResponse(
        received=req,
        depot=2,
        total_distance=123.45,
        route_order_indices=[0, 2, 1, 3]  # ví dụ: kho -> khách 2 -> khách 1 -> khách 3
    )
