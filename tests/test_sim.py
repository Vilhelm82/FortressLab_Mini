"""
Tick-loop battery — the first tests where anything actually MOVES.

The kernel proved resolution, the ladder proved the cost field, the score
battery proved the performance. This proves they compose.
"""

import pytest

from fortresslab_mini.worldmap import WorldMap
from fortresslab_mini.score import (ScoreExec, cancellation, attrition, note,
                                    score, silence, SELF_DIRECTED)
from fortresslab_mini.sim import Sim, HOME, AWAY, acts_this_tick

FLAT = ["." * 16 for _ in range(12)]


def hold_order(area):
    """A held address: richness dies if the ground is lost or we are halved.
    Attrition is the self-resolving note, so the score always ends."""
    return score(area, [note(silence(), label="ground-lost"),
                        note(attrition(1, 2), label="halved")],
                 kinds=("defend",))


def test_cadence_hook_is_the_only_switch():
    """Ruled: every unit, every tick — but behind one function."""
    assert acts_this_tick(None, 0) is True
    assert acts_this_tick(None, 7) is True


def test_bare_commanders_charge_and_tie():
    """The dead short, now enacted by the sim rather than the solver."""
    s = Sim(WorldMap(FLAT))
    s.add_unit(1, HOME, "C", 2, 5)
    s.add_unit(2, AWAY, "C", 13, 5)
    assert s.run() == 0
    assert not any(u.alive for u in s.units.values())


def test_trace_records_every_tick():
    s = Sim(WorldMap(FLAT))
    s.add_unit(1, HOME, "C", 2, 5)
    s.add_unit(2, AWAY, "C", 13, 5)
    s.run()
    assert len(s.trace) == s.tick + 1
    assert [f["tick"] for f in s.trace] == list(range(s.tick + 1))
    assert any(e.get("death") for f in s.trace for e in f["events"])


def test_soldier_trades_itself_for_the_enemy_commander():
    """Zero HP plus contact-is-death: a man-at-arms buys the game with his life.
    Survival is instrumental (spec B4) — dying to end it costs nothing."""
    s = Sim(WorldMap(FLAT))
    s.add_unit(1, HOME, "C", 0, 0)
    s.add_unit(2, HOME, "M", 6, 5)
    s.add_unit(3, AWAY, "C", 9, 5)
    assert s.run() == 1
    assert not s.units[2].alive and not s.units[3].alive
    assert s.units[1].alive


def test_determinism_same_setup_same_trace():
    def build():
        s = Sim(WorldMap(FLAT))
        s.add_unit(1, HOME, "C", 1, 1)
        s.add_unit(2, HOME, "M", 4, 6)
        s.add_unit(3, AWAY, "C", 14, 9)
        s.add_unit(4, AWAY, "M", 11, 3)
        s.run()
        return [(f["tick"], tuple((u["uid"], u["x"], u["y"])
                                  for u in f["units"])) for f in s.trace]
    assert build() == build()
