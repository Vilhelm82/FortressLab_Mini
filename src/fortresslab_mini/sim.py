"""
The tick loop — where the kernel, the order language and the map finally meet.

Deterministic and integer-only. Every run records a full TRACE: one frame per
tick carrying positions, company states and events, so a run can be replayed,
scrubbed and stepped rather than watched once (spec: seeded determinism).

CADENCE (ruled 2026-08-20): units act on every tick for now. The decision sits
behind `acts_this_tick` alone -- swap that one function for a rank- or
kind-dependent rule and cadence lands everywhere at once, with no other change.

NOT YET MODELLED, deliberately: perception (every unit sees everything within
DETECTION), armour, ammo consumption, engines, mining. Fog is absent on purpose
so the first sim runs give a known-clear baseline to compare against later.
"""

from dataclasses import dataclass, field

from fortresslab_mini.kernel import cheb
from fortresslab_mini.worldmap import DIRS8, BREACH
from fortresslab_mini.enemy_brain import cost_field
from fortresslab_mini.score import (ScoreExec, company_status, SELF_DIRECTED,
                                    STALE)
from fortresslab_mini.perception import (Perception, facing_from_delta, RING,
                                         IDENTIFIED, PRESENCE, NOTHING)

DETECTION = 6            # stand-in for perception until the capacitor lands
TICKS_PER_HOUR = 30      # diegetic clock; orders read time_at_or_after
CLOCK_START = 6

HOME, AWAY = 0, 1


def acts_this_tick(unit, tick):
    """The cadence hook. Every unit, every tick. Change here, only here."""
    return True


@dataclass
class Unit:
    uid: int
    side: int
    kind: str                 # 'C' commander, 'M' man-at-arms, 'A' archer...
    x: int
    y: int
    company: int = -1
    alive: bool = True
    facing: int = 0           # index into perception.RING; set by movement


@dataclass
class Company:
    cid: int
    side: int
    officer: int = -1              # uid, or -1 for none
    members: list = field(default_factory=list)
    order: ScoreExec = None
    initial: int = 0
    goal: tuple = None             # current destination, from the order node


class Sim:
    def __init__(self, wm, exposure=None, fog=False, perception_cfg=None):
        """fog defaults OFF: that is the v0 baseline (universal awareness),
        the known-clear control every fogged run is compared against. Turn it
        on per-run; it is a rung, not a global switch."""
        self.wm = wm
        self.fog = fog
        self.percept = Perception(wm, perception_cfg)
        self.exp = exposure if exposure is not None else wm.exposure_field()
        self.units = {}
        self.companies = {}
        self.tick = 0
        self.trace = []
        self._fields = {}                  # goal -> cost field, per tick

    # --- setup ---------------------------------------------------------------

    def add_unit(self, uid, side, kind, x, y, company=-1):
        self.units[uid] = Unit(uid, side, kind, x, y, company)
        return self.units[uid]

    def add_company(self, cid, side, officer, members, order=None, goal=None):
        c = Company(cid, side, officer, list(members), order,
                    len(members), goal)
        self.companies[cid] = c
        for uid in members:
            self.units[uid].company = cid
        return c

    # --- world observation ---------------------------------------------------

    def living(self, side=None):
        return [u for u in self.units.values()
                if u.alive and (side is None or u.side == side)]

    def _region_cells(self, company, region):
        """'here' = within DETECTION of the company's centre of mass.
        'assigned' = the current order node's granted area.
        'visible' = same as here until perception exists (documented, not silent).
        """
        mem = [self.units[u] for u in company.members if self.units[u].alive]
        if region in ("here", "visible"):
            if not mem:
                return lambda x, y: False
            cx = sum(u.x for u in mem) // len(mem)
            cy = sum(u.y for u in mem) // len(mem)
            return lambda x, y: cheb((x, y), (cx, cy)) <= DETECTION
        if region == "assigned" and company.order is not None:
            x0, y0, x1, y1 = company.order.current_scope()["area"]
            return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
        return lambda x, y: False

    def snapshot(self, company):
        """Build the world dict the order guards read. This is the join between
        the order language and the map: `count(enemy, here)` stops being a
        hand-written test fixture and starts being a fact."""
        alive = [self.units[u] for u in company.members if self.units[u].alive]
        counts = {}
        for region in ("here", "assigned", "visible"):
            inside = self._region_cells(company, region)
            for cls, pred in (
                    ("enemy", lambda u: u.side != company.side),
                    ("friend", lambda u: u.side == company.side),
                    ("messenger", lambda u: u.side == company.side
                     and u.kind == "r"),
                    ("officer", lambda u: u.side == company.side
                     and u.kind == "O"),
                    ("civilian", lambda u: u.kind == "m")):
                n = sum(1 for u in self.living() if pred(u) and inside(u.x, u.y))
                counts[(cls, region)] = n
        return {
            "clock": CLOCK_START + self.tick // TICKS_PER_HOUR,
            "elapsed": self.tick,
            "self": {"strength": len(alive), "initial": company.initial,
                     "losses": company.initial - len(alive), "ammo": 20},
            "count": counts,
            "hazard": {},
        }

    # --- movement ------------------------------------------------------------

    def _field(self, goal):
        if goal not in self._fields:
            self._fields[goal] = cost_field(self.wm, self.exp, goal)
        return self._fields[goal]

    def _nearest_enemy(self, unit):
        """Under fog a unit may only act deliberately on what it has
        IDENTIFIED. Presence alone is a reason to investigate, not to charge."""
        foes = [u for u in self.living()
                if u.side != unit.side
                and (not self.fog or self.percept.knows(unit.uid, u.uid))]
        if not foes:
            return None
        best = min(foes, key=lambda f: (cheb((f.x, f.y), (unit.x, unit.y)),
                                        f.uid))
        return best if cheb((best.x, best.y), (unit.x, unit.y)) <= DETECTION \
            else None

    def _goal_for(self, unit):
        """Bloodlust is the ground state; orders are impedance over it.

        A visible enemy inside the unit's permitted area is the goal. If the
        order's area forbids it, the unit holds to its assigned goal instead --
        the order shapes HOW and WHERE, never WHETHER (spec B4).
        """
        c = self.companies.get(unit.company)
        foe = self._nearest_enemy(unit)
        if foe is not None:
            if c is None or c.order is None or company_status(
                    self.units[c.officer].alive if c.officer in self.units
                    else False, c.order) == SELF_DIRECTED:
                return (foe.x, foe.y)
            x0, y0, x1, y1 = c.order.current_scope()["area"]
            if x0 <= foe.x <= x1 and y0 <= foe.y <= y1:
                return (foe.x, foe.y)
        if c is not None and c.goal is not None:
            return c.goal
        # Bloodlust fallback (spec B1-B2): a unit with nothing constraining it
        # closes on the enemy commander. Not gated by DETECTION -- v0 has no
        # fog, so awareness is universal by construction (spec U4). When the
        # perception capacitor lands, this reads the belief state instead.
        foes = [u for u in self.living()
                if u.side != unit.side and u.kind == "C"
                and (not self.fog or self.percept.knows(unit.uid, u.uid))]
        if foes:
            return (foes[0].x, foes[0].y)
        # Nothing identified: investigate the strongest mere PRESENCE.
        if self.fog:
            hits = [(self.percept.charge.get((unit.uid, u.uid), 0), u.uid, u)
                    for u in self.living() if u.side != unit.side]
            hits = [h for h in hits if h[0] > 0]
            if hits:
                _, _, u = max(hits)
                return (u.x, u.y)
        return None

    def _step_toward(self, unit, goal):
        dist = self._field(goal)
        here = dist[unit.y][unit.x]
        best, bestd = None, here
        for dx, dy in DIRS8:
            nx, ny = unit.x + dx, unit.y + dy
            if not self.wm.inside(nx, ny):
                continue
            d = dist[ny][nx]
            if d is not None and (bestd is None or d < bestd):
                best, bestd = (nx, ny), d
        return best

    # --- the tick ------------------------------------------------------------

    def step(self):
        events = []
        self._fields = {}

        # 0. Perception. Charge the accumulators before anyone decides anything.
        if self.fog:
            for e in self.percept.step(self.living(), self.tick):
                events.append(dict(e, kind="sighting"))

        # 1. Orders. Guards read the real world now.
        for c in self.companies.values():
            if c.order is None or c.order.released is not None:
                continue
            ev = c.order.step(self.snapshot(c))
            if ev:
                events.append({"company": c.cid, "order": ev[0],
                               "detail": ev[1] if len(ev) > 1 else None})
                if ev[0] == "release":
                    c.goal = None

        # 2. Movement. Intents, cadence, then the stopping rule (spec A4):
        #    no two units may STOP on the same cell; transit is unconstrained.
        claimed = {(u.x, u.y) for u in self.living()}
        intents = {}
        for u in sorted(self.living(), key=lambda u: u.uid):
            if not acts_this_tick(u, self.tick):
                continue
            goal = self._goal_for(u)
            if goal is None or (u.x, u.y) == goal:
                continue
            dest = self._step_toward(u, goal)
            if dest and dest not in claimed:
                claimed.discard((u.x, u.y))
                claimed.add(dest)
                intents[u.uid] = dest
        for uid, (x, y) in intents.items():
            u = self.units[uid]
            dx, dy = x - u.x, y - u.y
            if (dx, dy) in RING:
                u.facing = facing_from_delta(dx, dy)  # you face where you walk
            u.x, u.y = x, y

        # 3. Contact. Every hostile pair at Chebyshev <= 1 dies, simultaneously.
        doomed = set()
        live = self.living()
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if a.side != b.side and cheb((a.x, a.y), (b.x, b.y)) <= 1:
                    doomed.add(a.uid)
                    doomed.add(b.uid)
        for uid in sorted(doomed):
            self.units[uid].alive = False
            events.append({"death": uid, "side": self.units[uid].side,
                           "kind": self.units[uid].kind})

        self.tick += 1
        self.trace.append(self.frame(events))
        return events

    def frame(self, events=()):
        return {
            "tick": self.tick,
            "clock": CLOCK_START + self.tick // TICKS_PER_HOUR,
            "units": [{"uid": u.uid, "side": u.side, "kind": u.kind,
                       "x": u.x, "y": u.y, "facing": u.facing,
                       "sees": {t.uid: self.percept.state(u.uid, t.uid)
                                for t in self.living() if t.side != u.side
                                if self.percept.state(u.uid, t.uid) != NOTHING}}
                      for u in self.living()],
            "companies": [
                {"cid": c.cid,
                 "status": company_status(
                     c.officer in self.units and self.units[c.officer].alive,
                     c.order),
                 "node": c.order.node if c.order else None,
                 "released": c.order.released if c.order else None}
                for c in self.companies.values()],
            "events": list(events),
        }

    def terminal(self):
        """Only one way to end: a commander dies. Both on one tick is the tie."""
        h = any(u.kind == "C" and u.side == HOME for u in self.living())
        a = any(u.kind == "C" and u.side == AWAY for u in self.living())
        if h and a:
            return None
        return 0 if not h and not a else (1 if h else -1)

    def run(self, limit=400):
        self.trace.append(self.frame())
        while self.tick < limit:
            self.step()
            t = self.terminal()
            if t is not None:
                return t
        return None
