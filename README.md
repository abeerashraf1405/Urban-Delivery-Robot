# 🤖 Intelligent Urban Delivery Robot

A visual AI pathfinding simulator built with Python and Tkinter. A robot navigates a procedurally generated city grid to complete deliveries using five classic search algorithms, with real-time animation, cost tracking, and performance metrics.

---

## 📸 Preview

The application renders a **15×15 city grid** with:
- 🏠 A base station where the robot starts
- 📦 Delivery targets scattered across the map
- 🏢 Buildings that act as obstacles
- 🟠 Traffic zones with high traversal cost
- 🤖 An animated robot that moves step-by-step along the computed path

---

## ✨ Features

- **5 Search Algorithms** selectable at runtime:
  - Breadth-First Search (BFS)
  - Depth-First Search (DFS)
  - Uniform Cost Search (UCS)
  - Greedy Best-First Search
  - A\* Search *(recommended)*
- **Animated visualization** of the robot moving along the planned path
- **Live status panel** showing current delivery, path length, cost, nodes explored, and time
- **Performance metrics table** updated after each delivery
- **End-of-run summary** with aggregate cost, nodes, and time per algorithm
- **Console benchmark mode** to compare all algorithms without the GUI
- **Reset** button to regenerate the map and run again

---

## 🗂️ Project Structure

```
urban-delivery-robot/
│
├── Module1.py        # Main application (all logic + GUI in one file)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.8+**
- Tkinter (included with most Python installations)

To verify Tkinter is available:
```bash
python -m tkinter
```

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/urban-delivery-robot.git
cd urban-delivery-robot
```

No external dependencies, only the Python standard library is used.

### Run the GUI

```bash
python Module1.py
```

### Run the Console Benchmark

Compare all 5 algorithms side-by-side without opening the GUI:

```bash
python Module1.py --console
```

Sample output:
```
=================================================================
   URBAN DELIVERY ROBOT – Console Benchmark
=================================================================

── Delivery 1: (1, 1) → (7, 9) ──
  Algo        Cost    Nodes   Time(ms)  Found
  ---------------------------------------------
  BFS          42       130      0.85    Yes
  DFS         117       212      1.10    Yes
  UCS          38       145      1.22    Yes
  Greedy       45        88      0.61    Yes
  A*           38        92      0.74    Yes
```

---

## 🧠 Algorithms

| Algorithm | Optimal? | Complete? | Heuristic | Best For |
|-----------|----------|-----------|-----------|----------|
| BFS | ✅ (uniform cost) | ✅ | None | Unweighted grids |
| DFS | ❌ | ❌ | None | Memory-limited search |
| UCS | ✅ | ✅ | None | Weighted grids |
| Greedy | ❌ | ✅ | Combined (Manhattan + Euclidean) | Speed |
| A\* | ✅ | ✅ | Combined (Manhattan + Euclidean) | Optimal + efficient |

### Heuristic Used (Greedy & A\*)
```python
combined(a, b) = (manhattan(a, b) + euclidean(a, b)) / 2
```

---

## 🗺️ Grid Legend

| Color | Symbol | Meaning |
|-------|--------|---------|
| 🔵 Blue | 🏠 | Base Station (start) |
| 🔴 Red | 📦 | Delivery Target |
| 🟢 Green | — | Road (traversal cost: 1–5) |
| 🟠 Orange | — | Traffic Zone (traversal cost: 10–20) |
| ⚫ Dark | 🏢 | Building (impassable) |
| 🟡 Gold | — | Planned Path |
| 🩵 Cyan | — | Explored Nodes |
| 🟣 Purple | 🤖 | Robot |

---

## ⚙️ Configuration

You can tweak these constants at the top of `Module1.py`:

```python
GRID_SIZE     = 15      # Grid dimensions (GRID_SIZE × GRID_SIZE)
NUM_DELIVERIES = 5      # Number of delivery targets
ANIM_DELAY    = 30      # Animation speed in milliseconds per step
```

Building density is 25% of cells; traffic zones cover 15%.

---

## 📊 How It Works

1. A random city grid is generated each run.
2. The robot starts at the **base station** `(1, 1)`.
3. For each delivery location (in order), the selected algorithm computes a path.
4. The robot animates along the path, and the delivery is marked complete.
5. After all deliveries, a summary popup shows aggregate statistics.

---

## 🤝 Contributing

Pull requests are welcome! Some ideas for extension:
- Add diagonal movement support
- Implement Bidirectional A\*
- Add a TSP optimizer to reorder deliveries for minimum total cost
- Export metrics to CSV

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

## 👤 Author

**Abeer Ashraf**
