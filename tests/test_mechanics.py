"""
Mechanics over time — the first tests where resonance actually runs.

Every scenario is hand-placed on the development castle. No commander, no
orders: a location is tuned, units hear it, and we watch what happens.
"""

from fortresslab_mini.devmap import GATE_Y, REGIONS, WAR_ROOM, H, W, \
    material_cells
from fortresslab_mini.resonance import (Emitter, Grid, WanderingUnit,
                                        dyad_specifier, leader_note,
                                        region_root)
from fortresslab_mini.stepper import (DEAD, Mover, Stepper,
                                      chase_strongest_canceller,
                                      follow_then_fold, hold, seek_harmony,
                                      sneak_to)

STONE, TIMBER = material_cells()


def grid():
    return Grid(W, H, stone=STONE, timber=TIMBER)


def post(xy, region, degree):
    return Emitter(xy, [region_root(region), dyad_specifier(region, degree)])


# ------------------------------------------------------------ 1. it walks
def test_a_unit_marches_to_the_post_it_harmonises_with():
    bailey = post((22, 5), 4, 1)
    decoy = post((22, 17), 9, 3)
    unit = Mover(Emitter((20, 10), bailey.notes),
                 goal=seek_harmony([bailey, decoy]), name="man")
    s = Stepper(grid(), [unit], statics=[bailey, decoy])
    s.run(40, until=lambda st: unit.pos == bailey.pos)
    assert unit.pos == bailey.pos, unit.path[-5:]
    assert len(unit.path) > 1, "it actually moved"


def test_it_walks_around_stone_not_through_it():
    """The keep's wall stands between the unit and the war room; the only
    way in is the south door at (28,12)."""
    inside = post(WAR_ROOM, 11, 0)
    unit = Mover(Emitter((28, 5), inside.notes),
                 goal=seek_harmony([inside]), name="man")
    s = Stepper(grid(), [unit], statics=[inside])
    s.run(60, until=lambda st: unit.pos == WAR_ROOM)
    assert unit.pos == WAR_ROOM
    assert (28, 12) in unit.path, "it used the door"
    assert all(p not in STONE for p in unit.path), "never walked through wall"


# --------------------------------------------------- 2. the choir handoff
def test_company_follows_its_leader_then_folds_out_to_the_post():
    tower = post((32, 3), 6, 2)
    leader = Mover(Emitter((14, 4), [leader_note(6)]), name="sergeant")
    leader.goal = lambda m, f, w: tower.pos
    man = Mover(Emitter((13, 4), []), name="man")
    man.goal = follow_then_fold(leader, tower)
    s = Stepper(grid(), [leader, man], statics=[tower])

    followed = folded = None
    for t in range(80):
        f = s.field()
        la = sum(f._amp(leader.e, n, man.pos) for n in leader.e.notes)
        ra = sum(f._amp(tower, n, man.pos) for n in tower.notes)
        if followed is None and la > ra:
            followed = t
        if followed is not None and folded is None and ra >= la:
            folded = t
        s.step()
        if man.pos == tower.pos:
            break
    assert followed == 0, "he sets off after the sergeant"
    assert folded is not None, "the deeper root eventually takes over"
    assert man.pos == tower.pos, "and he ends on the post, not on the man"


def test_when_the_leader_dies_the_company_carries_on_to_the_post():
    tower = post((32, 3), 6, 2)
    leader = Mover(Emitter((14, 4), [leader_note(6)]), name="sergeant")
    leader.goal = lambda m, f, w: tower.pos
    man = Mover(Emitter((13, 4), []), name="man")
    man.goal = follow_then_fold(leader, tower)
    s = Stepper(grid(), [leader, man], statics=[tower])
    s.run(6)
    leader.kill()
    s.run(80, until=lambda st: man.pos == tower.pos)
    assert man.pos == tower.pos, "orders outlive the officer"


# ------------------------------------------------ 3. the inversion cascade
def test_a_leaderless_man_degrades_and_ends_holding_only_a_root():
    u = WanderingUnit((20, 10),
                      [region_root(4), dyad_specifier(4, 1)], leaderless=True)
    roots = []
    for _ in range(120):
        r = u.root
        if not roots or roots[-1] != r:
            roots.append(r)
        u.tick_filter()
        if u.root is None:
            break
    assert [r[0] for r in roots[:2]] == ["LOC", "SPEC"], \
        "the dyad shifts up into the root slot when the filter eats the root"
    assert roots[-1] is None or len(roots) >= 2


# --------------------------------------------------------- 4. two sides
def test_opposed_units_close_and_kill_each_other():
    """Bloodlust as physics: each hears the other cancelling and closes."""
    shared = [region_root(2)]
    home = Mover(Emitter((18, 17), shared, sign=+1), name="home")
    away = Mover(Emitter((26, 17), shared, sign=-1), name="away")
    home.goal = chase_strongest_canceller([away])
    away.goal = chase_strongest_canceller([home])
    s = Stepper(grid(), [home, away])
    s.run(40, until=lambda st: home.state == DEAD or away.state == DEAD)
    assert home.state == DEAD and away.state == DEAD, "the dead short"
    assert any(e[2] == "killed" for e in s.log)


def test_the_stronger_canceller_wins_the_focus():
    shared = [region_root(2)]
    home = Mover(Emitter((20, 16), shared, sign=+1), name="home")
    weak = Mover(Emitter((20, 10), shared, sign=-1, numbers=1), name="weak")
    strong = Mover(Emitter((24, 16), shared, sign=-1, numbers=6),
                   name="strong")
    weak.goal = strong.goal = hold
    home.goal = chase_strongest_canceller([weak, strong])
    s = Stepper(grid(), [home, weak, strong])
    s.run(4)
    assert home.pos[0] > 20, "he turned toward the strong one, not the near one"


# ------------------------------------------------------ 5. sneaking
def test_a_sneak_crosses_the_field_avoiding_the_watchers_cone():
    """Least detection over real ground: the tower watches the direct line."""
    watcher = Mover(Emitter((12, 10), [], facing=(-1, 0)), goal=hold,
                    name="watchman")
    sneak = Mover(Emitter((2, 10), [region_root(0)], sign=-1, db=0.05),
                  name="sneak")
    dest = (2, 20)
    sneak.goal = sneak_to(dest, [watcher])
    s = Stepper(grid(), [sneak, watcher])
    s.run(40, until=lambda st: sneak.pos == dest)
    assert sneak.pos == dest
    f = s.field()
    seen = [p for p in sneak.path
            if f.channels(watcher.e, Emitter(p, sneak.e.notes))["looking"] > 0]
    straight = [(2, y) for y in range(10, 21)]
    seen_straight = [p for p in straight
                     if f.channels(watcher.e,
                                   Emitter(p, sneak.e.notes))["looking"] > 0]
    assert len(seen) <= len(seen_straight), \
        "the chosen route is no more exposed than the straight one"


# ----------------------------------------------- 6. the gate is a killbox
def test_what_comes_through_the_gate_is_in_a_box():
    """Geometry and resonance together: a unit forced through the gate has
    only one way on, and it walks it."""
    g = grid()
    g.stone = set(g.stone) - {(12, GATE_Y[0])}          # gate forced open
    bailey = post((24, 6), 5, 2)
    intruder = Mover(Emitter((11, GATE_Y[0]), bailey.notes, sign=-1),
                     goal=seek_harmony([bailey]), name="intruder")
    s = Stepper(g, [intruder], statics=[bailey])
    s.run(80, until=lambda st: intruder.pos == bailey.pos)
    assert intruder.pos == bailey.pos
    ys = [p[1] for p in intruder.path if p[0] <= 18]
    assert min(ys) <= 5, "he had to go north over the spur to get out"
