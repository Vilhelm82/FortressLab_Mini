"""
The resonance field — THE DEFAULT SYSTEM (ruled 26 Aug 2026).

Orders are performances, not prose. This module is the runtime the proposal
specifies (docs/memos/PROPOSAL_resonance_command.md): steady-state
superposition of attenuating sources over walkable paths, addressing by
region root + diatonic dyad, the octave stack (depth is authority),
echolocation, three detection channels, masking, dB gating, the inversion
cascade, messenger root-replacement, and attraction by harmonic
complementarity.

Deterministic. No RNG. All constants in config_balance.RESONANCE.
"""

from collections import deque
from math import atan2, cos, pi

from fortresslab_mini.config_balance import RESONANCE as R

SEMI = 2 ** (1 / 12)
MAJOR_DEGREES = (2, 4, 5, 7, 9, 11)          # the 6 non-root scale degrees
DIRS8 = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))


def freq(layer, semitone):
    """Absolute frequency of a note: layer octave x chromatic step."""
    return round(R["base_hz"] * R["layer_mult"][layer] * (SEMI ** semitone), 2)


def region_root(region):                     # region 0..11
    return ("LOC", freq("LOC", region))


def dyad_specifier(region, degree_ix):       # degree_ix 0..5 (diatonic)
    return ("SPEC", freq("SPEC", (region + MAJOR_DEGREES[degree_ix]) % 12))


def leader_note(region):
    return ("LEAD", freq("LEAD", region))


def extension(region, degree_ix):
    return ("EXT", freq("EXT", (region + MAJOR_DEGREES[degree_ix]) % 12))


class Grid:
    """walkable topology + materials. material: None | 'stone' | 'timber'."""

    def __init__(self, w, h, stone=(), timber=()):
        self.w, self.h = w, h
        self.stone, self.timber = set(stone), set(timber)

    def cells(self):
        return [(x, y) for x in range(self.w) for y in range(self.h)]

    def open(self, c):
        return c not in self.stone and c not in self.timber

    def sound_dist(self, src):
        """Per-cell (steps, walls_crossed) for sound: it may pass through
        material, paying a transmission penalty per wall cell entered.
        Dijkstra-lite over uniform steps; walls tracked separately so each
        band applies its own transmission factor."""
        best = {src: (0, ())}
        q = deque([src])
        while q:
            c = q.popleft()
            d, walls = best[c]
            for dx, dy in DIRS8:
                n = (c[0]+dx, c[1]+dy)
                if not (0 <= n[0] < self.w and 0 <= n[1] < self.h):
                    continue
                mat = ("stone" if n in self.stone else
                       "timber" if n in self.timber else None)
                nw = walls + ((mat,),) if mat else walls
                cand = (d + 1, nw)
                if n not in best or cand[0] < best[n][0] \
                        or (cand[0] == best[n][0] and len(nw) < len(best[n][1])):
                    best[n] = cand
                    q.append(n)
        return best

    def los(self, a, b):
        """Bresenham; blocked by any material cell."""
        (x0, y0), (x1, y1) = a, b
        dx, dy = abs(x1-x0), abs(y1-y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err, x, y = dx - dy, x0, y0
        while (x, y) != (x1, y1):
            e2 = 2*err
            if e2 > -dy: err -= dy; x += sx
            if e2 < dx:  err += dx; y += sy
            if (x, y) != (x1, y1) and not self.open((x, y)):
                return False
        return True


class Emitter:
    """Anything that sings: a tuned location, a leader, a unit.
    notes: iterable of (layer, freq). sign: +1 Home, -1 Away.
    db: voice gain 0..1. Perception beam is NOT attenuated by db."""

    def __init__(self, pos, notes, sign=+1, db=1.0, numbers=1.0, facing=(1,0)):
        self.pos = tuple(pos)
        self.notes = tuple(notes)
        self.sign = sign
        self.db = db
        self.numbers = numbers
        self.facing = facing


class Field:
    """Steady-state superposition. hear() is a pure function of position —
    path-independent by construction; the conformance tests prove it."""

    def __init__(self, grid, emitters):
        self.grid = grid
        self.emitters = list(emitters)
        self._dists = {}

    def _dist(self, src):
        if src not in self._dists:
            self._dists[src] = self.grid.sound_dist(src)
        return self._dists[src]

    def _amp(self, e, note, at):
        layer, _ = note
        entry = self._dist(e.pos).get(at)
        if entry is None:
            return 0.0
        d, walls = entry
        a = e.db * e.numbers * R["layer_weight"][layer] * (R["decay"][layer] ** d)
        for (mat,) in walls:
            a *= R["stone_tx" if mat == "stone" else "timber_tx"][layer]
        return a

    def hear(self, at):
        """Signed spectrum at a cell: {(layer,freq): amplitude}."""
        spec = {}
        for e in self.emitters:
            for note in e.notes:
                a = self._amp(e, note, at)
                if a > 0:
                    spec[note] = spec.get(note, 0.0) + e.sign * a
        return spec

    # ---- perception channels (proposal §19/§22/§23) -------------------

    @staticmethod
    def _angle_off_facing(observer, target_pos):
        v = (target_pos[0]-observer.pos[0], target_pos[1]-observer.pos[1])
        if v == (0, 0):
            return 0.0
        a = atan2(v[1], v[0]) - atan2(observer.facing[1], observer.facing[0])
        while a > pi: a -= 2*pi
        while a < -pi: a += 2*pi
        return abs(a)                       # 0 = dead ahead, pi = behind

    def channels(self, observer, target):
        """The four channel strengths of `observer` noticing `target`."""
        d = max(1, abs(target.pos[0]-observer.pos[0]),
                   abs(target.pos[1]-observer.pos[1]))
        seen = self.grid.los(observer.pos, target.pos) and d <= R["beam_range"]
        looking = 4.0 / d if seen else 0.0                  # beam: full dB

        own = self.hear(observer.pos)
        interference = 0.0
        for note in observer.notes:                          # phase overlap
            if any(n == note for n in target.notes):
                interference += abs(self._amp(target, note, observer.pos))
        interference *= 3.0

        raw = sum(abs(self._amp(target, n, observer.pos)) for n in target.notes)
        # masking is by OTHER voices: a singer subtracts his own (echolocation
        # already requires self-monitoring), and the target is the signal,
        # not part of the noise floor.
        ambient = sum(abs(self._amp(e, n, observer.pos))
                      for e in self.emitters
                      if e is not observer and e is not target
                      for n in e.notes)
        audible = raw > max(R["hear_floor"], R["mask_ratio"] * max(ambient, 0.0))
        angle = self._angle_off_facing(observer, target.pos)
        hearing = (raw * (0.25 + 0.75 * cos(angle/2)**2)) if audible else 0.0
        hearing *= 2.0

        felt = 0.0                                          # being looked at
        if self.grid.los(target.pos, observer.pos) and d <= R["beam_range"]:
            rear = self._angle_off_facing(target, observer.pos)  # via target
            felt = 0.5 * max(0.0, cos(pi - rear) * -1)      # 0 at 180 deg
            # felt is how much OBSERVER notices TARGET's beam on them:
            beam_on_me = self._angle_off_facing(target, observer.pos)
            felt = 0.5 * max(0.0, cos(beam_on_me))          # silent behind
        return {"looking": looking, "interference": interference,
                "hearing": hearing, "being_looked_at": felt}

    def priority_target(self, unit, enemies):
        """Strongest cancellation source = offensive priority (§4)."""
        scored = [(self.channels(unit, e)["interference"], i)
                  for i, e in enumerate(enemies)]
        best = max(scored)
        return enemies[best[1]] if best[0] > 0 else None

    # ---- echolocation (§21) -------------------------------------------

    def ping(self, unit, locations):
        """Unit sings its part; each tuned location returns its signature
        scaled by match, round-trip attenuation, and the unit's own dB.
        Returns {location: (return_strength, resolved_layers)}."""
        out = {}
        for loc in locations:
            entry = self._dist(unit.pos).get(loc.pos)
            if entry is None:
                out[loc] = (0.0, set()); continue
            d, walls = entry
            match = len(set(unit.notes) & set(loc.notes))
            if match == 0:
                out[loc] = (0.0, set()); continue
            strength, layers = 0.0, set()
            for note in set(unit.notes) & set(loc.notes):
                layer = note[0]
                a = unit.db * R["layer_weight"][layer] * (R["decay"][layer] ** (2*d))
                for (mat,) in walls:
                    a *= R["stone_tx" if mat == "stone" else "timber_tx"][layer] ** 2
                if a > R["echo_floor"]:
                    strength += a; layers.add(layer)
            out[loc] = (strength, layers)
        return out

    def navigate_target(self, unit, locations):
        """Harmonisation sets the destination (§23)."""
        returns = self.ping(unit, locations)
        best = max(returns.items(), key=lambda kv: kv[1][0])
        return best[0] if best[1][0] > 0 else None

    # ---- least-detection routing (§23) --------------------------------

    def least_detection_route(self, start, goal, watchers):
        cost = {}
        for c in self.grid.cells():
            if not self.grid.open(c):
                continue
            det = 0.0
            for w in watchers:
                d = max(1, abs(c[0]-w.pos[0]), abs(c[1]-w.pos[1]))
                if d <= R["beam_range"] and self.grid.los(w.pos, c) \
                        and self._angle_off_facing(w, c) < R["beam_halfangle"]:
                    det += 4.0 / d
            cost[c] = 1.0 + R["lambda_obs"] * det * 50.0
        import heapq
        pq, dist, prev = [(0.0, start)], {start: 0.0}, {}
        while pq:
            dc, c = heapq.heappop(pq)
            if c == goal: break
            if dc > dist.get(c, 1e18): continue
            for dx, dy in DIRS8:
                n = (c[0]+dx, c[1]+dy)
                if n not in cost: continue
                nd = dc + cost[n]
                if nd < dist.get(n, 1e18):
                    dist[n] = nd; prev[n] = c
                    heapq.heappush(pq, (nd, n))
        path, c = [], goal
        while c != start:
            path.append(c); c = prev[c]
        return list(reversed(path))


class CompanyPart:
    """A part = (unit type, count) -> chord. No unit identity (§31)."""

    def __init__(self, chord, target_count, voiced_count):
        self.chord = tuple(chord)
        self.target = target_count
        self.voiced = voiced_count

    @property
    def missing(self):
        return max(0, self.target - self.voiced)


def attraction(stray_root, companies):
    """§29: harmonic complementarity, not amplitude. A stray is drawn to the
    company whose chord CONTAINS its root and which has an unresolved gap."""
    best, best_score = None, 0.0
    for comp in companies:
        for part in comp["parts"]:
            if stray_root in part.chord and part.missing > 0:
                score = 1.0 + part.missing
                if score > best_score:
                    best, best_score = comp, score
    return best


class WanderingUnit:
    """Carries a chord; when leaderless, the rising filter strips it from the
    bottom (§28). The root slot is a cursor (§30)."""

    def __init__(self, pos, notes, leaderless=False):
        self.pos = tuple(pos)
        self.notes = sorted(notes, key=lambda n: n[1])       # by frequency
        self.leaderless = leaderless
        self.hpf = R["hpf_start_hz"]

    @property
    def root(self):
        return self.notes[0] if self.notes else None

    def tick_filter(self):
        if not self.leaderless:
            return
        self.hpf *= R["hpf_mult_per_tick"]
        self.notes = [n for n in self.notes if n[1] >= self.hpf]

    # messenger progression: arrival replaces the root (§30)
    def arrive(self):
        if self.notes:
            self.notes = self.notes[1:]


def follow_target(field, unit, leader, location_emitter):
    """§28 handoff: the unit tracks whichever matched source is louder at its
    ear — the leader (LEAD layer) or the location root (LOC layer, deeper,
    stronger). No rule: just amplitude."""
    la = sum(field._amp(leader, n, unit.pos) for n in leader.notes)
    ra = sum(field._amp(location_emitter, n, unit.pos)
             for n in location_emitter.notes)
    return leader.pos if la > ra else location_emitter.pos
