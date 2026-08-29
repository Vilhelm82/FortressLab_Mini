"""
The world in three dimensions.

Columns of typed blocks, not a heightmap — because the design needs
subsurface galleries under walls, and a heightmap cannot express a tunnel.

    z = 0        bedrock / earth. Solid everywhere unless excavated.
    z = 1..n     what is built. A wall 2 high fills z=1 and z=2.
    a unit       stands in the lowest air cell above a solid one.
    his eye      is at his own z (the ruled "stack height + 1").

Sound moves through air in 26 directions and pays to cross material. So it
goes over a low wall, down a stairwell, along a gallery — no rule for any of
those, just the shape of the space.
"""

from math import exp, log
import heapq

AIR = None
EARTH, STONE, TIMBER, STAIR = "earth", "stone", "timber", "stair"

# A stair is solid like any other block — it stops sight and sound the same
# way — but a man standing on one may step to a neighbouring level. It is the
# only thing that connects heights: without it, a wall-walk is unreachable.
CLIMBABLE = {STAIR}

# 26-neighbourhood: sound goes any way it can
NB26 = [(dx, dy, dz)
        for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
        if (dx, dy, dz) != (0, 0, 0)]

# movement: eight compass steps, on the level. Changing level requires a
# stair — men do not scramble up walls.
NB8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
       if (dx, dy) != (0, 0)]


class World:
    """A voxel world. `solid[(x,y,z)] = material`; everything else is air.

    z=0 is filled with EARTH at construction unless `bedrock=False`, so the
    ground exists without anyone declaring every cell of it.
    """

    def __init__(self, w, h, depth=6, bedrock=True):
        self.w, self.h, self.depth = w, h, depth
        self.solid = {}
        if bedrock:
            for x in range(w):
                for y in range(h):
                    self.solid[(x, y, 0)] = EARTH

    # --- editing ---------------------------------------------------------

    def fill(self, x, y, z0, z1, material):
        for z in range(z0, z1 + 1):
            self.solid[(x, y, z)] = material

    def excavate(self, x, y, z):
        self.solid.pop((x, y, z), None)

    def material(self, c):
        return self.solid.get(c)

    def air(self, c):
        x, y, z = c
        return (0 <= x < self.w and 0 <= y < self.h
                and -self.depth <= z <= self.depth
                and c not in self.solid)

    def column_top(self, x, y):
        """Highest solid z in a column; None if the column is all air."""
        zs = [z for (cx, cy, z) in self.solid if cx == x and cy == y]
        return max(zs) if zs else None

    def stand(self, x, y):
        """Where a man on this column stands: the air cell just above the
        highest solid block. None if there is nothing to stand on."""
        top = self.column_top(x, y)
        if top is None:
            return None
        c = (x, y, top + 1)
        return c if self.air(c) else None

    def standable(self, c):
        """Can a man be here? Air, with something solid directly beneath."""
        x, y, z = c
        return self.air(c) and not self.air((x, y, z - 1))

    def on_stair(self, c):
        """Is the block this man is standing on a stair?"""
        x, y, z = c
        return self.solid.get((x, y, z - 1)) in CLIMBABLE

    def steps_from(self, c):
        """Where a man standing at `c` may go next tick.

        Eight compass steps on the level, always. A change of one level is
        legal only when the HIGHER of the two standing cells rests on a
        stair — climbing it going up, descending it coming down. One stair
        block lifts you one level; to rise two you need a second stair, and
        that one needs something solid beneath it.
        """
        if not self.standable(c):
            return []
        x, y, z = c
        out = []
        for dx, dy in NB8:
            for dz in (0, 1, -1):
                n = (x + dx, y + dy, z + dz)
                if not self.standable(n):
                    continue
                if dz != 0:
                    higher = n if n[2] > z else c
                    if not self.on_stair(higher):
                        continue
                out.append(n)
                break                 # nearest reachable level in this direction
        return out

    def cells(self):
        return [c for c in self._all() if self.air(c)]

    def _all(self):
        for x in range(self.w):
            for y in range(self.h):
                for z in range(-self.depth, self.depth + 1):
                    yield (x, y, z)

    def standing_cells(self):
        return [c for c in self._all() if self.standable(c)]

    # --- propagation -----------------------------------------------------

    def band_field(self, src, step_decay, tx):
        """Amplitude multiplier per air cell for ONE band, by the loudest
        path. Dijkstra in -log(amplitude) space over the 26-neighbourhood.

        step_decay: per-step multiplier for this band (highs die faster).
        tx: {material: transmission multiplier}; 0 means impassable.
        """
        step = -log(step_decay)
        cost_mat = {}
        for m, v in tx.items():
            cost_mat[m] = float("inf") if v <= 0.0 else -log(v)

        cost = {src: 0.0}
        pq = [(0.0, src)]
        while pq:
            c, cell = heapq.heappop(pq)
            if c > cost.get(cell, float("inf")):
                continue
            x, y, z = cell
            for dx, dy, dz in NB26:
                n = (x + dx, y + dy, z + dz)
                if not (0 <= n[0] < self.w and 0 <= n[1] < self.h
                        and -self.depth <= n[2] <= self.depth):
                    continue
                mat = self.solid.get(n)
                w = cost_mat.get(mat, 0.0) if mat else 0.0
                if w == float("inf"):
                    continue
                nc = c + step + w
                if nc < cost.get(n, float("inf")):
                    cost[n] = nc
                    heapq.heappush(pq, (nc, n))
        return {k: exp(-v) for k, v in cost.items()}

    # --- sight -----------------------------------------------------------

    def los(self, a, b, steps=None):
        """3D line of sight between two cells, sampled along the segment.
        Blocked by any solid voxel between them. Height therefore matters:
        a man on a tower sees over a curtain that blinds one beside it."""
        ax, ay, az = a
        bx, by, bz = b
        n = steps or max(abs(bx-ax), abs(by-ay), abs(bz-az))
        if n == 0:
            return True
        for i in range(1, n):
            t = i / n
            c = (round(ax + (bx-ax)*t),
                 round(ay + (by-ay)*t),
                 round(az + (bz-az)*t))
            if c == a or c == b:
                continue
            if not self.air(c):
                return False
        return True


# --- looking at it -----------------------------------------------------------

GLYPH = {EARTH: ".", STONE: "#", TIMBER: "=", STAIR: "/"}


def section(world, y, z_top=None, marks=None):
    """A side-on slice along one row: what you would see standing due south.

    Rows are heights, highest at the top. Columns are x. Solid blocks show
    their material; a man shows as his mark, standing on top of something.
    """
    z_top = z_top or 4
    marks = marks or {}
    out = []
    for z in range(z_top, -1, -1):
        line = ""
        for x in range(world.w):
            c = (x, y, z)
            if c in marks:
                line += marks[c]
            else:
                line += GLYPH.get(world.solid.get(c), " ")
        out.append("%2d |%s|" % (z, line))
    out.append("   +" + "-" * world.w + "+")
    out.append("    " + "".join(str(x % 10) for x in range(world.w)))
    return "\n".join(out)


def plan(world, marks=None):
    """Looking down: the height of each column, or a man's mark."""
    marks = marks or {}
    flat = {(c[0], c[1]): m for c, m in marks.items()}
    out = ["   " + "".join(str(x % 10) for x in range(world.w))]
    for y in range(world.h):
        line = ""
        for x in range(world.w):
            if (x, y) in flat:
                line += flat[(x, y)]
                continue
            top = world.column_top(x, y)
            line += "." if top in (None, 0) else (
                "/" if world.solid.get((x, y, top)) == STAIR else str(top))
        out.append("%2d %s" % (y, line))
    return "\n".join(out)
