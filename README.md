# VRP Algorithm Visualizer Documentation

## Overview
This project provides a set of tools and algorithms to solve and visualize the Vehicle Routing Problem (VRP). It includes implementations of heuristic algorithms such as Nearest Neighbor, Cheapest Insertion, and Clarke-Wright Savings. The project supports step-by-step visualization of these algorithms using Streamlit and can generate animations in GIF format for better understanding.

## Dev

```
uvicorn server_vrp:app --reload
```

Local search: 
- data hiện tại
- lời giải hiện tại


D: np.ndarray,
demands: Optional[List[float]] = None,
vehicle_capacity: Optional[float] = None,
max_stops_per_route: Optional[int] = None,
num_vehicles: int = 1,
depot_idx: int = 0, cố định
current_solution: VRPResult

trả ra -> List[VRPResult]

10 - 20 - 50 -70

---

## Project Structure
### 1. **`vrp_viz`**
    - Contains the core logic for VRP algorithms and visualization utilities.

#### Submodules:
- **`nearest_neighbor`**:
  - Implements the Nearest Neighbor heuristic.
  - Files:
     - `nn_generator.py`: Step-by-step generator for visualization.
     - `nn_gif.py`: Generates frames for GIF animations.
     - `nearnest_neighbor.py`: Core implementation of the Nearest Neighbor algorithm.

- **`cheapest_insertion`**:
  - Implements the Cheapest Insertion heuristic.
  - Files:
     - `ci_generator.py`: Step-by-step generator for visualization.
     - `ci_gif.py`: Generates frames for GIF animations.
     - `cheapest_insertion.py`: Core implementation of the Cheapest Insertion algorithm.

- **`clark_saving`**:
  - Implements the Clarke-Wright Savings heuristic.
  - Files:
     - `cs_generator.py`: Step-by-step generator for visualization.
     - `cs_gif.py`: Generates frames for GIF animations.
     - `clarke_saving.py`: Core implementation of the Clarke-Wright Savings algorithm.

- **`utils.py`**:
  - Utility functions for distance calculations, route visualization, and Streamlit integration.

- **`gif_utils.py`**:
  - Functions for creating GIF animations from algorithm frames.

---

### 2. **`data`**
    - Contains sample VRP instances and their optimal solutions.
    - Files:
      - `P-n16-k8.vrp`: A small VRP instance with 16 nodes.
      - `A-n32-k5.vrp`: A medium VRP instance with 32 nodes.
      - `P-n16-k8.sol`: Optimal solution for `P-n16-k8.vrp`.
      - `A-n32-k5.sol`: Optimal solution for `A-n32-k5.vrp`.

---

### 3. **`vrp_solution_streamlit.py`**
    - A Streamlit-based application for step-by-step visualization of VRP algorithms.
    - Features:
      - Select VRP instance and algorithm.
      - Step through the algorithm's execution.
      - View intermediate and final results.

---

### 4. **`vrp_solution_to_gif.py`**
    - Generates GIF animations for VRP algorithms.
    - Features:
      - Runs all algorithms on a selected VRP instance.
      - Creates GIFs for each algorithm's execution.

---

### 5. **`vrp_cli.py`**
    - A command-line interface for running VRP algorithms.
    - Features:
      - Executes all algorithms on a selected VRP instance.
      - Prints results and execution time.
      - Optionally visualizes routes using Matplotlib.

---

## Algorithms
### 1. **Nearest Neighbor**
    - Starts from the depot and iteratively adds the nearest unvisited customer to the current route until capacity is reached.

### 2. **Cheapest Insertion**
    - Starts with a single customer and iteratively inserts the cheapest unvisited customer into the existing routes.

### 3. **Clarke-Wright Savings**
    - Merges routes based on the savings in distance achieved by combining two routes.

---

## Key Functions
### `calculate_total_distance(routes, dist_matrix)`
    - Computes the total distance of all routes.

### `visualize_routes(routes, locations, title)`
    - Visualizes the routes using Matplotlib.

### `save_gif_frame(frame_path, title, locations, routes, ...)`
    - Saves a single frame for GIF animation.

### `create_gif(frames_dir, gif_path, duration)`
    - Creates a GIF from saved frames.

---

## Usage
### Streamlit Application
1. Run `vrp_solution_streamlit.py`.
2. Select a VRP instance and algorithm.
3. Step through the algorithm or run animations.

### Generate GIFs
1. Run `vrp_solution_to_gif.py`.
2. GIFs will be saved in the `gif/` directory.

### Command-Line Interface
1. Run `vrp_cli.py`.
2. View results and optionally visualize routes.

---

## Dependencies
- Python 3.7+
- Required Libraries:
  - `numpy`
  - `matplotlib`
  - `streamlit`
  - `imageio`
  - `vrplib`

---

## Notes
- Ensure VRP instance files are in the `data/` directory.
- GIF generation may take time for large instances.
- Streamlit app provides an interactive way to understand algorithm behavior.