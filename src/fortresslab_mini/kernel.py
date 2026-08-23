"""
Kernel v0.1 — "The Dead Short"

Implements spec sections 1-6. Integers only, no floats, no randomness.

Conventions
-----------
side  : 0 = Home, 1 = Away
kind  : 'C' = Commander (crown), 'M' = Man-at-Arms
unit  : (side, kind, x, y)
state : tuple of units, sorted -- canonical ordering
"""

from itertools import product

# --- Actions (spec A1): 8 Moore neighbours + Stay -----------------------------
# Stay first so it is index 0; the rest in a fixed lexicographic order (spec B2).
DELTAS = ((0, 0),
          (-1, -1), (-1, 0), (-1, 1),
          (0, -1), (0, 1),
          (1, -1), (1, 0), (1, 1))

HOME, AWAY = 0, 1


def cheb(a, b):
    """Chebyshev distance -- the metric that matches 8-directional stepping."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class Board:
    """Finite map. The edge is an array limit, not a game element (spec W2).

    Test T3 asks whether optimal play ever touches it; if it does, the map is
    too small and results are contaminated.
    """

    def __init__(self, size):
        self.size = size

    def inside(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def on_edge(self, x, y):
        return x in (0, self.size - 1) or y in (0, self.size - 1)


def units_of(state, side):
    return [u for u in state if u[0] == side]


def commander(state, side):
    for u in state:
        if u[0] == side and u[1] == 'C':
            return u
    return None


# --- Legal joint actions (spec A1-A5) ----------------------------------------

def legal_joint_actions(board, state, side):
    """All joint actions for one side.

    Occupancy is a property of stopping, not transit (spec A4):
      * every destination must be on the map
      * no two friendly units may stop on the same cell
    Transit is unconstrained -- units pass through each other freely.
    Hostile cells are NOT excluded: closing to contact is legal and lethal.
    """
    mine = units_of(state, side)
    out = []
    for combo in product(range(len(DELTAS)), repeat=len(mine)):
        dests = []
        ok = True
        for u, ai in zip(mine, combo):
            dx, dy = DELTAS[ai]
            nx, ny = u[2] + dx, u[3] + dy
            if not board.inside(nx, ny):
                ok = False
                break
            dests.append((nx, ny))
        if ok and len(set(dests)) == len(dests):
            out.append(combo)
    return out


# --- Resolution (spec section 5) ---------------------------------------------

def resolve(board, state, ja_home, ja_away):
    """One tick: intent -> placement -> contact -> (caller checks terminal).

    No collision-resolution step exists; illegal configurations were excluded
    at legality, never resolved at runtime.
    """
    moved = []
    for side, ja in ((HOME, ja_home), (AWAY, ja_away)):
        for u, ai in zip(units_of(state, side), ja):
            dx, dy = DELTAS[ai]
            moved.append((u[0], u[1], u[2] + dx, u[3] + dy))

    # Contact: every hostile pair at Chebyshev <= 1 dies. All deaths simultaneous.
    doomed = set()
    for i, a in enumerate(moved):
        for b in moved[i + 1:]:
            if a[0] != b[0] and cheb((a[2], a[3]), (b[2], b[3])) <= 1:
                doomed.add(a)
                doomed.add(b)

    return tuple(sorted(u for u in moved if u not in doomed))


# --- Terminal states and values (spec section 6) ------------------------------

WIN_HOME, WIN_AWAY, TIE = +1, -1, 0


def terminal(state):
    """Returns None if the game continues, else the value from Home's view."""
    ch = commander(state, HOME) is not None
    ca = commander(state, AWAY) is not None
    if ch and ca:
        return None
    if ch and not ca:
        return WIN_HOME
    if ca and not ch:
        return WIN_AWAY
    return TIE          # both commanders dead on the same tick -- the dead short


# --- Invariant (spec S3) ------------------------------------------------------

def live_invariant(state):
    """No hostile pair at Chebyshev <= 1 may exist in a live state.

    Such pairs die during resolution, so a live state containing one is
    unreachable. Property-tested, not assumed.
    """
    for i, a in enumerate(state):
        for b in state[i + 1:]:
            if a[0] != b[0] and cheb((a[2], a[3]), (b[2], b[3])) <= 1:
                return False
    return True


def make_state(units):
    return tuple(sorted(units))
