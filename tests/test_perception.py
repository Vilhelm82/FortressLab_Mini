"""
Perception battery — the capacitor.

Angle and distance are the same mechanic (marginal contact) in two geometries,
so the tests check they behave identically: one brush gives PRESENCE, a second
inside the alert window gives IDENTIFICATION, and silence lets it decay away.

Every threshold is a CONFIG parameter, not a constant — the LLM R&D phase
tunes these. The tests assert the SHAPE of the mechanic, never the numbers.
"""

import pytest

from fortresslab_mini.worldmap import WorldMap
from fortresslab_mini.perception import (Perception, arc_of, CONFIG, RING,
                                         facing_from_delta,
                                         FRONT, PERIPHERY, REAR,
                                         NOTHING, PRESENCE, IDENTIFIED)
from fortresslab_mini.sim import Sim, Unit, HOME, AWAY

FLAT = ["." * 20 for _ in range(14)]
EAST = facing_from_delta(1, 0)


def u(uid, side, x, y, facing=EAST):
    return Unit(uid, side, "M", x, y, facing=facing)


def test_arcs_partition_the_ring():
    """Front, periphery, rear — every direction lands in exactly one."""
    seen = {arc_of(EAST, dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)}
    assert seen == {FRONT, PERIPHERY, REAR}


def test_directly_ahead_is_front_directly_behind_is_rear():
    assert arc_of(EAST, 3, 0) == FRONT
    assert arc_of(EAST, -3, 0) == REAR


def test_front_sighting_identifies_at_once():
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 8, 5)
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == IDENTIFIED


def test_periphery_gives_presence_not_identification():
    """The ruling: peripheral awareness is worth half of facing awareness."""
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 5, 2)      # off to his flank
    assert arc_of(obs.facing, tgt.x - obs.x, tgt.y - obs.y) == PERIPHERY
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == PRESENCE


def test_two_peripheral_brushes_inside_the_window_identify():
    """Cross his corner of eye twice before the alert cools and you are made."""
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 5, 2)
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == PRESENCE
    p.step([obs, tgt], 1)
    assert p.state(1, 2) == IDENTIFIED


def test_grid_accessors_are_bounds_safe():
    """An off-map coordinate must degrade, never raise. This exact unguarded
    index was crashing whole analyses."""
    wm = WorldMap(FLAT)
    assert wm.eye(-5, 900) == 1
    assert wm.blocks_sight(900, 900) is True


def test_awareness_decays_when_contact_stops():
    """The cooldown: charge bleeds off once nothing is being observed."""
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 8, 5)
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == IDENTIFIED
    gone = u(2, AWAY, 40, 40)
    for t in range(1, 40):
        p.step([obs, gone], t)
    assert p.state(1, 2) == NOTHING


def test_long_range_degrades_to_presence():
    """Distance and angle are the same mechanic: beyond the soft maximum a
    plain frontal sighting is worth only what a peripheral brush is worth."""
    p = Perception(WorldMap(FLAT))
    soft = CONFIG["soft_range"]
    near, far = u(2, AWAY, 5 + soft, 5), u(3, AWAY, 5 + soft + 2, 5)
    obs = u(1, HOME, 5, 5)
    p.step([obs, near, far], 0)
    assert p.state(1, 2) == IDENTIFIED
    assert p.state(1, 3) == PRESENCE


def test_nothing_is_seen_through_stone():
    walled = ["." * 20 for _ in range(5)] + ["#" * 20] + ["." * 20 for _ in range(8)]
    p = Perception(WorldMap(walled))
    obs, tgt = u(1, HOME, 5, 4, facing=facing_from_delta(0, 1)), u(2, AWAY, 5, 8)
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == NOTHING


def test_rear_approach_is_invisible_and_that_is_the_stealth_kill():
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 10, 5), u(2, AWAY, 6, 5)      # he faces east, away
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == NOTHING
    assert p.state(2, 1) == IDENTIFIED                   # the stalker sees him


def test_height_extends_reach():
    tower = ["." * 20 for _ in range(14)]
    tower[5] = "." * 5 + "4" + "." * 14
    wm = WorldMap(tower)
    p = Perception(wm)
    high = u(1, HOME, 5, 5)                              # standing on the tower
    far = u(2, AWAY, 5 + CONFIG["hard_range"] + 1, 5)
    assert p.quality(high, far)[0] > 0
    ground = u(3, HOME, 5, 6)          # beside the tower, not on it
    assert p.quality(ground, far)[0] == 0


def test_every_threshold_is_a_parameter():
    """Ruled: the LLM R&D phase tunes these. Nothing is a constant."""
    p = Perception(WorldMap(FLAT), {"identify": 99})
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 8, 5)
    p.step([obs, tgt], 0)
    assert p.state(1, 2) == PRESENCE      # same sighting, different doctrine


def test_sightings_report_why():
    """The viewport must be able to say WHY a cone went orange, not just that
    it did."""
    p = Perception(WorldMap(FLAT))
    obs, tgt = u(1, HOME, 5, 5), u(2, AWAY, 5, 2)
    ev = p.step([obs, tgt], 0)
    assert ev and ev[0]["arc"] == PERIPHERY and ev[0]["why"]
