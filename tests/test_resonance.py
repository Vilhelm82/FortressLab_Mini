"""
The resonance battery — conformance tests for THE DEFAULT SYSTEM.

Each test proves one claim the proposal makes. Cross-channel calibration
(exactly how much louder 'looking' is than 'hearing') is a balance knob, not
a conformance property; these tests pin the STRUCTURE — silences, orderings
within a channel, gradients, fold behaviour — never the constants.
"""

import pytest

from fortresslab_mini.config_balance import RESONANCE as R
from fortresslab_mini.resonance import (
    CompanyPart, Emitter, Field, Grid, WanderingUnit, attraction,
    dyad_specifier, extension, follow_target, leader_note, region_root)


# ---------------------------------------------------------------- 1. field
def test_superposition_is_order_independent_and_loops_close():
    g = Grid(12, 12)
    ems = [Emitter((2, 2), [region_root(0)], sign=+1),
           Emitter((9, 3), [region_root(5), dyad_specifier(5, 2)], sign=-1),
           Emitter((5, 8), [leader_note(3)], sign=+1)]
    f1 = Field(g, ems)
    f2 = Field(g, list(reversed(ems)))
    probe = (6, 6)
    assert f1.hear(probe) == f2.hear(probe)

    # closed loop: accumulated per-band deltas must vanish exactly
    loop = [(4, 4), (5, 4), (6, 5), (6, 6), (5, 7), (4, 6), (4, 5), (4, 4)]
    acc = {}
    prev = f1.hear(loop[0])
    for cell in loop[1:]:
        cur = f1.hear(cell)
        for k in set(prev) | set(cur):
            acc[k] = acc.get(k, 0.0) + cur.get(k, 0.0) - prev.get(k, 0.0)
        prev = cur
    assert all(abs(v) < 1e-12 for v in acc.values()), "loop residual nonzero"


# ------------------------------------------------------- 2. echolocation
def test_navigates_to_empty_post_and_db_gate_costs_resolution():
    g = Grid(30, 8)
    locs = [Emitter((27, 2), [region_root(0), dyad_specifier(0, 0)]),
            Emitter((27, 4), [region_root(4), dyad_specifier(4, 3)]),
            Emitter((27, 6), [region_root(9), dyad_specifier(9, 5)])]
    unit = Emitter((1, 4), [region_root(4), dyad_specifier(4, 3)], db=1.0)
    f = Field(g, locs)
    assert f.navigate_target(unit, locs) is locs[1]
    strength, layers = f.ping(unit, locs)[locs[1]]
    assert "SPEC" in layers, "full voice resolves the dyad at range"

    quiet = Emitter((1, 4), [region_root(4), dyad_specifier(4, 3)], db=0.05)
    strength_q, layers_q = f.ping(quiet, locs)[locs[1]]
    assert "LOC" in layers_q and "SPEC" not in layers_q, \
        "gated voice navigates on bass alone — stealth costs resolution"


# ------------------------------------------------- 3. handoff / fold-out
def test_unit_follows_leader_then_folds_out_to_the_post():
    g = Grid(32, 9)
    post = Emitter((28, 4), [region_root(7)])
    leader = Emitter((5, 4), [leader_note(7)])
    f = Field(g, [post, leader])
    unit_pos, first_target, folded_tick = (2, 4), None, None
    lp = list(leader.pos)
    for t in range(80):
        leader.pos = tuple(lp)
        f._dists.pop(tuple(lp), None)
        tgt = follow_target(f, Emitter(unit_pos, []), leader, post)
        if first_target is None:
            first_target = tgt
        if tgt == post.pos and folded_tick is None:
            folded_tick = t
        step = (min(1, max(-1, tgt[0]-unit_pos[0])),
                min(1, max(-1, tgt[1]-unit_pos[1])))
        unit_pos = (unit_pos[0]+step[0], unit_pos[1]+step[1])
        if lp[0] < post.pos[0] - 2:          # the choir marches too
            lp[0] += 1
        if unit_pos == post.pos:
            break
    assert first_target == (5, 4), "starts by following the leader"
    assert folded_tick is not None, "the deeper root eventually drowns him out"
    assert unit_pos == post.pos, "ends at the post, not on the sergeant"


# ------------------------------------- 4. inversion cascade -> fold-in
def test_cascade_strips_roots_then_stray_folds_into_matching_company():
    u = WanderingUnit((0, 0),
                      [region_root(2), dyad_specifier(2, 1), extension(2, 4)],
                      leaderless=True)
    seq = [u.root]
    for _ in range(200):
        before = u.root
        u.tick_filter()
        if u.root != before:
            seq.append(u.root)
        if u.root is None or u.root[0] == "SPEC":
            break
    assert [n[0] for n in seq[:2]] == ["LOC", "SPEC"], \
        "the root slot shifts upward as the filter climbs"

    matching = {"parts": [CompanyPart([u.root, extension(2, 4)], 3, 1)]}
    nearer_wrong = {"parts": [CompanyPart([region_root(11)], 3, 0)]}
    assert attraction(u.root, [nearer_wrong, matching]) is matching, \
        "root+dyad is the dissonance barrier — strays drift to matching roles"


# --------------------------------------------- 5. under-strength pull
def test_hollow_company_attracts_before_full_one():
    root = dyad_specifier(6, 2)
    full = {"parts": [CompanyPart([root], 3, 3)]}
    hollow = {"parts": [CompanyPart([root], 3, 1)]}
    assert attraction(root, [full, hollow]) is hollow
    assert attraction(root, [full]) is None, "a complete chord cannot resolve"


# ------------------------------------------------ 6. detection channels
def test_channel_structure_rear_silence_and_priority():
    g = Grid(20, 10)
    shared = region_root(3)
    observer = Emitter((5, 5), [shared], facing=(1, 0))
    away_facing = Emitter((11, 5), [shared], sign=-1, facing=(1, 0))
    f = Field(g, [observer, away_facing])
    ch = f.channels(observer, away_facing)
    assert ch["being_looked_at"] == 0.0, "a beam striking at 180 deg is silent"
    assert ch["looking"] > 0 and ch["interference"] > 0 and ch["hearing"] > 0

    toward = Emitter((11, 5), [shared], sign=-1, facing=(-1, 0))
    ch2 = Field(g, [observer, toward]).channels(observer, toward)
    assert ch2["being_looked_at"] > 0.0, "a beam on your face is felt"

    behind = Emitter((1, 5), [shared], sign=-1, facing=(1, 0))
    fb = Field(g, [observer, behind])
    assert fb.channels(observer, behind)["hearing"] < ch["hearing"], \
        "hearing ratio is weakest toward 180 deg"

    strong = Emitter((7, 5), [shared], sign=-1, numbers=4)
    weak = Emitter((7, 7), [shared], sign=-1, numbers=1)
    fp = Field(g, [observer, strong, weak])
    assert fp.priority_target(observer, [weak, strong]) is strong, \
        "the stronger cancellation source is the offensive priority"

    stranger = Emitter((11, 5), [region_root(9)], sign=-1)
    assert Field(g, [observer, stranger]).channels(observer, stranger)[
        "interference"] == 0.0, "no shared bands, no cancellation"


# ------------------------------------------------------------ 7. masking
def test_masking_hides_the_quiet_beside_noise_and_exposes_it_in_silence():
    g = Grid(20, 10)
    listener = Emitter((10, 5), [region_root(0)], facing=(-1, 0))
    sneak = Emitter((4, 5), [region_root(8)], sign=-1, db=0.02, facing=(1, 0))
    racket = Emitter((11, 5), [leader_note(1)], numbers=6)
    noisy = Field(g, [listener, sneak, racket])
    assert noisy.channels(listener, sneak)["hearing"] == 0.0, \
        "buried beside the racket"
    silent = Field(g, [listener, sneak])
    assert silent.channels(listener, sneak)["hearing"] > 0.0, \
        "in silence even a whisper eventually draws focus"


# ------------------------------------- 8. least-detection covered route
def test_routing_bends_around_the_watchers_beam():
    g = Grid(21, 13)
    watcher = Emitter((10, 10), [], facing=(0, -1))   # looking north
    f = Field(g, [watcher])
    start, goal = (2, 2), (18, 2)
    path = f.least_detection_route(start, goal, [watcher])

    def in_beam(c):
        d = max(1, abs(c[0]-10), abs(c[1]-10))
        return (d <= R["beam_range"] and g.los(watcher.pos, c)
                and f._angle_off_facing(watcher, c) < R["beam_halfangle"])

    assert any(in_beam((x, 2)) for x in range(7, 14)), \
        "sanity: the straight line WOULD cross the beam"
    assert path and path[-1] == goal
    assert not any(in_beam(c) for c in path), \
        "the chosen route stays out of the cone with nothing coding sneaking"


# ---------------------------------- 9. the 72 addresses, stone, timber
def _ring_cells(cx, cy, r):
    cells = []
    for x in range(cx-r, cx+r+1):
        cells += [(x, cy-r), (x, cy+r)]
    for y in range(cy-r+1, cy+r):
        cells += [(cx-r, y), (cx+r, y)]
    return sorted(set(cells))


def test_all_72_addresses_resolve_and_stone_hides_the_dyad():
    cx = cy = 10
    ring = _ring_cells(cx, cy, 9)
    assert len(ring) == 72
    locs = []
    i = 0
    for region in range(12):
        for degree in range(6):
            locs.append(Emitter(ring[i],
                                [region_root(region),
                                 dyad_specifier(region, degree)]))
            i += 1
    g_open = Grid(21, 21)
    f = Field(g_open, locs)
    for region in (0, 5, 11):
        for degree in (0, 3, 5):
            u = Emitter((cx, cy),
                        [region_root(region), dyad_specifier(region, degree)])
            got = f.navigate_target(u, locs)
            want = locs[region*6 + degree]
            assert got is want, f"address ({region},{degree}) misresolved"

    stone = Grid(21, 21, stone=_ring_cells(cx, cy, 5))
    fs = Field(stone, locs)
    u = Emitter((cx, cy), [region_root(3), dyad_specifier(3, 2)])
    _, layers = fs.ping(u, locs)[locs[3*6 + 2]]
    assert layers == {"LOC"}, "stone gives away the region, hides the post"
    a = fs.ping(u, locs)[locs[3*6 + 2]][0]
    u_other = Emitter((cx, cy), [region_root(3), dyad_specifier(3, 4)])
    b = fs.ping(u_other, locs)[locs[3*6 + 4]][0]
    assert abs(a - b) < 1e-12, "behind stone, two dyads of one region tie"

    timber = Grid(21, 21, timber=_ring_cells(cx, cy, 5))
    ft = Field(timber, locs)
    _, layers_t = ft.ping(u, locs)[locs[3*6 + 2]]
    assert "SPEC" in layers_t, "timber leaks the position"
