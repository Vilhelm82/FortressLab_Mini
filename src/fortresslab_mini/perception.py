"""
Perception — the capacitor.

Ruled 2026-08-20: diagonal/peripheral awareness grants HALF what direct facing
grants. A unit crossing another's periphery is flagged as PRESENCE only, not
identified. Cross again inside the alert window and it becomes IDENTIFIED.
Range degrades the same way: beyond the soft maximum, a sighting carries only
peripheral quality. Vantage height extends reach.

Angle and distance are the same mechanic in two geometries -- MARGINAL CONTACT
-- so both are implemented as one accumulator per observer-target pair:

    charge  = how well this observer currently knows this target
    +FULL   direct front arc, inside soft range
    +HALF   periphery, or beyond soft range
    decay   one step per DECAY_EVERY ticks   <- the alert cooldown

    charge >= IDENTIFY  -> identified   (orange)
    charge >= PRESENCE  -> presence     (purple, cooling down)
    otherwise           -> nothing

EVERY NUMBER HERE IS A PARAMETER, not a constant (ruled: cone reach and the
nuances are for the LLM R&D phase to balance). Sweep CONFIG, don't edit code.
"""

from fortresslab_mini.kernel import cheb
from fortresslab_mini.worldmap import DIRS8

CONFIG = {
    "front_arc": 1,       # steps either side of facing that count as FRONT
    "periphery_arc": 2,   # further steps that count as PERIPHERY; beyond = rear
    "soft_range": 5,      # full-quality sighting distance
    "hard_range": 8,      # beyond this, nothing at all
    "height_bonus": 2,    # extra range per level of vantage
    "full": 2,            # charge from a clean front-arc sighting
    "half": 1,            # charge from periphery or long range
    "cap": 3,             # accumulator ceiling
    "identify": 2,        # threshold for full identification
    "presence": 1,        # threshold for "something is out there"
    "decay_every": 4,     # ticks per unit of decay -- the alert cooldown
}

NOTHING, PRESENCE, IDENTIFIED = "nothing", "presence", "identified"
FRONT, PERIPHERY, REAR = "front", "periphery", "rear"

# Facing is an index into RING, which goes round the compass clockwise with y
# pointing down. NOT DIRS8 -- that is lexicographic, and doing modular arc
# arithmetic on it silently makes north the rear of east.
RING = ((1, 0), (1, 1), (0, 1), (-1, 1),
        (-1, 0), (-1, -1), (0, -1), (1, -1))


def facing_from_delta(dx, dy):
    """The direction a unit ends up facing after stepping (dx, dy)."""
    return RING.index((dx, dy))


def arc_of(facing, dx, dy, cfg=CONFIG):
    """Which arc a bearing falls in, relative to a RING facing index."""
    if dx == 0 and dy == 0:
        return FRONT
    n = max(abs(dx), abs(dy))
    ux, uy = round(dx / n), round(dy / n)
    bi = RING.index((ux, uy))
    off = min((bi - facing) % 8, (facing - bi) % 8)
    if off <= cfg["front_arc"]:
        return FRONT
    if off <= cfg["periphery_arc"]:
        return PERIPHERY
    return REAR


class Perception:
    """One accumulator per (observer, target). Deterministic, integer-only."""

    def __init__(self, wm, cfg=None):
        self.wm = wm
        self.cfg = dict(CONFIG, **(cfg or {}))
        self.charge = {}                  # (obs_uid, tgt_uid) -> int
        self._last_decay = 0

    # --- one observation -----------------------------------------------------

    def quality(self, obs, tgt):
        """How much charge this sighting is worth: full, half, or none.

        Returns (gain, arc, reason) so the visualiser can say WHY, not just
        show a colour.
        """
        c = self.cfg
        eye = self.wm.eye(obs.x, obs.y)
        reach = c["hard_range"] + c["height_bonus"] * (eye - 1)
        soft = c["soft_range"] + c["height_bonus"] * (eye - 1)
        d = cheb((obs.x, obs.y), (tgt.x, tgt.y))
        if d > reach:
            return 0, None, "out of reach"
        if not self.wm.los((obs.x, obs.y), (tgt.x, tgt.y), eye):
            return 0, None, "no line"
        arc = arc_of(obs.facing, tgt.x - obs.x, tgt.y - obs.y, c)
        if arc == REAR:
            return 0, arc, "behind him"
        if arc == PERIPHERY:
            return c["half"], arc, "caught in the corner of the eye"
        if d > soft:
            return c["half"], arc, "too far to make out"
        return c["full"], arc, "seen plainly"

    # --- the tick ------------------------------------------------------------

    def step(self, units, tick):
        """Charge every live observer-target pair, then decay on cadence."""
        c = self.cfg
        events = []
        for obs in units:
            for tgt in units:
                if obs.side == tgt.side or obs.uid == tgt.uid:
                    continue
                gain, arc, why = self.quality(obs, tgt)
                if not gain:
                    continue
                k = (obs.uid, tgt.uid)
                before = self.charge.get(k, 0)
                after = min(c["cap"], before + gain)
                self.charge[k] = after
                if self._state(before) != self._state(after):
                    events.append({"observer": obs.uid, "target": tgt.uid,
                                   "state": self._state(after), "arc": arc,
                                   "why": why})
        if tick - self._last_decay >= c["decay_every"]:
            self._last_decay = tick
            for k in list(self.charge):
                self.charge[k] -= 1
                if self.charge[k] <= 0:
                    del self.charge[k]
        return events

    def _state(self, v):
        c = self.cfg
        if v >= c["identify"]:
            return IDENTIFIED
        if v >= c["presence"]:
            return PRESENCE
        return NOTHING

    def state(self, obs_uid, tgt_uid):
        return self._state(self.charge.get((obs_uid, tgt_uid), 0))

    def knows(self, obs_uid, tgt_uid):
        """Identified — good enough to act on deliberately."""
        return self.state(obs_uid, tgt_uid) == IDENTIFIED

    def cone(self, obs):
        """What the viewport draws: the arcs, at this unit's actual reach."""
        c = self.cfg
        eye = self.wm.eye(obs.x, obs.y)
        reach = c["hard_range"] + c["height_bonus"] * (eye - 1)
        front, periph = [], []
        for y in range(max(0, obs.y - reach), min(self.wm.h, obs.y + reach + 1)):
            for x in range(max(0, obs.x - reach),
                           min(self.wm.w, obs.x + reach + 1)):
                if cheb((x, y), (obs.x, obs.y)) > reach:
                    continue
                if not self.wm.los((obs.x, obs.y), (x, y), eye):
                    continue
                a = arc_of(obs.facing, x - obs.x, y - obs.y, c)
                (front if a == FRONT else periph if a == PERIPHERY
                 else []).append((x, y))
        return {"front": front, "periphery": periph, "eye": eye,
                "reach": reach}
