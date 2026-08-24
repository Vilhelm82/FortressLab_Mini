"""
Beliefs + closure battery.

The conformance half is the ADOPTED instrument: exact transport on a correct
model must have zero holonomy — commuting evidence commutes, and a loop over
a world that matches the model closes to ~0. Any residual there is a filter
bug, not information.

The probation half (does closure-driven dispatch beat a fixed rotation?) is
NOT here — that verdict comes from experiments/closure_bench.py with numbers.
"""

from fortresslab_mini.worldmap import WorldMap
from fortresslab_mini.beliefs import (BeliefField, loop_residual,
                                      sector_residuals, choose_next_loop)

FLAT = ["." * 16 for _ in range(12)]


def field():
    return BeliefField(WorldMap(FLAT))


def test_mass_is_conserved_by_prediction():
    b = field()
    for _ in range(30):
        b.predict()
    assert abs(sum(b.b[y][x] for x, y in b.open) - 1.0) < 1e-9


def test_independent_evidence_commutes():
    """Zero-holonomy conformance: order of independent reports is immaterial."""
    obs1 = [(3, 3, False, 5)]
    obs2 = [(12, 8, True, 5)]
    a, c = field(), field()
    a.fuse(obs1, now=5); a.fuse(obs2, now=5)
    c.fuse(obs2, now=5); c.fuse(obs1, now=5)
    for x, y in a.open:
        assert abs(a.b[y][x] - c.b[y][x]) < 1e-12


def snapshot(b):
    row = [r[:] for r in b.b]
    return (lambda rw: lambda x, y, rad: sum(
        rw[yy][xx] for yy in range(max(0, y - rad), min(12, y + rad + 1))
        for xx in range(max(0, x - rad), min(16, x + rad + 1))))(row)


def test_correct_model_closes_to_the_diffusion_floor():
    """A static empty corridor, believed empty, patrolled: residual sits at
    the MOTION-MODEL floor, not zero — the model itself says an enemy could
    have wandered in. Per-observation residual must stay at that leak level;
    anything above it is filter error."""
    b = field()
    b.fuse([(x, 2, False, 0) for x in range(16)], now=0)   # known-empty north
    snaps = {}
    for t in range(1, 7):
        b.predict()
        snaps[t] = snapshot(b)
    obs = [(x, 2, False, t) for t, x in enumerate(range(1, 7), start=1)]
    total, per = loop_residual(snaps, obs, viewshed_r=1)
    assert total / len(obs) < 0.06, f"per-obs residual {total/len(obs)}"


def test_model_violation_fires_the_residual():
    """The world moved behind the model's back: the loop must NOT close.
    Confidence is earned first — three consecutive confirmations of the same
    contact concentrate the belief — and only a confident belief, violated,
    fires a loud residual. A humble belief violated fires a humble one."""
    b = field()
    for t in range(3):
        b.fuse([(3, 3, True, t)], now=t)       # tracked contact, pinned
    snap = {3: snapshot(b)}
    total, per = loop_residual(snap, [(3, 3, False, 3)], viewshed_r=1)
    assert total > 0.6, f"confident belief violated, residual only {total}"
    assert per[0][3] == total                  # localised to the exact visit


def test_residuals_localise_by_sector():
    per = [(2, 2, 1, 0.9), (13, 2, 2, 0.05), (2, 9, 3, 0.02)]
    sec = sector_residuals(per, lambda x, y: ("W" if x < 8 else "E")
                           + ("N" if y < 6 else "S"))
    assert max(sec, key=sec.get) == "WN"


def test_dispatch_prefers_mass_and_breaks_ties_by_staleness():
    b = field()
    b.fuse([(12, 3, True, 0)], now=0)          # mass concentrated NE
    sectors = {"NW": (0, 0, 7, 5), "NE": (8, 0, 15, 5),
               "SW": (0, 6, 7, 11), "SE": (8, 6, 15, 11)}
    stale = {"NW": 3, "NE": 1, "SW": 9, "SE": 3}
    assert choose_next_loop(sectors, b, stale) == "NE"
    b2 = field()                               # uniform: degenerate case
    assert choose_next_loop(sectors, b2, stale) == "SW"   # staleness decides
