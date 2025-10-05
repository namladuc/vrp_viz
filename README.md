# VRP Algorithm Visualizer

## Quick Start

### 1. Start the Server
```bash
uvicorn server_vrp:app 
```

### 2. Open the Application
Open the file `vrp_home.html` in your web browser to access the VRP visualization dashboard.

## What it does
This application provides an interactive web interface for solving and visualizing Vehicle Routing Problems (VRP) with various heuristic algorithms including:
- Nearest Neighbor
- Clarke-Wright Savings  
- Cheapest Insertion
- Local Search optimization (2-opt, shift, swap)

The dashboard allows you to configure parameters, run algorithms, and view results on an interactive map.