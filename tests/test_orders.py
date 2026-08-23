"""
Orders rung battery — grammar, validator, executor, lifecycle.

Tested as pure state machines: no AI authors anything here. Scripted world
events drive every transition. This is the law, tested before the lawyers.
"""

import pytest

from fortresslab_mini.orders import (
    validate_order, order_size, OrderExec, MalformedOrder,
    company_status, try_rally,
    ORDERED, STALE, FERAL, AWAITING,
)

AREA = (0, 0, 30, 10)      # the full granted scope: hold area + routes home
HOLD = (0, 0, 10, 10)


def scope(kinds, area=AREA):
    return {"kinds": set(kinds), "area": area}


def W(hour=9, messenger=False, enemy=False, lost=0, total=9, **kw):
    """A scripted world snapshot the guards read."""
    w = {"hour": hour, "messenger_contact": messenger,
         "enemy_contact": enemy, "losses": (lost, total)}
    w.update(kw)
    return w


# --- Order fixtures -----------------------------------------------------------

def clear_routes_suborder():
    """'Send two men-at-arms back and clear messenger routes.'
    Succeeds on finding a messenger; fails out on half losses."""
    return {
        "scope": scope({"move", "clear_route"}),
        "start": "clear",
        "nodes": {"clear": {"scope": scope({"move", "clear_route"}),
                            "edges": [
            {"when": ("messenger_contact",), "release": "contact_made"},
        ]}},
        "global_edges": [
            {"when": ("attrition_at_least", 1, 2), "release": "return"},
        ],
    }


def ten_am_order():
    """Will's contingency draft, verbatim in tree form:
    defend until the 10am messenger; if none by 11am -- no enemy: all return;
    in contact: detach two to clear routes and keep defending;
    at any point, half losses: all return."""
    return {
        "scope": scope({"defend", "move", "clear_route"}),
        "start": "hold",
        "nodes": {
            "hold": {"scope": scope({"defend"}, HOLD), "edges": [
                {"when": ("messenger_contact",), "release": "recalled"},
                {"when": ("and", ("time_at_or_after", 11),
                          ("no_enemy_contact",)), "release": "return"},
                {"when": ("and", ("time_at_or_after", 11),
                          ("enemy_contact",)),
                 "detach": {"n": 2, "order": clear_routes_suborder(),
                            "goto": "hold_reduced"}},
            ]},
            "hold_reduced": {"scope": scope({"defend"}, HOLD), "edges": [
                {"when": ("messenger_contact",), "release": "recalled"},
            ]},
        },
        "global_edges": [
            {"when": ("attrition_at_least", 1, 2), "release": "return"},
        ],
    }


# --- Validator ----------------------------------------------------------------

def test_bare_hold_is_malformed():
    """An order with no release conditions cannot exist."""
    bare = {"scope": scope({"defend"}), "start": "hold",
            "nodes": {"hold": {"scope": scope({"defend"}, HOLD), "edges": []}}}
    ok, why = validate_order(bare)
    assert not ok and any("no release" in p for p in why)


def test_until_recalled_alone_is_malformed():
    """The soft-lock rule: a dead messenger must not weld men to an order."""
    o = {"scope": scope({"defend"}), "start": "hold",
         "nodes": {"hold": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": ("messenger_contact",), "release": "recalled"}]}}}
    ok, why = validate_order(o)
    assert not ok
    assert any("self-triggerable" in p for p in why)


def test_recalled_or_half_losses_validates():
    """The x-or-y form: one exit the commander controls, one the unit does."""
    o = {"scope": scope({"defend"}), "start": "hold",
         "nodes": {"hold": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": ("messenger_contact",), "release": "recalled"}]}},
         "global_edges": [
             {"when": ("attrition_at_least", 1, 2), "release": "return"}]}
    ok, why = validate_order(o)
    assert ok, why


def test_remote_fact_release_is_malformed():
    """A unit cannot be released by a fact it has no way to observe."""
    o = {"scope": scope({"defend"}), "start": "hold",
         "nodes": {"hold": {"scope": scope({"defend"}, HOLD), "edges": [
             {"when": ("remote_fact", "far_gate_fallen"),
              "release": "done"}]}}}
    ok, why = validate_order(o)
    assert not ok and any("non-local" in p for p in why)


def test_will_10am_contingency_order_validates():
    """The granular draft is legal: every path releases, the sub-order
    attenuates, and it fits a sergeant's head."""
    o = ten_am_order()
    ok, why = validate_order(o, rank="sergeant")
    assert ok, why
    assert order_size(o) <= 8


def test_detach_outside_parent_scope_is_refused():
    """Attenuation, never amplification."""
    o = ten_am_order()
    d = o["nodes"]["hold"]["edges"][2]["detach"]["order"]
    d["scope"]["area"] = (0, 0, 100, 100)          # beyond the grant
    ok, why = validate_order(o)
    assert not ok and any("exceeds parent scope" in p for p in why)


def test_capacity_bounds_granularity():
    """A monster tree is legal for a captain and unissuable to a sergeant."""
    edges = [{"when": ("time_at_or_after", h), "goto": "hold"}
             for h in range(6, 15)]
    monster = {"scope": scope({"defend"}), "start": "hold",
               "nodes": {"hold": {"scope": scope({"defend"}, HOLD),
                                  "edges": edges}},
               "global_edges": [
                   {"when": ("attrition_at_least", 1, 2),
                    "release": "return"}]}
    ok_s, why_s = validate_order(monster, rank="sergeant")
    ok_c, _ = validate_order(monster, rank="captain")
    assert not ok_s and any("capacity" in p for p in why_s)
    assert ok_c


# --- Executor: Will's order, run through its scripted futures -----------------

def test_messenger_arrives_at_ten():
    ex = OrderExec(ten_am_order())
    assert ex.step(W(hour=9)) is None                       # holding, quiet
    assert ex.step(W(hour=10, messenger=True)) == ("release", "recalled")
    assert ex.can_retask()


def test_timeout_quiet_all_return():
    ex = OrderExec(ten_am_order())
    ex.step(W(hour=10))
    assert ex.step(W(hour=11)) == ("release", "return")


def test_timeout_in_contact_detaches_two():
    """The lost-comms drill: no word by 11, fighting -> send two back."""
    ex = OrderExec(ten_am_order())
    ex.step(W(hour=10, enemy=True))
    ev = ex.step(W(hour=11, enemy=True))
    assert ev[0] == "detach" and ev[1] == 2
    assert ex.node == "hold_reduced"
    n, sub = ex.detachments[0]
    # The detachment runs its own order: clears routes until contact.
    assert sub.step(W(hour=11)) is None
    assert sub.step(W(hour=12, messenger=True)) == ("release", "contact_made")


def test_half_losses_release_fires_from_any_node():
    """The global exit rides every branch -- including post-detachment."""
    ex = OrderExec(ten_am_order())
    ex.step(W(hour=11, enemy=True))                          # detach, reduced
    assert ex.node == "hold_reduced"
    assert ex.step(W(hour=12, enemy=True, lost=5)) == ("release", "return")


def test_order_lock_holds_until_release():
    ex = OrderExec(ten_am_order())
    assert not ex.can_retask()
    ex.step(W(hour=9))
    assert not ex.can_retask()                               # still locked
    ex.step(W(hour=10, messenger=True))
    assert ex.can_retask()                                   # released


# --- Lifecycle: the leash, the wind-up toy, the slipped leash ------------------

def test_stale_orders_execute_unchanged():
    """Officer dead, order live: the company carries on, a wind-up toy."""
    ex = OrderExec(ten_am_order())
    ex.stale = True                    # officer killed mid-order
    assert company_status(officer_alive=False, exec_=ex) == STALE
    ev = ex.step(W(hour=11, enemy=True))
    assert ev[0] == "detach"           # the drill still runs, unchanged


def test_feral_requires_both_conditions():
    """Feral = officer dead AND order complete. Either alone is not enough."""
    ex = OrderExec(ten_am_order())
    assert company_status(True, ex) == ORDERED
    assert company_status(False, ex) == STALE
    ex.step(W(hour=10, messenger=True))                     # release fires
    assert company_status(True, ex) == AWAITING
    assert company_status(False, ex) == FERAL


def test_feral_rally_fills_open_slot():
    companies = [
        {"members": 9, "capacity": 9, "pos": (2, 2)},       # full: no slot
        {"members": 7, "capacity": 9, "pos": (4, 4)},       # room for two
    ]
    joined = try_rally((5, 5), companies, detection_radius=3)
    assert joined is companies[1] and companies[1]["members"] == 8


def test_feral_out_of_detection_stays_feral():
    companies = [{"members": 5, "capacity": 9, "pos": (0, 0)}]
    assert try_rally((20, 20), companies, detection_radius=3) is None


def test_determinism_same_world_same_trace():
    worlds = [W(hour=9), W(hour=10, enemy=True), W(hour=11, enemy=True),
              W(hour=12, enemy=True), W(hour=12, enemy=True, lost=5)]
    traces = []
    for _ in range(2):
        ex = OrderExec(ten_am_order())
        trace = []
        for w in worlds:
            ev = ex.step(w)
            # detach events carry a fresh executor object; compare shape only
            trace.append(ev[:2] if ev and ev[0] == "detach" else ev)
        traces.append(trace)
    assert traces[0] == traces[1]


def test_malformed_order_is_unissuable():
    with pytest.raises(MalformedOrder):
        OrderExec({"scope": scope({"defend"}), "start": "h",
                   "nodes": {"h": {"scope": scope({"defend"}, HOLD),
                                   "edges": []}}})
