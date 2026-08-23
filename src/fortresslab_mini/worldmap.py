"""
World map for the enemy-brain planner — stage 1 of the commander pipeline.

Terrain is the impedance. Integer arithmetic only.

Cell legend (ASCII maps in tests):
  .  open ground
  #  stone wall      (breach cost WALL_BREACH ticks)
  =  palisade        (breach cost PALISADE_BREACH ticks)
  G  gate            (breach cost GATE_BREACH ticks)
  A  defender archer (stands on the cell under it)
  W  defender archer standing ON a wall (rampart)
  S  attacker start
  T  target (the Home commander / war-room)

OPEN RULING: timber gates currently block movement but NOT sight, so archers
shoot through them and cover the approach lane. Discovered during M2d
calibration, awaiting a ruling on whether gates should be opaque.
"""

OPEN, WALL, PALISADE, GATE = 0, 1, 2, 3

WALL_BREACH = 40        # ticks to dig through dressed stone
PALISADE_BREACH = 6     # ticks through timber
GATE_BREACH = 10        # ticks through the gate -- gates are the cheap edge
ARCHER_RANGE = 6        # Chebyshev range of a bow in stage 1

DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))

BREACH = {OPEN: 0, WALL: WALL_BREACH, PALISADE: PALISADE_BREACH,
          GATE: GATE_BREACH}


class WorldMap:
    def __init__(self, rows, heights=None):
        """rows: list of equal-length strings using the legend above.
        heights: optional [y][x] block-stack heights. Defaults to 1 for any
        solid cell, 0 for open ground -- which reproduces the old flat model.
        """
        self.h, self.w = len(rows), len(rows[0])
        self.cell = [[OPEN] * self.w for _ in range(self.h)]
        self.archers = []                 # defender firing positions
        self.start = self.target = None
        tall = {}                         # digit legend: stone of that height
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == '#':
                    self.cell[y][x] = WALL
                elif ch == '=':
                    self.cell[y][x] = PALISADE
                elif ch == 'G':
                    self.cell[y][x] = GATE
                elif ch == 'A':
                    self.archers.append((x, y))
                elif ch == 'W':
                    self.cell[y][x] = WALL
                    self.archers.append((x, y))
                elif ch.isdigit() and ch != '0':
                    self.cell[y][x] = WALL          # stone, this many high
                    tall[(x, y)] = int(ch)
                elif ch == 'S':
                    self.start = (x, y)
                elif ch == 'T':
                    self.target = (x, y)

        if heights is None:
            heights = [[tall.get((x, y), 1) if self.cell[y][x] == WALL else 0
                        for x in range(self.w)] for y in range(self.h)]
        self.height = heights

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def eye(self, x, y):
        """A unit stands on top of whatever it occupies (ruled 2026-08-20):
        placing an archer on a block puts him on it, one level of advantage."""
        return self.height[y][x] + 1

    def blocks_sight(self, x, y, eye=1):
        """Stone blocks a line only if it stands at or above the eye looking
        through it. A man on a one-high wall sees over one-high walls; the
        same wall blinds a man standing beside it. Timber gates never block."""
        return self.cell[y][x] == WALL and self.height[y][x] >= eye

    # --- line of sight: integer walk, endpoints excluded ---------------------
    def los(self, a, b, eye=1):
        (x0, y0), (x1, y1) = a, b
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
        err, x, y = dx - dy, x0, y0
        while True:
            if (x, y) != a and (x, y) != b and self.blocks_sight(x, y, eye):
                return False
            if (x, y) == b:
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    # --- exposure field: defender fire lines over every cell -----------------
    def exposure_field(self):
        """exp[y][x] = number of defender firing positions covering that cell.

        A field like smoke or water: computed identically everywhere, consumed
        by whoever reads it (the attacker's planner here; individual units'
        risk-awareness later).
        """
        exp = [[0] * self.w for _ in range(self.h)]
        for ax, ay in self.archers:
            eye = self.eye(ax, ay)
            for y in range(self.h):
                for x in range(self.w):
                    if max(abs(x - ax), abs(y - ay)) <= ARCHER_RANGE \
                            and self.los((ax, ay), (x, y), eye):
                        exp[y][x] += 1
        return exp
