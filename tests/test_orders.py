"""
Orders rung battery — generalised doctrine.

Tested as pure state machines: no AI authors anything. Scripted worlds drive
every transition. The law, tested before the lawyers.

The closure test at the bottom is the point of the refactor: a situation
nobody anticipated (a burning gatehouse, an ammo-dry archer company) is
expressible with ZERO changes to the grammar.
"""

import pytest

from fortresslab_mini.orders import (
    validate_order, order_size, OrderExec, MalformedOrder,
    company_status, try_rally, eval_guard,
    ORDERED, STALE, FERAL, AWAITING,
    contact, absent, losses_at_least, clock_at_or_after, spent, hazard_in)

AREA = (0, 0, 30, 10)
HOLD = (0, 0, 10, 10)


def scope(kinds, area=AREA):
    return {"kinds": set(kinds), "area": area}


def W(clock=9, elapsed=0, strength=9, initial=9, losses=0, ammo=20,
      counts=None, hazards=None):
    return {"clock": clock, "elapsed": elapsed,
            "self": {"strength": strength, "initial": initial,
                     "losses": losses, "ammo": ammo},
            "count": counts or {}, "hazard": hazards or {}}


def clear_routes_suborder():
    return {
        "scope": scope({"move", "clear_route"}),
        "start": "clear",
        "nodes": {"clear": {"scope": scope({"move", "clear_route"}), "edges": [
            {"when": contact("messenger"), "release": "contact_made"}]}},
        "global_edges": [{"when": losses_at_least(1, 2), "release": "return"}],
    }


def ten_am_order():
    """Will's contingency draft, composed from the general grammar."""
    return {
        "scope": scope({"defend", "move", "clear_route"}),
        "start": "hold",
        "nodes": {
            "hold": {"scope": scope({"defend"}, HOLD), "edges": [
                {"when": contact("messenger"), "release": "recalled"},
                {"when": ("and", clock_at_or_after(11), absent("enemy")),
                 "release": "return"},
                {"when": ("and", clock_at_or_after(11), contact("enemy")),
                 "detach": {"n": 2, "order": clear_routes_suborder(),
                            "goto": "hold_reduced"}},
            ]},
            "hold_reduced": {"scope": scope({"defend"}, HOLD), "edges": [
                {"when": contact("messenger"), "release": "recalled"}]},
        },
        "global_edges": [{"when": losses_at_least(1, 2), "release": "return"}],
    }


ENEMY_HERE = {("enemy", "here"): 3}
MSG_HERE = {("messenger", "here"): 1}


def test_bare_hold_is_malformed():
    bare = {"scope": scope({"defend"}), "start": "h",
            "nodes": {"h": {"scope": scope({"defend"}, HOLD), "edges": []}}}
    ok, why = validate_order(bare)
    assert not ok and any("no release" in p for p in why)


def test_until_recalled_alone_is_malformed():
    o = {"scope": scope({"defend"}), "start": "h",
         "nodes": {"h": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": contact("messenger"), "release": "recalled"}]}}}
    ok, why = validate_order(o)
    assert not ok and any("self-triggerable" in p for p in why)


def test_recalled_or_half_losses_validates():
    o = {"scope": scope({"defend"}), "start": "h",
         "nodes": {"h": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": contact("messenger"), "release": "recalled"}]}},
         "global_edges": [{"when": losses_at_least(1, 2), "release": "return"}]}
    ok, why = validate_order(o)
    assert ok, why


def test_release_on_unobservable_region_is_malformed():
    o = {"scope": scope({"defend"}), "start": "h",
         "nodes": {"h": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": contact("enemy", "far_gate"), "release": "done"}]}}}
    ok, why = validate_order(o)
    assert not ok and any("cannot observe" in p for p in why)


def test_will_10am_order_validates_and_fits_a_sergeant():
    o = ten_am_order()
    ok, why = validate_order(o, rank="sergeant")
    assert ok, why
    assert order_size(o) <= 8


def test_detach_outside_parent_scope_is_refused():
    o = ten_am_order()
    o["nodes"]["hold"]["edges"][2]["detach"]["order"]["scope"]["area"] = \
        (0, 0, 100, 100)
    ok, why = validate_order(o)
    assert not ok and any("exceeds parent scope" in p for p in why)


def test_capacity_bounds_granularity():
    edges = [{"when": clock_at_or_after(h), "goto": "h"} for h in range(6, 15)]
    monster = {"scope": scope({"defend"}), "start": "h",
               "nodes": {"h": {"scope": scope({"defend"}, HOLD),
                               "edges": edges}},
               "global_edges": [{"when": losses_at_least(1, 2),
                                 "release": "return"}]}
    ok_s, why_s = validate_order(monster, rank="sergeant")
    ok_c, _ = validate_order(monster, rank="captain")
    assert not ok_s and any("capacity" in p for p in why_s)
    assert ok_c


def test_messenger_arrives_at_ten():
    ex = OrderExec(ten_am_order())
    assert ex.step(W(clock=9)) is None
    assert ex.step(W(clock=10, counts=MSG_HERE)) == ("release", "recalled")
    assert ex.can_retask()


def test_timeout_quiet_all_return():
    ex = OrderExec(ten_am_order())
    ex.step(W(clock=10))
    assert ex.step(W(clock=11)) == ("release", "return")


def test_timeout_in_contact_detaches_two():
    ex = OrderExec(ten_am_order())
    ex.step(W(clock=10, counts=ENEMY_HERE))
    ev = ex.step(W(clock=11, counts=ENEMY_HERE))
    assert ev[0] == "detach" and ev[1] == 2
    assert ex.node == "hold_reduced"
    _, sub = ex.detachments[0]
    assert sub.step(W(clock=11)) is None
    assert sub.step(W(clock=12, counts=MSG_HERE)) == ("release", "contact_made")


def test_half_losses_fires_from_any_node():
    ex = OrderExec(ten_am_order())
    ex.step(W(clock=11, counts=ENEMY_HERE))
    assert ex.node == "hold_reduced"
    assert ex.step(W(clock=12, counts=ENEMY_HERE, losses=5)) \
        == ("release", "return")


def test_order_lock_holds_until_release():
    ex = OrderExec(ten_am_order())
    assert not ex.can_retask()
    ex.step(W(clock=9))
    assert not ex.can_retask()
    ex.step(W(clock=10, counts=MSG_HERE))
    assert ex.can_retask()


def test_stale_orders_execute_unchanged():
    ex = OrderExec(ten_am_order())
    assert company_status(False, ex) == STALE
    assert ex.step(W(clock=11, counts=ENEMY_HERE))[0] == "detach"


def test_feral_requires_both_conditions():
    ex = OrderExec(ten_am_order())
    assert company_status(True, ex) == ORDERED
    assert company_status(False, ex) == STALE
    ex.step(W(clock=10, counts=MSG_HERE))
    assert company_status(True, ex) == AWAITING
    assert company_status(False, ex) == FERAL


def test_feral_rally_fills_open_slot():
    companies = [{"members": 9, "capacity": 9, "pos": (2, 2)},
                 {"members": 7, "capacity": 9, "pos": (4, 4)}]
    assert try_rally((5, 5), companies, 3) is companies[1]
    assert companies[1]["members"] == 8


def test_feral_out_of_detection_stays_feral():
    assert try_rally((20, 20),
                     [{"members": 5, "capacity": 9, "pos": (0, 0)}], 3) is None


def test_malformed_order_is_unissuable():
    with pytest.raises(MalformedOrder):
        OrderExec({"scope": scope({"defend"}), "start": "h",
                   "nodes": {"h": {"scope": scope({"defend"}, HOLD),
                                   "edges": []}}})


def test_unanticipated_situations_need_no_grammar_change():
    burning = ("and", hazard_in("fire"), clock_at_or_after(0))
    assert eval_guard(burning, W(hazards={("fire", "here"): 1}))
    assert not eval_guard(burning, W())

    dry = spent("ammo")
    assert eval_guard(dry, W(ammo=0))
    assert not eval_guard(dry, W(ammo=3))

    outnumbered = ("ratio_ge", ("count", "enemy", "here"),
                   ("self", "strength"), 3, 1)
    assert eval_guard(outnumbered, W(strength=4, counts={("enemy", "here"): 12}))
    assert not eval_guard(outnumbered,
                          W(strength=4, counts={("enemy", "here"): 8}))


def test_composed_doctrine_validates_as_an_order():
    o = {"scope": scope({"defend"}), "start": "h",
         "nodes": {"h": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": contact("messenger"), "release": "recalled"},
             {"when": hazard_in("fire"), "goto": "h"}]}},
         "global_edges": [
             {"when": ("or", losses_at_least(1, 2), spent("ammo")),
              "release": "return"}]}
    ok, why = validate_order(o)
    assert ok, why
