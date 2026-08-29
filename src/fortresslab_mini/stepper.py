"""
The stepper — motion, and nothing else.

Just enough to watch resonance behave over time. No orders, no commander, no
credits, no spawning. You place emitters, you step, you look at what happened.

A Mover is an Emitter that walks. Each tick it re-reads the field, picks a
destination by the rule you gave it, and takes one Chebyshev step toward it
along walkable ground. The field is rebuilt every tick because emitters move,
which is also what makes it honest: nothing is cached across a step.

Contact stays as ruled — Chebyshev <= 1 between opposed movers kills both.
"""

from collections import deque

from fortresslab_mini.resonance import DIRS8, Emitter, Field

DEAD, ALIVE = "dead", "alive"


class Mover:
    """An emitter with legs and a way of choosing where to go.

    goal(mover, field, world) -> (x, y) | None
        Called each tick. Return None to stand still. This is where a
        mechanic under test plugs in: harmonisation, least detection,
        following a leader, chasing the strongest canceller.
    """

    def __init__(self, emitter, goal=None, speed=1, name=None):
        self.e = emitter
        self.goal = goal
        self.speed = speed
        self.name = name or "mover"
        self.state = ALIVE
        self.path = [tuple(emitter.pos)]

    @property
    def pos(self):
        return self.e.pos

    def kill(self):
        self.state = DEAD


def _walk_dist(grid, src):
    """Steps over open ground only — men route around stone, they do not
    walk through it. (Sound does; legs do not.)"""
    seen, q = {src: 0}, deque([src])
    while q:
        c = q.popleft()
        for dx, dy in DIRS8:
            n = (c[0] + dx, c[1] + dy)
            if 0 <= n[0] < grid.w and 0 <= n[1] < grid.h \
                    and grid.open(n) and n not in seen:
                seen[n] = seen[c] + 1
                q.append(n)
    return seen


def step_toward(grid, frm, to):
    """One step along the shortest open path. Returns frm if unreachable."""
    if frm == to:
        return frm
    dist = _walk_dist(grid, to)
    best, bd = frm, dist.get(frm)
    if bd is None:
        return frm
    for dx, dy in DIRS8:
        n = (frm[0] + dx, frm[1] + dy)
        d = dist.get(n)
        if d is not None and d < bd:
            best, bd = n, d
    return best


class Stepper:
    """Runs movers over a grid. `world` is a free-form dict handed to every
    goal function — put whatever the mechanic under test needs in it."""

    def __init__(self, grid, movers, statics=(), world=None):
        self.grid = grid
        self.movers = list(movers)
        self.statics = list(statics)        # tuned locations, silent posts
        self.world = world if world is not None else {}
        self.tick = 0
        self.log = []                       # (tick, name, event, detail)

    def living(self):
        return [m for m in self.movers if m.state == ALIVE]

    def field(self):
        """Rebuilt every tick: emitters have moved."""
        return Field(self.grid, self.statics
                     + [m.e for m in self.living()])

    def _resolve_contact(self):
        live = self.living()
        doomed = set()
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if a.e.sign != b.e.sign and \
                        max(abs(a.pos[0] - b.pos[0]),
                            abs(a.pos[1] - b.pos[1])) <= 1:
                    doomed.add(a)
                    doomed.add(b)
        for m in doomed:
            m.kill()
            self.log.append((self.tick, m.name, "killed", m.pos))
        return doomed

    def step(self):
        """One tick: everyone reads the same field, then everyone moves, then
        contact resolves. Simultaneous, as ruled — no turn order."""
        f = self.field()
        intents = {}
        for m in self.living():
            if m.goal is None:
                continue
            tgt = m.goal(m, f, self.world)
            if tgt is not None and tuple(tgt) != m.pos:
                intents[m] = tuple(tgt)

        for m, tgt in intents.items():
            p = m.pos
            for _ in range(m.speed):
                nxt = step_toward(self.grid, p, tgt)
                if nxt == p:
                    break
                p = nxt
            if p != m.pos:
                m.e.facing = (max(-1, min(1, p[0] - m.pos[0])),
                              max(-1, min(1, p[1] - m.pos[1])))
                m.e.pos = p
                m.path.append(p)

        self.tick += 1
        self._resolve_contact()
        return f

    def run(self, ticks, until=None):
        """Steps up to `ticks` times. `until(stepper) -> bool` stops early."""
        for _ in range(ticks):
            if until is not None and until(self):
                return self.tick
            self.step()
        return self.tick


# --- goal functions: one per mechanic under test -----------------------------

def seek_harmony(locations):
    """Go wherever your own part resonates best (echolocation)."""
    def goal(m, field, world):
        best = field.navigate_target(m.e, locations)
        return best.pos if best is not None else None
    return goal


def follow_then_fold(leader_mover, post):
    """Track the leader until the post's deeper root drowns him out."""
    def goal(m, field, world):
        if leader_mover.state == DEAD:
            return post.pos
        la = sum(field._amp(leader_mover.e, n, m.pos)
                 for n in leader_mover.e.notes)
        ra = sum(field._amp(post, n, m.pos) for n in post.notes)
        return leader_mover.pos if la > ra else post.pos
    return goal


def chase_strongest_canceller(enemies):
    """The direction of destructive interference draws the focus."""
    def goal(m, field, world):
        live = [e.e for e in enemies if e.state == ALIVE]
        if not live:
            return None
        tgt = field.priority_target(m.e, live)
        return tgt.pos if tgt is not None else None
    return goal


def sneak_to(dest, watchers):
    """Least detection: the route bends around whoever is looking."""
    def goal(m, field, world):
        if m.pos == dest:
            return None
        watch = [w.e if isinstance(w, Mover) else w for w in watchers]
        path = field.least_detection_route(m.pos, dest, watch)
        return path[0] if path else dest
    return goal


def hold(_m=None, _f=None, _w=None):
    """Stand."""
    return None
