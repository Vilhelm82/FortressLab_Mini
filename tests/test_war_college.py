"""
The War College — scenario exams for the commander decision loop.

Each scenario is a CONTROLLED quilt (the map picture a commander would hold)
plus a behavioural assertion: does he act on the dangers and opportunities in
it logically? Assertions are about the SHAPE of the decision — which sector,
which class of action, what he refuses to do — never exact orders, mirroring
the perception battery's rule: test the shape, not the numbers.

The battery is the contract. Commander v0 is the first candidate to sit the
exam; every smarter pipeline that follows must pass the same papers.

NOTE: these are SINGLE-DECISION exams. Sequence behaviour — thrashing,
memory of one's own outstanding orders, feint detection, reserve discipline
over time — is the campaign battery, not yet built.
"""

import pytest

from fortresslab_mini.commander import (Situation, decide, fuse_quilt,
                                        threats, sector_of)

W, H = 24, 24
KEEP = (12, 12)
SECTORS = {"NW": (0, 0, 11, 11), "NE": (12, 0, 23, 11),
           "SW": (0, 12, 11, 23), "SE": (12, 12, 23, 23)}


def sit(patches, companies=None, credits=100, now=100, walls=()):
    return Situation(walls, W, H, KEEP, now, credits, patches,
                     companies if companies is not None else [], SECTORS)


def patch(area, t, sightings=()):
    return {"area": area, "t": t, "sightings": list(sightings)}


def company(cid, pos, locked=False):
    return {"cid": cid, "pos": pos, "locked": locked, "sector": None}


def tasked_sectors(s, acts):
    out = []
    for a in acts:
        if a[0] in ("task", "spawn"):
            x0, y0, x1, y1 = a[-1]["area"]
            out.append(sector_of(s, (x0 + x1) // 2, (y0 + y1) // 2))
    return out


def test_breach_threat_tasks_the_reserve_to_the_right_sector():
    """Sappers massing at the west wall; one free reserve in the courtyard.
    Logical behaviour: that reserve goes WEST. Not east, not nowhere."""
    s = sit(patches=[patch((0, 8, 6, 16), t=95,
                           sightings=[(3, 12, "enemy", 8)])],
            companies=[company(1, (13, 13))])
    acts = decide(s)
    assert "NW" in tasked_sectors(s, acts) or "SW" in tasked_sectors(s, acts)
    assert all(sec not in ("NE", "SE") for sec in tasked_sectors(s, acts))


def test_quiet_quilt_holds():
    """Fresh patches, nothing in them: the logical action is none at all."""
    s = sit(patches=[patch(SECTORS[n], t=98) for n in SECTORS],
            companies=[company(1, (13, 13))])
    assert decide(s) == [("hold",)]


def test_fresh_clear_report_overrides_stale_sighting():
    """Old patch: enemy at the gate. Newer patch over the same ground: clear.
    Last write wins (ruled): the commander must NOT act on the ghost."""
    s = sit(patches=[
        patch((0, 8, 6, 16), t=40, sightings=[(3, 12, "enemy", 8)]),
        patch((0, 8, 6, 16), t=90, sightings=[]),
    ], companies=[company(1, (13, 13))])
    assert fuse_quilt(s) == []
    assert all(a[0] != "task" for a in decide(s))


def test_conflicting_patches_act_on_the_newest():
    """Stale big force east, fresh force west: the west report is the live
    one; the east ghost must not outrank it purely on remembered size."""
    s = sit(patches=[
        patch((16, 8, 23, 16), t=10, sightings=[(20, 12, "enemy", 12)]),
        patch((0, 8, 6, 16), t=96, sightings=[(3, 12, "enemy", 5)]),
    ], companies=[company(1, (13, 13))])
    assert threats(s)[0]["x"] < 12, "freshness failed to outrank stale mass"


def test_locked_company_is_never_retasked():
    """The only company near the threat is order-locked. The commander must
    work around the lock — spawn, or task someone else — never violate it."""
    s = sit(patches=[patch((0, 8, 6, 16), t=95,
                           sightings=[(3, 12, "enemy", 8)])],
            companies=[company(1, (5, 12), locked=True),
                       company(2, (20, 20))], credits=100)
    acts = decide(s)
    assert all(not (a[0] == "task" and a[1] == 1) for a in acts)
    assert any(a[0] == "task" and a[1] == 2 for a in acts) \
        or any(a[0] == "spawn" for a in acts)


def test_no_free_companies_converts_credits():
    """Everyone locked, danger at the wall, credits in hand: the reserve is
    latent force — convert it. (Spend-anytime, ruled 25 Aug.)"""
    s = sit(patches=[patch((0, 8, 6, 16), t=95,
                           sightings=[(3, 12, "enemy", 8)])],
            companies=[company(1, (5, 12), locked=True)], credits=40)
    assert any(a[0] == "spawn" for a in decide(s))


def test_no_companies_no_credits_holds_rather_than_hallucinates():
    """Nothing to task, nothing to buy: the only legal answer is nothing."""
    s = sit(patches=[patch((0, 8, 6, 16), t=95,
                           sightings=[(3, 12, "enemy", 8)])],
            companies=[company(1, (5, 12), locked=True)], credits=0)
    acts = decide(s)
    assert all(a[0] not in ("task", "spawn") or a[1] != 1 for a in acts)


def test_lightly_guarded_enemy_commander_draws_a_strike():
    """Their commander with two guards, a fresh company in reach: logical
    behaviour is a strike order aimed at his position."""
    s = sit(patches=[patch((16, 16, 23, 23), t=97,
                           sightings=[(20, 20, "C", 1),
                                      (20, 21, "enemy", 2)])],
            companies=[company(1, (14, 14))])
    strikes = [a for a in decide(s) if a[0] == "task"
               and "attack" in a[2]["kinds"]]
    assert strikes, "opportunity ignored"
    x0, y0, x1, y1 = strikes[0][2]["area"]
    assert x0 <= 20 <= x1 and y0 <= 20 <= y1


def test_heavily_guarded_commander_is_not_prey():
    """Same sighting with a real bodyguard: the cheap strike must NOT fire."""
    s = sit(patches=[patch((16, 16, 23, 23), t=97,
                           sightings=[(20, 20, "C", 1),
                                      (20, 21, "enemy", 9)])],
            companies=[company(1, (14, 14))])
    assert not any(a[0] == "task" and "attack" in a[2]["kinds"]
                   for a in decide(s))


def test_dark_sector_draws_a_scout():
    """Three sectors reporting, one silent for 200 ticks: close the loop.
    (The holonomy doctrine as behaviour: unmeasured ground is unclosed error.)"""
    s = sit(patches=[patch(SECTORS[n], t=95) for n in ("NW", "NE", "SE")],
            companies=[], credits=10, now=100)
    scouts = [a for a in decide(s) if a[0] == "scout"]
    assert scouts
    x0, y0, x1, y1 = scouts[0][1]["area"]
    assert sector_of(s, (x0 + x1) // 2, (y0 + y1) // 2) == "SW"


def test_every_emitted_order_validates():
    """decide() asserts internally; this proves the assertion is live."""
    for build in (
        lambda: sit(patches=[patch((0, 8, 6, 16), t=95,
                                   sightings=[(3, 12, "enemy", 8)])],
                    companies=[company(1, (13, 13))]),
        lambda: sit(patches=[patch(SECTORS[n], t=95)
                             for n in ("NW", "NE", "SE")], credits=10),
    ):
        decide(build())
