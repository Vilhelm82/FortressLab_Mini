"""
E2 — the discriminating probe.

Home has C+M, Away has a bare C. This is the first case with a NON-ZERO
expected value, i.e. the first test that could actually catch a broken engine.

Marked slow: 5x5 took ~232s in pure Python + Fractions. That runtime is the
port trigger recorded in the spec, not a defect.
"""

import pytest

from fortresslab_mini.kernel import Board, make_state, HOME, AWAY
from fortresslab_mini.solver import solve, play_out


@pytest.mark.parametrize("size", [4])
def test_extra_soldier_is_decisive(size):
    board = Board(size)
    start = make_state([(HOME, 'C', 0, 0),
                        (HOME, 'M', 1, 0),
                        (AWAY, 'C', size - 1, size - 1)])
    V, sweeps, conv = solve(board, start, max_sweeps=60)
    assert conv, "value iteration did not converge"
    assert V[start] == 1, f"expected Home win, got {V[start]}"

    trace, outcome = play_out(board, start, V)
    assert outcome == 1


@pytest.mark.slow
@pytest.mark.parametrize("size", [5])
def test_extra_soldier_is_decisive_larger(size):
    """Same claim one board size up. ~4 minutes; run with -m slow."""
    board = Board(size)
    start = make_state([(HOME, 'C', 0, 0),
                        (HOME, 'M', 1, 0),
                        (AWAY, 'C', size - 1, size - 1)])
    V, _, conv = solve(board, start, max_sweeps=60)
    assert conv and V[start] == 1
