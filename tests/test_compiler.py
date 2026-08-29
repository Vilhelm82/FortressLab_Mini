"""
Compiler conformance — the grammar and the performance must agree.

The decisive exams run BOTH systems against one scripted world and assert
they release on the SAME tick. That is what "compilation is faithful" means.
The legality exams assert what cannot be sung is refused, by name.
"""

import pytest

from fortresslab_mini.compiler import (AddressBook, CompileError,
                                       PerformanceState, compile_order)
from fortresslab_mini.orders import (OrderExec, clock_at_or_after, contact,
                                     losses_at_least, spent)
from fortresslab_mini.resonance import dyad_specifier, region_root

BOOK = AddressBook([
    {"area": (0, 0, 9, 9),   "posts": [(2, 2), (7, 2), (5, 8)]},   # region 0
    {"area": (10, 0, 19, 9), "posts": [(12, 3), (17, 7)]},          # region 1
])


def world(clock=0, elapsed=0, counts=None, losses=0, initial=10, ammo=5,
          hazards=None):
    return {"clock": clock, "elapsed": elapsed,
            "count": counts or {}, "hazard": hazards or {},
            "self": {"losses": losses, "initial": initial, "ammo": ammo,
                     "strength": initial - losses}}


def simple(scope_area, release_edges):
    sc = {"kinds": {"defend", "move"}, "area": scope_area}
    return {"scope": sc, "start": "hold",
            "nodes": {"hold": {"scope": sc, "edges": []}},
            "global_edges": release_edges}


# ------------------------------------------------------- legality filter
def test_clock_guard_cannot_be_sung():
    order = simple((1, 1, 4, 4), [
        {"when": clock_at_or_after(10), "release": "timeout"},
        {"when": losses_at_least(1, 2), "release": "return"}])
    with pytest.raises(CompileError, match="clock.*scrapped"):
        compile_order(order, BOOK)


def test_elapsed_guard_cannot_be_sung():
    order = simple((1, 1, 4, 4), [
        {"when": ("ge", ("elapsed",), 30), "release": "waited"},
        {"when": losses_at_least(1, 2), "release": "return"}])
    with pytest.raises(CompileError, match="elapsed"):
        compile_order(order, BOOK)


def test_the_six_layer_cap_is_enforced():
    edges = [{"when": contact("enemy", "here", n), "release": f"r{n}"}
             for n in range(1, 8)]
    edges.append({"when": losses_at_least(1, 2), "release": "return"})
    with pytest.raises(CompileError, match="caps complexity"):
        compile_order(simple((1, 1, 4, 4), edges), BOOK)


# --------------------------------------------------------- addressing
def test_address_resolution_post_and_region_level():
    perf = compile_order(simple((6, 1, 8, 3), [
        {"when": losses_at_least(1, 2), "release": "return"}]), BOOK)
    p = perf["parts"][0]
    assert (p["region"], p["degree"]) == (0, 1), "nearest post wins"
    assert p["tuning"] == [region_root(0), dyad_specifier(0, 1)]

    perf2 = compile_order(simple((0, 0, 9, 9), [
        {"when": losses_at_least(1, 2), "release": "return"}]), BOOK)
    p2 = perf2["parts"][0]
    assert p2["degree"] is None and p2["tuning"] == [region_root(0)], \
        "an order covering the whole region tunes the bass alone"


def test_recall_is_new_sheet_music_not_a_note():
    perf = compile_order(simple((1, 1, 4, 4), [
        {"when": contact("messenger"), "release": "recalled"},
        {"when": losses_at_least(1, 2), "release": "return"}]), BOOK)
    assert perf["recall_via_messenger"] is True
    assert len(perf["parts"][0]["notes"]) == 1, \
        "the messenger clause compiles to no extension"


# ------------------------------------------------- conformance: attrition
def test_canonical_order_releases_on_the_same_tick_in_both_systems():
    order = simple((1, 1, 4, 4), [
        {"when": contact("messenger"), "release": "recalled"},
        {"when": losses_at_least(1, 2), "release": "return"}])
    ex = OrderExec(order)
    ps = PerformanceState(compile_order(order, BOOK)["parts"][0])
    script = [world(losses=k) for k in (0, 1, 2, 4, 5, 6)]
    g_tick = r_tick = None
    for t, w in enumerate(script):
        if g_tick is None and ex.step(w):
            g_tick = t
        if r_tick is None and ps.step(w):
            r_tick = t
    assert g_tick == r_tick == 4, "half losses fires both at tick 4"


# -------------------------------- conformance: Will's gate example (§13)
def test_gate_example_two_companies_release_in_order_on_both_systems():
    gate = (1, 1, 4, 4)
    b_order = simple(gate, [
        {"when": contact("enemy", "assigned"), "release": "gate-lost"},
        {"when": losses_at_least(1, 2), "release": "return"}])
    a_order = simple(gate, [
        {"when": ("and", contact("enemy", "assigned"), spent("ammo")),
         "release": "gate-lost-and-dry"},
        {"when": losses_at_least(1, 2), "release": "return"}])

    exb, exa = OrderExec(b_order), OrderExec(a_order)
    psb = PerformanceState(compile_order(b_order, BOOK)["parts"][0])
    psa = PerformanceState(compile_order(a_order, BOOK)["parts"][0])

    script = [world() for _ in range(4)]
    script += [world(counts={("enemy", "assigned"): 3})]           # t4 gate
    script += [world(counts={("enemy", "assigned"): 3})] * 3
    script += [world(counts={("enemy", "assigned"): 3}, ammo=0)]   # t8 dry

    ticks = {}
    for t, w in enumerate(script):
        for name, m in (("gB", exb), ("gA", exa), ("rB", psb), ("rA", psa)):
            if name not in ticks and m.step(w):
                ticks[name] = t
    assert ticks["gB"] == ticks["rB"] == 4, "B releases when the 5th dies"
    assert ticks["gA"] == ticks["rA"] == 8, \
        "A holds until gate lost AND out of ammo — the 7th"
    a_note = compile_order(a_order, BOOK)["parts"][0]["notes"][0]
    assert len(a_note["conditions"]) == 2, "AND compiles to ONE note"


# ------------------------------------------------------ parts (§31)
def test_detachment_compiles_to_its_own_part_with_its_own_address():
    gate_sc = {"kinds": {"defend", "move"}, "area": (1, 1, 4, 4)}
    route_sc = {"kinds": {"move"}, "area": (11, 1, 13, 5)}
    sub = {"scope": route_sc, "start": "clear",
           "nodes": {"clear": {"scope": route_sc, "edges": []}},
           "global_edges": [{"when": losses_at_least(1, 2),
                             "release": "return"}]}
    order = {"scope": {"kinds": {"defend", "move"}, "area": (0, 0, 19, 9)},
             "start": "hold",
             "nodes": {"hold": {"scope": gate_sc, "edges": [
                 {"when": contact("enemy", "here"),
                  "detach": {"n": 2, "order": sub, "goto": "hold2"}}]},
                 "hold2": {"scope": gate_sc, "edges": []}},
             "global_edges": [{"when": losses_at_least(1, 2),
                               "release": "return"}]}
    perf = compile_order(order, BOOK)
    assert len(perf["parts"]) == 2
    company, part = perf["parts"]
    assert company["filter"] == ("company", None) and company["region"] == 0
    assert part["filter"] == ("count", 2) and part["region"] == 1, \
        "two men, addressed by count never identity, singing region 1"
    assert part["notes"][0]["note"] != company["notes"][0]["note"] or \
        part["region"] != company["region"], "distinct extension voices"
