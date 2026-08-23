"""
Solver — spec section 8.

Simultaneous zero-sum game, perfect information (kernel scaffolding grant).
Per state the stage game is a matrix solved EXACTLY over rationals; global
values by iteration to fixpoint. No floats anywhere.

SCOPE NOTE (ruled 2026-08-20): v0 has no impedance layer, so its agents are
unshackled by construction and have no strategy space to optimise over. This
solver is therefore a CONFORMANCE instrument at kernel scale, not a balance
instrument. It becomes a balance instrument once credits, orders and terrain
give a commander something to tune.
"""

from fractions import Fraction

from fortresslab_mini.kernel import (HOME, AWAY, DELTAS, legal_joint_actions,
                                     resolve, terminal, commander, cheb)


# --- Exact zero-sum matrix game value -----------------------------------------

def matrix_value(A):
    """Value of a zero-sum matrix game to the ROW player (the maximiser).

    A is m x n of Fractions/ints. Shift to strict positivity, then solve
        max  sum_j y_j   s.t.  sum_j A'[i][j] y_j <= 1,  y >= 0
    whose optimum is 1/v'. Primal simplex, Bland's rule (no cycling),
    exact rational arithmetic throughout.
    """
    m, n = len(A), len(A[0])
    lo = min(min(row) for row in A)
    shift = Fraction(1) - Fraction(lo)          # guarantees every entry >= 1 > 0
    Ap = [[Fraction(A[i][j]) + shift for j in range(n)] for i in range(m)]

    W = n + m + 1                                # structural | slack | rhs
    tab = [[Fraction(0)] * W for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            tab[i][j] = Ap[i][j]
        tab[i][n + i] = Fraction(1)
        tab[i][W - 1] = Fraction(1)
    for j in range(n):
        tab[m][j] = Fraction(-1)                 # maximising sum_j y_j

    basis = [n + i for i in range(m)]

    while True:
        # Bland: lowest-index column with negative reduced cost
        col = -1
        for j in range(W - 1):
            if tab[m][j] < 0:
                col = j
                break
        if col < 0:
            break

        # Ratio test, Bland tie-break on lowest basis index
        row, best = -1, None
        for i in range(m):
            if tab[i][col] > 0:
                r = tab[i][W - 1] / tab[i][col]
                if best is None or r < best or (r == best and basis[i] < basis[row]):
                    best, row = r, i
        if row < 0:
            raise ArithmeticError("unbounded — matrix was not strictly positive")

        piv = tab[row][col]
        tab[row] = [v / piv for v in tab[row]]
        for i in range(m + 1):
            if i != row and tab[i][col] != 0:
                f = tab[i][col]
                tab[i] = [a - f * b for a, b in zip(tab[i], tab[row])]
        basis[row] = col

    obj = tab[m][W - 1]                          # = 1 / v'
    return Fraction(1, 1) / obj - shift


# --- State space --------------------------------------------------------------

def successors(board, state):
    """Cached successor table: (ja_home, ja_away) -> resulting state."""
    jh = legal_joint_actions(board, state, HOME)
    ja = legal_joint_actions(board, state, AWAY)
    tbl = {}
    for a in jh:
        for b in ja:
            tbl[(a, b)] = resolve(board, state, a, b)
    return jh, ja, tbl


def reachable(board, start):
    """Every state reachable from `start` under any pair of joint actions."""
    seen, frontier = {start}, [start]
    while frontier:
        s = frontier.pop()
        if terminal(s) is not None:
            continue
        _, _, tbl = successors(board, s)
        for nxt in tbl.values():
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen


def solve(board, start, max_sweeps=200):
    """Value iteration to fixpoint. Returns (values, sweeps, converged)."""
    states = reachable(board, start)
    live = [s for s in states if terminal(s) is None]

    V = {}
    for s in states:
        t = terminal(s)
        V[s] = Fraction(t) if t is not None else Fraction(0)

    cache = {s: successors(board, s) for s in live}

    for sweep in range(1, max_sweeps + 1):
        changed = False
        for s in live:
            jh, ja, tbl = cache[s]
            A = [[V[tbl[(a, b)]] for b in ja] for a in jh]
            v = matrix_value(A)
            if v != V[s]:
                V[s] = v
                changed = True
        if not changed:
            return V, sweep, True
    return V, max_sweeps, False


# --- Bloodlust policy (spec B2) ------------------------------------------------

def bloodlust_action(board, state, side, V):
    """Among maximin-optimal PURE actions, take the one that closes the distance
    to the enemy commander. Ties break by fixed action order.

    This is what makes two bare commanders charge rather than circle: the
    charge is the tiebreak. Bloodlust lives in the value layer, not in a rule.
    """
    jh, ja, tbl = successors(board, state)
    mine, theirs = (jh, ja) if side == HOME else (ja, jh)
    sign = 1 if side == HOME else -1

    guaranteed = []
    for a in mine:
        worst = None
        for b in theirs:
            key = (a, b) if side == HOME else (b, a)
            val = sign * V[tbl[key]]
            worst = val if worst is None else min(worst, val)
        guaranteed.append((worst, a))

    best = max(w for w, _ in guaranteed)
    candidates = [a for w, a in guaranteed if w == best]

    def closing(a):
        me, foe = commander(state, side), commander(state, 1 - side)
        dx, dy = 0, 0
        for u, ai in zip([u for u in state if u[0] == side], a):
            if u[1] == 'C':
                dx, dy = DELTAS[ai]
        return cheb((me[2] + dx, me[3] + dy), (foe[2], foe[3]))

    candidates.sort(key=lambda a: (closing(a), a))
    return candidates[0]


def play_out(board, start, V, limit=200):
    """Run the bloodlust policy for both sides. Returns (trace, outcome)."""
    s, trace = start, [start]
    for _ in range(limit):
        t = terminal(s)
        if t is not None:
            return trace, t
        a = bloodlust_action(board, s, HOME, V)
        b = bloodlust_action(board, s, AWAY, V)
        s = resolve(board, s, a, b)
        trace.append(s)
    return trace, None            # non-termination — a Test T2 finding
