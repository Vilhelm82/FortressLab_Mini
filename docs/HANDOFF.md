# FortressLab Mini — Session Handoff

**Repo:** `/mnt/fast/Work/Creative Projects/FortressLab_Mini` · latest commit `71e767f` · **136 tests green**
**Run tests:** `python3 -m pytest -q` (fast) · `pytest -m slow` adds the ~4-min 5×5 solve
**War room:** `python3 tools/warroom.py` → http://localhost:8770
**Bench:** `python3 experiments/closure_bench.py` (standing dispatch gate)
**Full ruling ledger:** Claude's memory file `/areas/voxel-castle-game.md` + `docs/kernel_v0_spec.md`

## Working process
- Will designs and rules everything; Claude transcribes rulings into spec and code.
- Loose ends are presented as multiple-choice options; Will picks or invents.
- Adoption bar: nothing enters because it's Will's research — it must materially
  beat the existing method on a measured test. Negative results stay in the repo.
- Commit as work is produced, without being asked.
- Known failure mode to watch: Claude has twice attributed its own suggestions
  to Will (repetition ruling; half-hour rule). Challenge attributions.

## Design spine (one breath each)
Bounded sandbox — design the walls and the sand, never script the play.
Chess shape — finite legal moves; value is positional. Circuit/potentiometer —
Away is potential, Home the return, design the impedance; both R→0 and R→∞
lose. Bloodlust universal; orders are impedance (constrain HOW, never WHETHER).
Order := (scope, release), release must be x-or-y guaranteed, order-lock until
release, capacity by rank, scope attenuates. Perception is a capacitor
(front/periphery arcs, charge, decay); marginal contact unifies angle and
distance. Eye = stack height + 1: height is the sole source of cover. Gates
are composed (portcullis/passage/doors). Every tunable is a CONFIG parameter
for the LLM R&D phase; the fresh-player condition gates all designed mechanics.

## Module map (src/fortresslab_mini/)
| module | job | notes |
|---|---|---|
| kernel.py | state, tick resolution, terminals | contact = Chebyshev ≤ 1, both die |
| solver.py | exact-rational simultaneous LP | conformance instrument ONLY; keeps Fractions by design |
| worldmap.py | terrain, eye-height LOS, exposure | digit legend `1`-`9` = tall stone; bounds-safe accessors |
| enemy_brain.py | Dijkstra cost field, breach ranking | cost = 1 + breach + λ·exposure |
| orders.py | grammar, validator, executor, lifecycle | generalised terms/comparators; NO lookup tables |
| sim.py | the tick loop + replayable trace | fog defaults OFF (control); cadence behind `acts_this_tick` |
| perception.py | the capacitor | RING compass arcs; CONFIG all-parameters |
| beliefs.py | belief field + holonomy instrument | diffusion transport; report-on-return fusion |

Tests mirror modules; `test_ladder.py` M0–M4 is the planner ladder (M4: height
alone casts shadow). `tools/warroom.*` is the 24×24 designer with height
stacks, cross-sections and subsurface. The planner the war room calls is
still 2D (documented in `tools/warroom.py`, not silent).

## Research import ledger
- **ADOPTED** — holonomy/closure instrument (`beliefs.py`, commit 71e767f):
  zero holonomy on a correct model; loop residual = model+filter error,
  localised; conformance tests permanent.
- **REJECTED** — closure-driven patrol dispatch: rotation 62.8 vs mass 65.9 vs
  residual 68.0 mean latency over 21 scenarios; uniform destination posterior
  makes coverage minimax-optimal. Door back in: reachable-set directional
  inference, re-facing `closure_bench.py`.
- **IDENTIFIED, unbuilt** — k-ellipse Weber siting (U-0878/U-1204); K_G balance
  audit (U-0024 + three-channel + U-0226 isolation); Local Curvature Calculus
  for design-space faces (U-0535/U-0650/U-0646); LloydFlow cross-ratio sector
  discovery; centrifuge hypothesis selection (U-0412, probation). NOT
  transferable: Galois/monodromy superstructure; LloydFlow RK4 machinery.

## Open rulings (Will's queue)
1. **LIVE — fogged search:** under fog, unengaged units with no contact have
   no goal; the sim stalls. Proposed: terrain-objective seeking (castle/camp
   as known landmarks). Awaiting ruling.
2. Gate arrow-transparency (gates currently block movement, not sight).
3. "Door" block type — Claude's addition, needs ratification.
4. Trauma floor, iff the aptitude system is ever built.

## Outstanding from last session
- Will's flat war-room playtest (interrupted by a since-fixed IndexError —
  re-seal the saved layout; two tower-stub archers were nearly blind before
  the eye-height fix, fine now).
- Watchmen and messenger routes are placeable but inert.

## Next build rungs, in agreed order
1. Cheap 2.5D planner half: column breach cost + walkability over stack tops —
   heights then fully matter to the verdict the war room shows.
2. Trace-and-scrub visualiser (Door Kickers style): replay a recorded trace,
   never live-stream; cones white front / grey periphery / orange identified /
   purple presence-cooldown; sightings already carry arc + reason.
3. Commander pipeline: beliefs → COA templates → variance-as-risk evaluator →
   receding-horizon loop clocked by messengers. Fractal instancing at
   Captain/Sergeant scale inside the scope lattice.
4. Shot-window exposure upgrade (archer = one arrow per draw) → the diversion
   emergence test: two men crossing one window beat one, by arithmetic.
5. Better Door replanning test, steerable-order variant (recall clauses are
   legal release branches within the x-or-y rule; steering costs a live
   messenger arriving).
