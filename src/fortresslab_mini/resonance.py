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

from math import atan2, cos, pi

from fortresslab_mini.config_balance import RESONANCE as R


SEMI = 2 ** (1 / 12)
MAJOR_DEGREES = (2, 4, 5, 7, 9, 11)          # the 6 non-root scale degrees
# movement neighbourhood comes from the world (stairs decide levels)


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

    def __init__(self, world, emitters):
        self.world = world
        self.emitters = list(emitters)
        self._dists = {}

    def _dist(self, src, layer):
        key = (src, layer)
        if key not in self._dists:
            tx = {"earth": 0.0,
                  "stone": R["stone_tx"][layer],
                  "timber": R["timber_tx"][layer],
                  "stair": R["stone_tx"][layer]}
            self._dists[key] = self.world.band_field(
                src, R["decay"][layer], tx)
        return self._dists[key]

    def _amp(self, e, note, at):
        layer, _ = note
        m = self._dist(e.pos, layer).get(at)
        if m is None:
            return 0.0
        return e.db * e.numbers * R["layer_weight"][layer] * m

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
        # The beam is DIRECTIONAL: line of sight, within range, AND inside
        # the cone. Height is in the coordinates, so a man on a tower sees
        # over a curtain that blinds one standing beside it.
        in_cone = self._angle_off_facing(observer, target.pos) \
            <= R["beam_halfangle"]
        seen = (in_cone and d <= R["beam_range"]
                and self.world.los(observer.pos, target.pos))
        looking = 4.0 / d if seen else 0.0                  # beam: full dB

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

        # being looked at: how much the observer notices the target's beam
        # landing on him. Silent when it arrives from behind the target's
        # facing -- i.e. the target is looking away.
        felt = 0.0
        beam_on_me = self._angle_off_facing(target, observer.pos)
        if beam_on_me <= R["beam_halfangle"] and d <= R["beam_range"] \
                and self.world.los(target.pos, observer.pos):
            felt = 0.5 * max(0.0, cos(beam_on_me))
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
            shared = set(unit.notes) & set(loc.notes)
            if not shared:
                out[loc] = (0.0, set()); continue
            strength, layers = 0.0, set()
            for note in shared:
                layer = note[0]
                m = self._dist(unit.pos, layer).get(loc.pos)
                if m is None:
                    continue
                a = unit.db * R["layer_weight"][layer] * (m ** 2)   # round trip
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
        for c in self.world.standing_cells():
            det = 0.0
            for w in watchers:
                d = max(1, abs(c[0]-w.pos[0]), abs(c[1]-w.pos[1]))
                if d <= R["beam_range"] \
                        and self._angle_off_facing(w, c) < R["beam_halfangle"] \
                        and self.world.los(w.pos, c):
                    det += 4.0 / d
            cost[c] = 1.0 + R["lambda_obs"] * det * 50.0
        import heapq
        pq, dist, prev = [(0.0, start)], {start: 0.0}, {}
        while pq:
            dc, c = heapq.heappop(pq)
            if c == goal: break
            if dc > dist.get(c, 1e18): continue
            for n in self.world.steps_from(c):
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
