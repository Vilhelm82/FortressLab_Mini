"""
Map ladder — progressively more complex maps, as ruled: confirm the pipeline
on the simplest test before expanding with more layers.

M0  flat ground        -> straight line, cost = pure travel = Chebyshev
M1a expensive wall     -> walks around (zero breach ticks)
M1b cheap palisade     -> digs through (breach beats detour)
M2  wall + gate        -> undefended: takes the gate
M2d wall + gate + bows -> covered gate repriced: goes through the dark instead
M3  sealed enclosure   -> circles to the least-covered face, unprompted

FINDINGS recorded during calibration (both were test-design errors, not
planner errors -- the field out-argued the author three times on M3):
  * gates are transparent to arrows, so a gate archer covers the whole
    approach lane through his own gate (awaiting ruling)
  * a courtyard shallower than bow range flattens entry choice: the interior
    tax is the same from every breach point, so WHERE you enter stops
    mattering. Depth is what makes entry a decision.
"""

from fortresslab_mini.worldmap import WorldMap, GATE
from fortresslab_mini.enemy_brain import plan


def solve_map(rows):
    wm = WorldMap(rows)
    return wm, plan(wm)


def gate_on_path(wm, result):
    return any(wm.cell[y][x] == GATE for x, y in result["path"])


M0 = [
    "S..........",
    "...........",
    "...........",
    "..........T",
]

M1A = [
    "....#......",
    "....#......",
    "S...#.....T",
    "....#......",
    "...........",
]

M1B = [
    "....=......",
    "....=......",
    "S...=.....T",
    "....=......",
    "....=......",
    "....=......",
    "....=......",
    "....=......",
    "....=......",
]

M2 = [
    ".....#.....",
    ".....#.....",
    "S....G....T",
    ".....#.....",
    ".....#.....",
]

M2D = [
    "S....#....T",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    ".....G.A...",
    "...........",
]

M3 = [
    "...................",
    "...#############...",
    "...#.....T.....#...",
    "...#...........#...",
    "...#...........#...",
    "...#...........#...",
    "...#...........#...",
    "...#...........#...",
    "...####W#G#W####...",
    "...................",
    "...................",
    ".........S.........",
]


def test_M0_cost_is_pure_travel():
    _, r = solve_map(M0)
    assert r["report"]["breach"] == 0
    assert r["report"]["exposure"] == 0


def test_M0_travel_equals_chebyshev():
    _, r = solve_map(M0)
    assert r["report"]["travel"] == 10


def test_M1a_walks_around_stone():
    """Detour is cheaper than 40 ticks of masonry — no rule says so."""
    _, r = solve_map(M1A)
    assert r["report"]["breach"] == 0


def test_M1b_digs_through_timber():
    """Same geometry, cheaper material: the decision flips on the numbers."""
    _, r = solve_map(M1B)
    assert r["report"]["breach"] > 0


def test_M2_takes_the_undefended_gate():
    wm, r = solve_map(M2)
    assert gate_on_path(wm, r)
    assert r["report"]["breach"] == 10


def test_M2d_abandons_the_covered_gate():
    wm, r = solve_map(M2D)
    assert not gate_on_path(wm, r)


def test_M2d_pays_stone_instead_of_arrows():
    _, r = solve_map(M2D)
    assert r["report"]["breach"] >= 40
    assert r["report"]["exposure"] == 0


def test_M3_breaches_somewhere():
    _, r = solve_map(M3)
    assert len(r["report"]["entries"]) >= 1


def test_M3_circles_to_the_dark_north_face():
    """The whole thesis in one assertion: it walks the long way round because
    the short way is covered. Nobody wrote 'avoid archers'."""
    _, r = solve_map(M3)
    assert all(y <= 2 for _, y in r["report"]["entries"])


def test_M3_ignores_the_covered_gate():
    wm, r = solve_map(M3)
    assert not gate_on_path(wm, r)


def test_M3_conductance_ranking_agrees():
    """The independent breach ranking picks the same face as the path."""
    _, r = solve_map(M3)
    assert r["breach_ranking"][0][1][1] <= 2
