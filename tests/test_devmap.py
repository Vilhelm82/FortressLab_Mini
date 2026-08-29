"""
The development map — the fixture stays honest.

These tests do not test the map's beauty; they pin the properties every other
subsystem will lean on. If someone edits the geometry, these say what broke.
"""

from collections import deque

from fortresslab_mini.devmap import (CASTLE, GATE_Y, KEEP_DOOR, POCKET,
                                     REGIONS, ROWS, SPUR_X, SPUR_Y, WAR_ROOM,
                                     H, W, material_cells, worldmap)
from fortresslab_mini.resonance import Emitter, Field, Grid, region_root

SOLID = set("#234=G")


def open_cells():
    return {(x, y) for y, r in enumerate(ROWS) for x, c in enumerate(r)
            if c not in SOLID}


def reach(start, passable):
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)):
            n = (x + dx, y + dy)
            if n in passable and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def test_shape_and_legend():
    assert len(ROWS) == H and all(len(r) == W for r in ROWS)
    assert set("".join(ROWS)) <= SOLID | set(".ST")


def test_the_castle_is_sealed_until_something_is_breached():
    """Gates are shut. There is no walk-in: the attacker must breach, scale,
    or open something. This is the property the whole siege rests on."""
    passable = open_cells()
    x0, y0, x1, y1 = CASTLE
    interior = {(x, y) for x in range(x0 + 1, x1) for y in range(y0 + 1, y1)}
    assert not (reach((2, 2), passable) & interior), "sealed"

    forced = passable | {(12, GATE_Y[0]), (12, GATE_Y[1])}
    assert reach((2, 2), forced) & interior, \
        "and opening the gate lets him in — the gate is the cheap edge"


def test_the_war_room_is_reachable_only_through_the_keep_door():
    passable = open_cells()
    bailey = (20, 5)
    assert WAR_ROOM in reach(bailey, passable), "reachable from the bailey"
    assert WAR_ROOM not in reach(bailey, passable - {KEEP_DOOR}), \
        "the keep has exactly one way in"


def test_the_gate_opens_into_a_cul_de_sac():
    """Anything that comes through the main gate is in a box whose only exit
    is north, past the spur."""
    passable = open_cells()
    inside_gate = (13, GATE_Y[0])
    passable = passable | {(12, GATE_Y[0]), (12, GATE_Y[1])}   # gate forced
    x0, y0, x1, y1 = POCKET
    pocket = {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)
              if (x, y) in passable}
    assert inside_gate in pocket

    # The pocket's only exit is north, over the top of the spur. Seal that
    # gap and anything inside is stranded in the box.
    mouth = {(x, y) for x in range(x0, SPUR_X + 1)
             for y in range(POCKET[1], SPUR_Y[0])}
    sealed = passable - mouth
    assert not (reach(inside_gate, sealed) & {WAR_ROOM}), \
        "with the mouth shut, the gate leads nowhere"
    assert reach(inside_gate, passable) & {WAR_ROOM}, \
        "and the long way round exists"


def test_height_is_varied_not_flat():
    """Varied height is the sole source of cover (ruled). The fixture must
    supply it: towers 3, curtain 2, spur 1, keep 4."""
    wm = worldmap()
    heights = {wm.height[y][x] for y in range(H) for x in range(W)
               if wm.height[y][x]}
    assert heights == {1, 2, 3, 4}, heights
    assert wm.height[2][12] == 3, "north-west tower"
    assert wm.height[3][12] == 2, "curtain between towers"
    assert wm.height[6][SPUR_X] == 1, "the spur is a low internal wall"
    assert wm.height[8][26] == 4, "the keep is the tallest thing standing"


def test_both_materials_are_present_and_separable():
    stone, timber = material_cells()
    assert timber, "the south wall's palisade stretch"
    assert len(timber) == 8
    assert stone and not (stone & timber)
    assert all(ROWS[y][x] == "=" for x, y in timber)


def test_timber_leaks_the_dyad_where_stone_does_not():
    """The material contrast the fixture exists to provide: identical
    geometry, different transmission."""
    stone, timber = material_cells()
    g = Grid(W, H, stone=stone, timber=timber)
    post = Emitter((28, 16), [region_root(3)])          # inside, near the wall
    f = Field(g, [post])

    outside_timber = (28, 21)                            # beyond the palisade
    outside_stone = (16, 21)                             # beyond stone wall
    a = abs(f.hear(outside_timber).get(region_root(3), 0.0))
    b = abs(f.hear(outside_stone).get(region_root(3), 0.0))
    assert a > b, "timber transmits more of the bass than stone"


def test_twelve_regions_all_lie_on_the_map_and_do_not_overlap():
    assert len(REGIONS) == 12, "twelve fundamentals, twelve regions"
    seen = {}
    for name, rects in REGIONS.items():
        for (x0, y0, x1, y1) in rects:
            assert 0 <= x0 <= x1 < W and 0 <= y0 <= y1 < H, name
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    assert (x, y) not in seen, "%s overlaps %s at %r" % (
                        name, seen.get((x, y)), (x, y))
                    seen[(x, y)] = name


def test_the_field_is_open_ground():
    passable = open_cells()
    field = {(x, y) for x in range(0, 12) for y in range(H)}
    assert field <= passable, "the approach is open ground, no cover given"
