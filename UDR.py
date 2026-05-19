import random
import time
import heapq
import math
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import threading

#  CONSTANTS
GRID_SIZE = 15
NUM_DELIVERIES = 5

EMPTY    = 0
BUILDING = 1
TRAFFIC  = 2
DELIVERY = 3
BASE     = 4
ROBOT    = 5
PATH     = 6
VISITED  = 7

COLORS = {
    EMPTY:    "#D4E8D4",
    BUILDING: "#3A3A3A",
    TRAFFIC:  "#F4A261",
    DELIVERY: "#E63946",
    BASE:     "#2196F3",
    ROBOT:    "#9C27B0",
    PATH:     "#FFD700",
    VISITED:  "#B2EBF2",
}

BG_COLOR  = "#FFFFFF"
CELL_SIZE = 42
ANIM_DELAY = 30   # ← was 80 ms; now 30 ms per step


class GridEnvironment:
    def __init__(self):
        self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.cost  = [[0]     * GRID_SIZE for _ in range(GRID_SIZE)]
        self.base  = (0, 0)
        self.delivery_locs = []
        self._build()

    def _build(self):
        self._place_base()
        self._place_buildings()
        self._place_traffic_zones()
        self._assign_road_costs()
        self._place_deliveries()

    def _place_base(self):
        self.base = (1, 1)
        self.grid[1][1] = BASE
        self.cost[1][1] = 1

    def _place_buildings(self):
        count = int(GRID_SIZE * GRID_SIZE * 0.25)
        placed = 0
        while placed < count:
            r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[r][c] == EMPTY and (r, c) != self.base:
                self.grid[r][c] = BUILDING
                placed += 1

    def _place_traffic_zones(self):
        count = int(GRID_SIZE * GRID_SIZE * 0.15)
        placed = 0
        while placed < count:
            r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[r][c] == EMPTY and (r, c) != self.base:
                self.grid[r][c] = TRAFFIC
                placed += 1

    def _assign_road_costs(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == EMPTY:
                    self.cost[r][c] = random.randint(1, 5)
                elif self.grid[r][c] == TRAFFIC:
                    self.cost[r][c] = random.randint(10, 20)
                elif self.grid[r][c] == BASE:
                    self.cost[r][c] = 1

    def _place_deliveries(self):
        self.delivery_locs = []
        candidates = [
            (r, c)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self.grid[r][c] in (EMPTY, TRAFFIC) and (r, c) != self.base
        ]
        random.shuffle(candidates)
        for pos in candidates[:NUM_DELIVERIES]:
            self.delivery_locs.append(pos)
            self.grid[pos[0]][pos[1]] = DELIVERY
            self.cost[pos[0]][pos[1]] = random.randint(1, 5)

    def passable(self, r, c):
        return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and self.grid[r][c] != BUILDING

    def neighbors(self, r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if self.passable(nr, nc):
                yield (nr, nc)

    def step_cost(self, r, c):
        return self.cost[r][c] if self.cost[r][c] > 0 else 1


def manhattan(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
def euclidean(a, b): return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
def combined(a, b):  return (manhattan(a, b) + euclidean(a, b)) / 2


class SearchResult:
    def __init__(self, path, cost, nodes_explored, elapsed):
        self.path           = path
        self.cost           = cost
        self.nodes_explored = nodes_explored
        self.elapsed        = elapsed

def _reconstruct(parent, start, goal):
    path, node = [], goal
    while node is not None:
        path.append(node); node = parent[node]
    path.reverse(); return path

def bfs(env, start, goal):
    t0 = time.perf_counter()
    frontier, parent, visited, nodes = deque([start]), {start: None}, set(), 0
    while frontier:
        cur = frontier.popleft()
        if cur == goal:
            p = _reconstruct(parent, start, goal)
            return SearchResult(p, sum(env.step_cost(*n) for n in p[1:]), nodes, time.perf_counter()-t0)
        if cur in visited: continue
        visited.add(cur); nodes += 1
        for nb in env.neighbors(*cur):
            if nb not in parent: parent[nb] = cur; frontier.append(nb)
    return SearchResult([], float('inf'), nodes, time.perf_counter()-t0)

def dfs(env, start, goal):
    t0 = time.perf_counter()
    stack, parent, visited, nodes = [start], {start: None}, set(), 0
    while stack:
        cur = stack.pop()
        if cur == goal:
            p = _reconstruct(parent, start, goal)
            return SearchResult(p, sum(env.step_cost(*n) for n in p[1:]), nodes, time.perf_counter()-t0)
        if cur in visited: continue
        visited.add(cur); nodes += 1
        for nb in env.neighbors(*cur):
            if nb not in visited:
                if nb not in parent: parent[nb] = cur
                stack.append(nb)
    return SearchResult([], float('inf'), nodes, time.perf_counter()-t0)

def ucs(env, start, goal):
    t0 = time.perf_counter()
    heap, cost_so_far, parent, nodes = [(0, start)], {start: 0}, {start: None}, 0
    while heap:
        g, cur = heapq.heappop(heap)
        if cur == goal:
            return SearchResult(_reconstruct(parent, start, goal), g, nodes, time.perf_counter()-t0)
        if g > cost_so_far.get(cur, float('inf')): continue
        nodes += 1
        for nb in env.neighbors(*cur):
            new_g = g + env.step_cost(*nb)
            if new_g < cost_so_far.get(nb, float('inf')):
                cost_so_far[nb] = new_g; parent[nb] = cur
                heapq.heappush(heap, (new_g, nb))
    return SearchResult([], float('inf'), nodes, time.perf_counter()-t0)

def greedy(env, start, goal, heuristic=combined):
    t0 = time.perf_counter()
    heap, parent, visited, nodes = [(heuristic(start,goal), start)], {start: None}, set(), 0
    while heap:
        _, cur = heapq.heappop(heap)
        if cur == goal:
            p = _reconstruct(parent, start, goal)
            return SearchResult(p, sum(env.step_cost(*n) for n in p[1:]), nodes, time.perf_counter()-t0)
        if cur in visited: continue
        visited.add(cur); nodes += 1
        for nb in env.neighbors(*cur):
            if nb not in visited:
                if nb not in parent: parent[nb] = cur
                heapq.heappush(heap, (heuristic(nb, goal), nb))
    return SearchResult([], float('inf'), nodes, time.perf_counter()-t0)

def astar(env, start, goal, heuristic=combined):
    t0 = time.perf_counter()
    heap = [(heuristic(start,goal), 0, start)]
    cost_so_far, parent, nodes = {start: 0}, {start: None}, 0
    while heap:
        f, g, cur = heapq.heappop(heap)
        if cur == goal:
            return SearchResult(_reconstruct(parent, start, goal), g, nodes, time.perf_counter()-t0)
        if g > cost_so_far.get(cur, float('inf')): continue
        nodes += 1
        for nb in env.neighbors(*cur):
            new_g = g + env.step_cost(*nb)
            if new_g < cost_so_far.get(nb, float('inf')):
                cost_so_far[nb] = new_g; parent[nb] = cur
                heapq.heappush(heap, (new_g + heuristic(nb, goal), new_g, nb))
    return SearchResult([], float('inf'), nodes, time.perf_counter()-t0)

ALGORITHMS = {"BFS": bfs, "DFS": dfs, "UCS": ucs, "Greedy": greedy, "A*": astar}


class RobotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🤖  Intelligent Urban Delivery Robot")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self.env       = GridEnvironment()
        self.robot_pos = self.env.base
        self.running   = False
        self.algo_var  = tk.StringVar(value="A*")
        self.stats_rows= []
        self.cell_types= {}
        self._cache_types()

        self.rect_ids  = {}
        self.icon_ids  = {}
        self.robot_icon = None

        self._build_ui()
        self._init_canvas()

    def _cache_types(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.cell_types[(r,c)] = self.env.grid[r][c]

    def _build_ui(self):
        top = tk.Frame(self, bg=BG_COLOR, pady=8)
        top.pack(fill="x", padx=16)

        tk.Label(top, text="🤖 Urban Delivery Robot", font=("Courier New", 16, "bold"),
                 bg=BG_COLOR, fg="#212121").pack(side="left")

        ctrl = tk.Frame(top, bg=BG_COLOR)
        ctrl.pack(side="right")

        tk.Label(ctrl, text="Algorithm:", font=("Courier New", 11),
                 bg=BG_COLOR, fg="#424242").pack(side="left", padx=4)

        ttk.Combobox(ctrl, textvariable=self.algo_var,
                     values=list(ALGORITHMS.keys()),
                     state="readonly", width=10,
                     font=("Courier New", 11)).pack(side="left", padx=4)

        self.run_btn = tk.Button(ctrl, text="▶  Run", font=("Courier New", 11, "bold"),
                                 bg="#9C27B0", fg="#FFFFFF", relief="flat",
                                 padx=12, command=self._start_simulation)
        self.run_btn.pack(side="left", padx=8)

        tk.Button(ctrl, text="↺  Reset", font=("Courier New", 11),
                  bg="#F3E5F5", fg="#424242", relief="flat",
                  padx=10, command=self._reset).pack(side="left")

        main = tk.Frame(self, bg=BG_COLOR)
        main.pack(padx=16, pady=4)

        canvas_px = GRID_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(main, width=canvas_px, height=canvas_px,
                                bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(side="left")

        side = tk.Frame(main, bg=BG_COLOR, padx=12)
        side.pack(side="left", fill="y")

        tk.Label(side, text="LEGEND", font=("Courier New", 10, "bold"),
                 bg=BG_COLOR, fg="#212121").pack(anchor="w", pady=(0,4))
        for color, label in [
            (COLORS[BASE],     "Base Station"),
            (COLORS[DELIVERY], "Delivery Target"),
            (COLORS[EMPTY],    "Road (cost 1-5)"),
            (COLORS[TRAFFIC],  "Traffic (cost 10-20)"),
            (COLORS[BUILDING], "Building (obstacle)"),
            (COLORS[PATH],     "Planned Path"),
            (COLORS[VISITED],  "Explored Nodes"),
            (COLORS[ROBOT],    "Robot"),
        ]:
            row = tk.Frame(side, bg=BG_COLOR)
            row.pack(anchor="w", pady=1)
            tk.Label(row, bg=color, width=3, relief="flat").pack(side="left", padx=(0,6))
            tk.Label(row, text=label, font=("Courier New", 9),
                     bg=BG_COLOR, fg="#424242").pack(side="left")

        tk.Label(side, text="STATUS", font=("Courier New", 10, "bold"),
                 bg=BG_COLOR, fg="#212121").pack(anchor="w", pady=(14,4))
        self.status_var = tk.StringVar(value="Ready. Press ▶ Run.")
        tk.Label(side, textvariable=self.status_var, font=("Courier New", 9),
                 bg=BG_COLOR, fg="#424242", wraplength=200, justify="left").pack(anchor="w")

        self.progress_var = tk.StringVar(value="Deliveries: 0 / 5")
        tk.Label(side, textvariable=self.progress_var, font=("Courier New", 10, "bold"),
                 bg=BG_COLOR, fg="#212121").pack(anchor="w", pady=4)

        tk.Label(side, text="METRICS", font=("Courier New", 10, "bold"),
                 bg=BG_COLOR, fg="#212121").pack(anchor="w", pady=(10,4))

        self.tbl_frame = tk.Frame(side, bg="#F3E5F5", bd=1, relief="flat")
        self.tbl_frame.pack(anchor="w", fill="x")
        for i, h in enumerate(["#", "Algo", "Cost", "Nodes", "ms"]):
            tk.Label(self.tbl_frame, text=h, font=("Courier New", 8, "bold"),
                     bg="#F3E5F5", fg="#212121", width=6).grid(row=0, column=i, padx=2)
        self.tbl_labels = []

    def _init_canvas(self):
        self.canvas.delete("all")
        self.rect_ids.clear()
        self.icon_ids.clear()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x0 = c * CELL_SIZE
                y0 = r * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                cx = (x0 + x1) // 2
                cy = (y0 + y1) // 2
                ctype = self.cell_types[(r, c)]

                rid = self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill=COLORS[ctype], outline=BG_COLOR, width=1
                )
                self.rect_ids[(r, c)] = rid

                icon = None
                if ctype == BASE:
                    icon = self.canvas.create_text(cx, cy, text="🏠", font=("Arial", 12))
                elif ctype == DELIVERY:
                    icon = self.canvas.create_text(cx, cy, text="📦", font=("Arial", 12))
                elif ctype == BUILDING:
                    icon = self.canvas.create_text(cx, cy, text="🏢", font=("Arial", 11))
                self.icon_ids[(r, c)] = icon

        r0, c0 = self.robot_pos
        rx = c0 * CELL_SIZE + CELL_SIZE // 2
        ry = r0 * CELL_SIZE + CELL_SIZE // 2
        self.robot_icon = self.canvas.create_text(rx, ry, text="🤖", font=("Arial", 14))

    def _update_canvas(self, path_set, robot_pos):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                ctype = self.cell_types[(r, c)]
                rid   = self.rect_ids[(r, c)]

                if (r, c) == robot_pos:
                    color = COLORS[ROBOT]
                elif (r, c) in path_set:
                    color = COLORS[PATH]
                else:
                    color = COLORS[ctype]

                self.canvas.itemconfig(rid, fill=color)

                iid = self.icon_ids.get((r, c))
                if iid:
                    hide = (ctype == DELIVERY and (r, c) in path_set) or (r, c) == robot_pos
                    self.canvas.itemconfig(iid, state="hidden" if hide else "normal")

        rx = robot_pos[1] * CELL_SIZE + CELL_SIZE // 2
        ry = robot_pos[0] * CELL_SIZE + CELL_SIZE // 2
        self.canvas.coords(self.robot_icon, rx, ry) # type: ignore
        self.canvas.tag_raise(self.robot_icon) # type: ignore

    def _start_simulation(self):
        if self.running: return
        self.running = True
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._simulate, daemon=True).start()

    def _simulate(self):
        algo_name = self.algo_var.get()
        algo_fn   = ALGORITHMS[algo_name]

        self.robot_pos  = self.env.base
        self.stats_rows = []
        self._clear_table()

        for i, goal in enumerate(self.env.delivery_locs):
            self.status_var.set(
                f"Delivery {i+1}/5\nFrom {self.robot_pos} → {goal}\nPlanning with {algo_name}…"
            )
            self.progress_var.set(f"Deliveries: {i} / 5")
            time.sleep(0.15)   # ← was 0.3 s

            result = algo_fn(self.env, self.robot_pos, goal)

            if not result.path:
                self.status_var.set(f"❌ No path to {goal}!\nSkipping…")
                time.sleep(0.6)  # ← was 1 s
                continue

            self.status_var.set(
                f"Delivery {i+1}/5\n"
                f"Path len: {len(result.path)}\n"
                f"Cost: {result.cost:.1f}\n"
                f"Nodes explored: {result.nodes_explored}\n"
                f"Time: {result.elapsed*1000:.1f} ms"
            )

            for step_idx, step in enumerate(result.path):
                remaining = set(result.path[step_idx + 1:])
                self._update_canvas(remaining, step)
                self.robot_pos = step
                time.sleep(ANIM_DELAY / 1000)

            self.cell_types[goal] = EMPTY
            iid = self.icon_ids.get(goal)
            if iid:
                self.canvas.itemconfig(iid, state="hidden")
            self._update_canvas(set(), self.robot_pos)

            row = (i+1, algo_name, f"{result.cost:.0f}",
                   result.nodes_explored, f"{result.elapsed*1000:.1f}")
            self.stats_rows.append(row)
            self._add_table_row(row)
            self.progress_var.set(f"Deliveries: {i+1} / 5")
            time.sleep(0.2)   # ← was 0.4 s

        self.status_var.set("✅ All deliveries complete!")
        self.progress_var.set("Deliveries: 5 / 5 ✅")
        self._show_summary()
        self.running = False
        self.run_btn.config(state="normal")

    def _clear_table(self):
        for wlist in self.tbl_labels:
            for w in wlist: w.destroy()
        self.tbl_labels = []

    def _add_table_row(self, row_data):
        ri = len(self.tbl_labels) + 1
        ws = []
        for ci, val in enumerate(row_data):
            lbl = tk.Label(self.tbl_frame, text=str(val),
                           font=("Courier New", 8),
                           bg="#9C27B0" if ri % 2 == 0 else "#F8BBD9",
                           fg="#424242", width=6)
            lbl.grid(row=ri, column=ci, padx=2, pady=1)
            ws.append(lbl)
        self.tbl_labels.append(ws)

    def _show_summary(self):
        if not self.stats_rows: return
        tc = sum(float(r[2]) for r in self.stats_rows)
        tn = sum(r[3]        for r in self.stats_rows)
        tt = sum(float(r[4]) for r in self.stats_rows)
        msg = (f"Algorithm: {self.stats_rows[0][1]}\n\n"
               f"{'Delivery':^10} {'Cost':^8} {'Nodes':^8} {'Time(ms)':^10}\n"
               f"{'-'*40}\n")
        for row in self.stats_rows:
            msg += f"  #{row[0]:<7}  {row[2]:<8} {row[3]:<8} {row[4]:<10}\n"
        msg += f"{'-'*40}\n  {'TOTAL':<8}  {tc:<8.0f} {tn:<8} {tt:<10.1f}"
        messagebox.showinfo("📊 Simulation Summary", msg)

    def _reset(self):
        if self.running: return
        self.env = GridEnvironment()
        self.robot_pos = self.env.base
        self.stats_rows = []
        self._clear_table()
        self._cache_types()
        self.status_var.set("Ready. Press ▶ Run.")
        self.progress_var.set("Deliveries: 0 / 5")
        self._init_canvas()


def run_console_benchmark():
    print("=" * 65)
    print("   URBAN DELIVERY ROBOT – Console Benchmark")
    print("=" * 65)
    env = GridEnvironment()
    print(f"\nBase station : {env.base}")
    print(f"Deliveries   : {env.delivery_locs}\n")
    summary = {name: [] for name in ALGORITHMS}
    for d_idx, goal in enumerate(env.delivery_locs):
        start = env.base if d_idx == 0 else env.delivery_locs[d_idx-1]
        print(f"── Delivery {d_idx+1}: {start} → {goal} ──")
        print(f"  {'Algo':<10} {'Cost':>8} {'Nodes':>8} {'Time(ms)':>10} {'Found':>6}")
        print(f"  {'-'*45}")
        for name, fn in ALGORITHMS.items():
            res = fn(env, start, goal)
            cost = f"{res.cost:.1f}" if res.path else "—"
            print(f"  {name:<10} {cost:>8} {res.nodes_explored:>8} "
                  f"{res.elapsed*1000:>9.2f}  {'Yes' if res.path else 'No':>6}")
            summary[name].append(res)
        print()
    print("=" * 65)
    print("  AGGREGATE TOTALS")
    print(f"  {'Algo':<10} {'TotCost':>10} {'TotNodes':>10} {'TotTime(ms)':>13}")
    print(f"  {'-'*47}")
    for name, rl in summary.items():
        print(f"  {name:<10} {sum(r.cost for r in rl if r.path):>10.1f} "
              f"{sum(r.nodes_explored for r in rl):>10} "
              f"{sum(r.elapsed for r in rl)*1000:>12.2f}")
    print("=" * 65)


if __name__ == "__main__":
    import sys
    if "--console" in sys.argv:
        run_console_benchmark()
    else:
        app = RobotApp()
        app.mainloop()