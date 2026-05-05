"""
=============================================================
  ANT COLONY FORAGING SIMULATION
  Uses ONLY tkinter — NO installation needed!
  Just run: python ant_colony_tkinter.py
=============================================================
"""

import tkinter as tk
import math
import random

# ── Configuration ──────────────────────────────────────────
W, H        = 850, 580
NUM_ANTS    = 80
SPEED       = 2.5
WANDER      = 0.4
SENSOR_DIST = 28
SENSOR_ANG  = math.pi / 4
CELL        = 8          # pheromone grid cell size (bigger = faster)
EVAP        = 0.005      # evaporation per frame
DEPOSIT     = 15
NEST_X      = W // 2
NEST_Y      = H // 2
NEST_R      = 22
FOOD_R      = 10
PICKUP_R    = 12
DROPOFF_R   = 26
FOOD_AMT    = 60
FPS_DELAY   = 16         # milliseconds between frames (~60fps)

GW = W // CELL
GH = H // CELL

# ── Pheromone Grid ─────────────────────────────────────────
class Grid:
    def __init__(self):
        self.home = [[0.0]*GW for _ in range(GH)]
        self.food = [[0.0]*GW for _ in range(GH)]

    def get(self, grid, px, py):
        gx = int(px / CELL)
        gy = int(py / CELL)
        if 0 <= gx < GW and 0 <= gy < GH:
            return grid[gy][gx]
        return 0.0

    def deposit(self, grid, px, py, amt):
        gx = int(px / CELL)
        gy = int(py / CELL)
        if 0 <= gx < GW and 0 <= gy < GH:
            grid[gy][gx] = min(255, grid[gy][gx] + amt)

    def sense(self, grid, px, py, angle, offset):
        sx = px + math.cos(angle + offset) * SENSOR_DIST
        sy = py + math.sin(angle + offset) * SENSOR_DIST
        return self.get(grid, sx, sy)

    def evaporate(self):
        for y in range(GH):
            for x in range(GW):
                self.home[y][x] = max(0, self.home[y][x] - EVAP * self.home[y][x])
                self.food[y][x] = max(0, self.food[y][x] - EVAP * self.food[y][x])


# ── Ant Agent ──────────────────────────────────────────────
class Ant:
    def __init__(self):
        self.x     = NEST_X + random.uniform(-8, 8)
        self.y     = NEST_Y + random.uniform(-8, 8)
        self.angle = random.uniform(0, 2 * math.pi)
        self.state = 'searching'   # 'searching' or 'carrying'
        self.stuck = 0

    def update(self, grid, foods):
        # Which pheromone to follow
        follow = grid.food if self.state == 'searching' else grid.home
        lay_on = grid.home if self.state == 'searching' else grid.food

        # Sense environment
        fwd = grid.sense(follow, self.x, self.y, self.angle, 0)
        lft = grid.sense(follow, self.x, self.y, self.angle, -SENSOR_ANG)
        rgt = grid.sense(follow, self.x, self.y, self.angle,  SENSOR_ANG)

        # Decide direction
        w = WANDER * (1 + self.stuck * 0.05)
        if fwd >= lft and fwd >= rgt:
            self.angle += random.uniform(-w*0.3, w*0.3)
        elif lft > rgt:
            self.angle -= random.uniform(w*0.4, w)
        else:
            self.angle += random.uniform(w*0.4, w)

        # Lay pheromone
        grid.deposit(lay_on, self.x, self.y, DEPOSIT)

        # Move
        px, py = self.x, self.y
        self.x += math.cos(self.angle) * SPEED
        self.y += math.sin(self.angle) * SPEED

        # Bounce off walls
        if self.x < 3 or self.x > W-3:
            self.angle = math.pi - self.angle
            self.x = max(3, min(W-3, self.x))
        if self.y < 3 or self.y > H-3:
            self.angle = -self.angle
            self.y = max(3, min(H-3, self.y))

        # Stuck check
        if abs(self.x-px) < 0.1 and abs(self.y-py) < 0.1:
            self.stuck += 1
        else:
            self.stuck = max(0, self.stuck-1)
        if self.stuck > 15:
            self.angle += math.pi * random.uniform(0.5, 1.5)
            self.stuck = 0

        # Interact with food / nest
        if self.state == 'searching':
            for f in foods:
                if f['amount'] > 0:
                    dx, dy = self.x - f['x'], self.y - f['y']
                    if dx*dx + dy*dy < PICKUP_R**2:
                        f['amount'] -= 1
                        self.state = 'carrying'
                        self.angle += math.pi
                        return False
        else:
            dx, dy = self.x - NEST_X, self.y - NEST_Y
            if dx*dx + dy*dy < DROPOFF_R**2:
                self.state = 'searching'
                self.angle += math.pi
                return True   # delivered food!
        return False


# ── Simulation App ─────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root
        root.title("Ant Colony Foraging — AI Agents & Environment")
        root.configure(bg="#0b0804")
        root.resizable(False, False)

        # Canvas
        self.canvas = tk.Canvas(root, width=W, height=H,
                                bg="#0b0804", highlightthickness=0)
        self.canvas.pack()

        # Stats panel
        self.info = tk.Label(root,
            text="", font=("Courier New", 11, "bold"),
            bg="#0b0804", fg="#f5c842", justify="left", anchor="w")
        self.info.pack(fill="x", padx=12, pady=4)

        # Buttons
        btn_frame = tk.Frame(root, bg="#0b0804")
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="⏸  Pause / Resume",
            command=self.toggle_pause,
            font=("Courier New", 10, "bold"),
            bg="#1a0a00", fg="#f97316",
            activebackground="#2a1a00", activeforeground="#fb923c",
            relief="flat", padx=12, pady=4).pack(side="left", padx=6)
        tk.Button(btn_frame, text="↺  Reset",
            command=self.reset,
            font=("Courier New", 10, "bold"),
            bg="#0a0a1a", fg="#a5b4fc",
            activebackground="#1a1a2a", activeforeground="#c7d2fe",
            relief="flat", padx=12, pady=4).pack(side="left", padx=6)

        # Legend
        leg = tk.Label(root,
            text="🟠 Searching    🟢 Carrying Food    🟡 Nest    🌿 Food Source    "
                 "── Amber trail = home pheromone    ── Green trail = food pheromone",
            font=("Courier New", 9), bg="#0b0804", fg="#706050")
        leg.pack(pady=4)

        self.paused    = False
        self.collected = 0
        self.reset()

    def reset(self):
        self.grid      = Grid()
        self.ants      = [Ant() for _ in range(NUM_ANTS)]
        self.foods     = [
            {'x': 130,   'y': 100,   'amount': FOOD_AMT, 'max': FOOD_AMT},
            {'x': W-130, 'y': 100,   'amount': FOOD_AMT, 'max': FOOD_AMT},
            {'x': W-130, 'y': H-100, 'amount': FOOD_AMT, 'max': FOOD_AMT},
            {'x': 130,   'y': H-100, 'amount': FOOD_AMT, 'max': FOOD_AMT},
            {'x': W//2,  'y': 65,    'amount': FOOD_AMT, 'max': FOOD_AMT},
            {'x': W//2,  'y': H-65,  'amount': FOOD_AMT, 'max': FOOD_AMT},
        ]
        self.collected = 0
        self.paused    = False

    def toggle_pause(self):
        self.paused = not self.paused

    def draw_pheromones(self):
        c = self.canvas
        grid = self.grid
        for gy in range(GH):
            for gx in range(GW):
                h = grid.home[gy][gx]
                f = grid.food[gy][gx]
                if h < 3 and f < 3:
                    continue   # skip invisible cells for speed
                px = gx * CELL
                py = gy * CELL
                # Amber for home, green for food
                r = min(255, int(h * 0.9 + f * 0.05))
                g = min(255, int(h * 0.4 + f * 0.85))
                b = min(255, int(h * 0.05 + f * 0.9))
                alpha = min(255, int((h + f) * 1.5))
                # Blend with background (#0b0804)
                br, bg_c, bb = 11, 8, 4
                fr = br + (r - br) * alpha // 255
                fg = bg_c + (g - bg_c) * alpha // 255
                fb = bb + (b - bb) * alpha // 255
                color = f"#{fr:02x}{fg:02x}{fb:02x}"
                c.create_rectangle(px, py, px+CELL, py+CELL,
                                   fill=color, outline="")

    def draw_nest(self):
        c = self.canvas
        for r in range(NEST_R+18, 0, -5):
            alpha = int(40 * (1 - r/(NEST_R+18)))
            shade = max(0, min(255, alpha))
            col = f"#{shade+30:02x}{shade+20:02x}{0:02x}"
            c.create_oval(NEST_X-r, NEST_Y-r, NEST_X+r, NEST_Y+r,
                          fill=col, outline="")
        c.create_oval(NEST_X-NEST_R, NEST_Y-NEST_R,
                      NEST_X+NEST_R, NEST_Y+NEST_R,
                      fill="#d4a017", outline="#fef3c7", width=2)
        c.create_text(NEST_X, NEST_Y, text="⌂",
                      fill="#fef9c3", font=("Arial", 12, "bold"))

    def draw_foods(self):
        c = self.canvas
        for f in self.foods:
            if f['amount'] <= 0:
                c.create_oval(f['x']-FOOD_R, f['y']-FOOD_R,
                              f['x']+FOOD_R, f['y']+FOOD_R,
                              outline="#2d5a3d", fill="", width=1)
                continue
            ratio = f['amount'] / f['max']
            r = max(4, int(FOOD_R * (0.4 + ratio * 0.6)))
            g = int(60 + 195 * ratio)
            col = f"#3c{g:02x}64"
            c.create_oval(f['x']-r-4, f['y']-r-4,
                          f['x']+r+4, f['y']+r+4,
                          fill="#1a3a2a", outline="")
            c.create_oval(f['x']-r, f['y']-r,
                          f['x']+r, f['y']+r,
                          fill=col, outline="#bbf7d0", width=1)
            c.create_text(f['x'], f['y']-r-7,
                          text=str(f['amount']),
                          fill="#d1fae5",
                          font=("Courier New", 8, "bold"))

    def draw_ants(self):
        c = self.canvas
        for a in self.ants:
            col  = "#86efac" if a.state == 'carrying' else "#f97316"
            size = 4
            x1, y1 = a.x - size//2, a.y - size//2
            x2, y2 = a.x + size//2, a.y + size//2
            c.create_oval(x1, y1, x2, y2, fill=col, outline="")
            # Direction indicator
            ex = a.x + math.cos(a.angle) * 5
            ey = a.y + math.sin(a.angle) * 5
            c.create_line(a.x, a.y, ex, ey, fill=col, width=1)
            # Food dot
            if a.state == 'carrying':
                c.create_oval(a.x-2, a.y-2, a.x+2, a.y+2,
                              fill="#4ade80", outline="")

    def loop(self):
        if not self.paused:
            # Update environment
            self.grid.evaporate()

            # Update agents
            for ant in self.ants:
                if ant.update(self.grid, self.foods):
                    self.collected += 1

        # Draw
        c = self.canvas
        c.delete("all")

        # Background
        c.create_rectangle(0, 0, W, H, fill="#0b0804", outline="")

        self.draw_pheromones()
        self.draw_nest()
        self.draw_foods()
        self.draw_ants()

        # Paused overlay
        if self.paused:
            c.create_text(W//2, H//2,
                text="⏸  PAUSED  —  Click Pause/Resume to continue",
                fill="#fbbf24", font=("Courier New", 14, "bold"))

        # Stats
        carrying  = sum(1 for a in self.ants if a.state == 'carrying')
        searching = NUM_ANTS - carrying
        remaining = sum(f['amount'] for f in self.foods)
        self.info.config(
            text=f"  Ants: {NUM_ANTS}   |   Searching: {searching}   |   "
                 f"Carrying: {carrying}   |   Collected: {self.collected}   |   "
                 f"Food remaining: {remaining}")

        self.root.after(FPS_DELAY, self.loop)


# ── Entry Point ────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = App(root)
    root.after(100, app.loop)
    root.mainloop()