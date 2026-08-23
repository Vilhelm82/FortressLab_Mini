# FortressLab Mini

A castle siege game built as a spiritual expansion to chess: a finite, closed
rule set with everything else falling out of how two commanders navigate it.

The player designs; the player never fights. Both sides are AI-commanded, and
the defenders inherit a castle they have to read for themselves. You cannot
leave them a guidebook — the architecture *is* the guidebook.

## Design spine

* **Bounded sandbox.** Design where the walls are and how the sand behaves.
  No scenario rules, no penalties triggered by detecting a strategy.
* **A wall is an expensive edge**, not an obstacle. Weakness is the cheapest
  path, discovered — never a rule saying "attack the weak point".
* **Orders are impedance.** Every unit is already violence; command constrains
  it, never causes it. No order can tell a unit not to kill.
* **The circuit.** Away is potential, Home is the neutral return, and the
  design is the impedance between them. Both extremes lose: R→0 is the dead
  short (mutual annihilation), R→∞ is the tomb (no work done, no kill).
* **Chess shape.** Any legal move is legal; a move's value is only what it
  contributes to the position.

## Layout

    src/fortresslab_mini/
        kernel.py       state, resolution, terminal values  (spec §1-6)
        solver.py       exact-rational simultaneous solver   (spec §8)
        worldmap.py     terrain, line of sight, exposure field
        enemy_brain.py  cost-field planner — path of least resistance
    tests/
        test_kernel.py    T0-T3 conformance battery
        test_ladder.py    M0-M3 progressive map ladder
        test_probe_2v1.py the discriminating non-zero-value probe
    docs/
        kernel_v0_spec.md  the ruled specification

## Running

    pip install -e ".[dev]"
    pytest                 # fast battery
    pytest -m slow         # includes the multi-minute 5x5 solve

## Status

Kernel conformance passing. Stage 1 of the commander pipeline (enemy-brain
planner) passing the full map ladder. Next: the particle/ledger belief layer,
where the planner stops reading ground truth and starts reading what a
commander merely believes.

## Open rulings

* Are timber gates opaque to arrows? Currently they block movement but not
  sight, so a gate archer covers his own approach lane.
* Trauma floor, if the aptitude system is ever built: a unit degradable
  without limit becomes catatonic, which the design elsewhere forbids.
