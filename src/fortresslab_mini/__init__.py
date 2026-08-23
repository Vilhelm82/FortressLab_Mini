"""FortressLab Mini — an expanded-chess kernel for a castle siege game.

Build order (each rung proven before the next is added):
  1. kernel      — the dead short: state, resolution, terminal values
  2. solver      — exact-rational simultaneous game solver (kernel scale only)
  3. worldmap    — terrain, line of sight, the exposure field
  4. enemy_brain — cost-field planner: a wall is an expensive edge
  5. beliefs     — particle ledger (not yet built)
  6. commander   — COA generation, evaluation, receding-horizon loop (not yet built)
"""

__version__ = "0.1.0"
