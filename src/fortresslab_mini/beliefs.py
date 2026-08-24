"""
Beliefs + closure — the cloud, and the error theory on top of it.

The BELIEF is a mass field over the map: where the commander thinks enemy
presence is. It is the transported object: predicted forward by a motion
model (diffusion), conditioned by observations when reports arrive.

The CLOSURE layer is the instrument on top (ruled 2026-08-20, on probation):
exact inference on a correct model has ZERO holonomy, so a loop that fails
to close — a patrol whose report disagrees with the commander's transported
prediction along the route — measures MODEL ERROR, not ordinary uncertainty.
Reports arrive only on return (messenger latency is a ruled mechanic), which
is exactly the regime where loop-thinking beats live filtering.

Floats permitted (ruled 2026-08-20). Every knob in CONFIG for the R&D sweep.
"""

CONFIG = {
    "diffuse": 0.12,       # motion model: per-tick mass share spread to 8-nbrs
    "see_empty": 0.10,     # multiplier for a cell reliably observed empty
    "see_hit": 40.0,       # multiplier for a cell with observed presence
    "obs_decay": 0.97,     # per-tick discount on stale report observations
    "floor": 1e-9,
}

NBRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


class BeliefField:
    """Commander's presence belief. Mass-normalised, walls carry none."""

    def __init__(self, wm, cfg=None):
        self.wm = wm
        self.cfg = dict(CONFIG, **(cfg or {}))
        self.open = [(x, y) for y in range(wm.h) for x in range(wm.w)
                     if wm.cell[y][x] == 0]
        u = 1.0 / len(self.open)
        self.b = [[u if wm.cell[y][x] == 0 else 0.0
                   for x in range(wm.w)] for y in range(wm.h)]

    def _normalise(self):
        s = sum(self.b[y][x] for x, y in self.open)
        if s <= 0:
            u = 1.0 / len(self.open)
            for x, y in self.open:
                self.b[y][x] = u
            return
        for x, y in self.open:
            self.b[y][x] = max(self.b[y][x] / s, self.cfg["floor"])

    def predict(self):
        """One tick of the motion model: enemies may step to any neighbour."""
        d = self.cfg["diffuse"]
        nb = [[0.0] * self.wm.w for _ in range(self.wm.h)]
        for x, y in self.open:
            m = self.b[y][x]
            if m <= 0:
                continue
            outs = [(x + dx, y + dy) for dx, dy in NBRS
                    if self.wm.inside(x + dx, y + dy)
                    and self.wm.cell[y + dy][x + dx] == 0]
            nb[y][x] += m * (1.0 - d)
            if outs:
                share = m * d / len(outs)
                for nx, ny in outs:
                    nb[ny][nx] += share
            else:
                nb[y][x] += m * d
        self.b = nb
        self._normalise()

    def fuse(self, observations, now):
        """Fuse a returned report: (x, y, seen_enemy, t_obs) tuples.
        Stale observations are discounted — the world may have moved since."""
        c = self.cfg
        for x, y, seen, t in observations:
            if self.wm.cell[y][x] != 0:
                continue
            age = max(0, now - t)
            w = c["obs_decay"] ** age
            mult = c["see_hit"] if seen else c["see_empty"]
            eff = mult * w + 1.0 * (1.0 - w)      # stale obs -> no-op
            self.b[y][x] *= eff
        self._normalise()

    def mass_near(self, x0, y0, r):
        return sum(self.b[y][x] for x, y in self.open
                   if max(abs(x - x0), abs(y - y0)) <= r)

    def argmax(self):
        return max(self.open, key=lambda p: self.b[p[1]][p[0]])

    def mass_in_rect(self, x0, y0, x1, y1):
        return sum(self.b[y][x] for x, y in self.open
                   if x0 <= x <= x1 and y0 <= y <= y1)


# --- Closure: the holonomy instrument ----------------------------------------

def loop_residual(belief_snapshots, observations, viewshed_r=0):
    """How badly did this loop fail to close?

    belief_snapshots: {t: predicted presence-mass function m(x, y, r)} — the
    commander's TRANSPORTED belief at each visit time (prediction only, no
    peeking at the report being scored).
    observations: (x, y, seen, t) along the route.

    Returns (total, per_obs) where per_obs carries the residual localised to
    each route point: |observed − predicted|. On a correct model with exact
    transport this is ~0 — nonzero closure measures model or filter error,
    never mere ignorance about unvisited ground.
    """
    per = []
    total = 0.0
    for x, y, seen, t in observations:
        p_hat = min(1.0, belief_snapshots[t](x, y, viewshed_r))
        r = abs((1.0 if seen else 0.0) - p_hat)
        per.append((x, y, t, r))
        total += r
    return total, per


def sector_residuals(per_obs, sector_of):
    out = {}
    for x, y, t, r in per_obs:
        s = sector_of(x, y)
        out[s] = out.get(s, 0.0) + r
    return out


def choose_next_loop(sectors, belief, staleness, w_mass=1.0, w_stale=0.02):
    """Closure-driven dispatch: close the loop where unclosed error can hide.
    Score = believed mass inside the sector + how long since its loop closed.
    Degenerate ties (all unvisited sectors equal) resolve by staleness alone —
    the centrifuge move: break the degeneracy by measuring it."""
    def score(name):
        x0, y0, x1, y1 = sectors[name]
        return w_mass * belief.mass_in_rect(x0, y0, x1, y1) \
            + w_stale * staleness[name]
    return max(sectors, key=score)
