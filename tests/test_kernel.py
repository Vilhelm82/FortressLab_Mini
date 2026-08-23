"""
Verification battery — spec section 9. Kernel conformance at R = 0.

T0  Dead Short   : bare commanders, every separation -> TIE, and the bloodlust
                   policy terminates in mutual death. Game One, certified.
T1  Mirror       : mirror-symmetric states solve to symmetric values.
T2  Termination  : optimal-with-tiebreak play reaches a terminal state.
T3  Boundary     : optimal play never touches the map edge.
Inv Invariant    : no live state holds a hostile pair at Chebyshev <= 1.

CAVEAT (recorded honestly): with commanders only, nothing can produce a
non-zero value -- an engine that always returned 0 would pass every T0 check.
test_probe_2v1 is the discriminating case.
"""

import pytest

from fortresslab_mini.kernel import (Board, make_state, terminal,
                                     live_invariant, HOME, AWAY)
from fortresslab_mini.solver import solve, play_out

SIZE = 9
SEPARATIONS = [2, 3, 4, 5, 6]
AXES = ['x', 'y', 'diag']


def dead_short(board_size, sep, axis):
    """Two bare commanders, `sep` apart along `axis`."""
    mid = board_size // 2
    off = mid - sep // 2
    if axis == 'x':
        h, a = (off, mid), (off + sep, mid)
    elif axis == 'y':
        h, a = (mid, off), (mid, off + sep)
    else:
        h, a = (off, off), (off + sep, off + sep)
    return make_state([(HOME, 'C', h[0], h[1]), (AWAY, 'C', a[0], a[1])])


@pytest.fixture(scope="module")
def board():
    return Board(SIZE)


@pytest.fixture(scope="module")
def solved(board):
    """Solve every dead-short configuration once, reuse across tests."""
    out = {}
    for axis in AXES:
        for sep in SEPARATIONS:
            start = dead_short(SIZE, sep, axis)
            V, sweeps, conv = solve(board, start)
            trace, outcome = play_out(board, start, V)
            out[(axis, sep)] = (start, V, sweeps, conv, trace, outcome)
    return out


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("sep", SEPARATIONS)
def test_T0_value_is_tie(solved, axis, sep):
    start, V, _, conv, _, _ = solved[(axis, sep)]
    assert conv, "value iteration did not converge"
    assert V[start] == 0, f"expected TIE, got {V[start]}"


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("sep", SEPARATIONS)
def test_T0_mutual_death(solved, axis, sep):
    """Both commanders die on the same tick — the dead short, enacted."""
    _, _, _, _, _, outcome = solved[(axis, sep)]
    assert outcome == 0


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("sep", SEPARATIONS)
def test_T2_terminates(solved, axis, sep):
    """Will's ruling: cycles 'will never occur'. Billed as a test, not assumed."""
    _, _, _, _, trace, outcome = solved[(axis, sep)]
    assert outcome is not None, f"non-terminating after {len(trace)-1} ticks"


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("sep", SEPARATIONS)
def test_T3_edge_untouched(board, solved, axis, sep):
    """The boundary is an array limit, not a game element — prove it stays inert."""
    _, _, _, _, trace, _ = solved[(axis, sep)]
    touched = [(u[2], u[3]) for s in trace for u in s
               if board.on_edge(u[2], u[3])]
    assert not touched, f"optimal play reached the edge at {touched[:3]}"


@pytest.mark.parametrize("axis", AXES)
@pytest.mark.parametrize("sep", SEPARATIONS)
def test_invariant_holds(solved, axis, sep):
    _, _, _, _, trace, _ = solved[(axis, sep)]
    bad = [s for s in trace if terminal(s) is None and not live_invariant(s)]
    assert not bad, f"{len(bad)} live states held a hostile pair at range"


@pytest.mark.parametrize("sep", [2, 3, 4, 5])
def test_T1_mirror_oracle(solved, sep):
    """A symmetric position must solve symmetrically — an engine bug detector."""
    sx, Vx, *_ = solved[('x', sep)]
    sy, Vy, *_ = solved[('y', sep)]
    assert Vx[sx] == Vy[sy]
