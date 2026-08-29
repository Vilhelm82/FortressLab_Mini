# FortressLab Mini — Session Handoff

**Repo:** `/mnt/fast/Work/Creative Projects/FortressLab_Mini` · **147 tests green**
**Tests:** `python3 -m pytest -q` · **War room:** `python3 tools/warroom.py` → :8770
**Bench:** `python3 experiments/closure_bench.py` (standing dispatch gate)

## Read these first
| doc | what it is |
|---|---|
| `docs/RULINGS.md` | **the complete authoritative ruling ledger** |
| `docs/memos/TWO_GAMES.md` | Game A / Game B definitions, modes, open items |
| `docs/memos/ESCALATION_LADDER.md` | 20-row ladder + gap register with statuses |
| `docs/memos/MEMO_2026-08-25_comms_and_spawn.md` | comms, spawn, the two memories |
| `docs/memos/MEMO2_2026-08-25_units_engines_fire.md` | units, ledger, engines, fire, ranging |
| `docs/memos/PROPOSAL_resonance_command.md` | **PROPOSITIONAL** — the resonance system, quarantined |
| `src/fortresslab_mini/config_balance.py` | every provisional number, all floats, LLM-sweep knobs |

## Working process
Will designs and rules everything; Claude transcribes into spec and code, and
presents loose ends as multiple choice. Adoption bar: nothing enters for being
Will's research — it must beat the existing method on a measured test.
Negative results stay in the repo. Commit as work is produced, unasked.
**Watch:** Claude has three times attributed its own suggestions to Will
(repetition ruling, half-hour rule, re-raising settled Game A scope).

## Module map (`src/fortresslab_mini/`)
| module | job |
|---|---|
| kernel.py | state, tick resolution, terminals (contact = Chebyshev ≤ 1) |
| solver.py | exact-rational simultaneous LP — conformance instrument ONLY |
| worldmap.py | terrain, eye-height LOS, exposure; digit legend for tall stone |
| enemy_brain.py | Dijkstra cost field `1 + breach + λ·exposure` |
| orders.py | grammar, validator, executor, lifecycle — NO lookup tables |
| sim.py | tick loop + replayable trace; fog defaults OFF (control) |
| perception.py | the capacitor — RING arcs, charge, decay |
| beliefs.py | belief field + `loop_residual` holonomy instrument |
| commander.py | decision loop v0 — quilt fusion, threats, lock-respecting tasking |
| config_balance.py | all provisional floats |

Tests mirror modules. `tests/test_war_college.py` = 11 **single-decision**
commander exams (the behavioural contract; sequence behaviour untested).
`tools/warroom.*` = 24×24 designer; its planner is still 2D (documented).

## Research import ledger
- **ADOPTED** — holonomy/closure instrument (`beliefs.py`, `71e767f`): zero
  holonomy on a correct model; loop residual = model+filter error, localised.
- **REJECTED** — closure-driven patrol dispatch: rotation 62.8 vs mass 65.9 vs
  residual 68.0 mean latency over 21 scenarios. Door back in: reachable-set
  directional inference, re-facing `closure_bench.py`.
- **IDENTIFIED, unbuilt** — k-ellipse Weber siting (U-0878/U-1204); K_G balance
  audit (U-0024 + three-channel + U-0226); Local Curvature Calculus for
  design-space faces (U-0535/U-0650/U-0646); LloydFlow cross-ratio sector
  discovery; centrifuge hypothesis selection (U-0412). NOT transferable:
  Galois/monodromy superstructure; LloydFlow RK4/CUDA.

## Open rulings (Will's queue)
**Blocking code:** GUARDLOC (internal `goto` guards read ground truth; only
releases are locality-checked — fix agreed in principle: locality on all
guards, "locally observable" includes watchman relay) · SELFORD (self-ordered
commanders/detached officers = restrained, vs self-directed remnants =
unrestrained).

**Structural:** UNDERPERC (perception is surface-only; mining invisible) ·
TENT (durability) · RETASK (orders flow outward by messenger only — coherent,
never formally stated).

**Recommended, awaiting ratification:** doors opaque / portcullis
arrow-transparent both ways · "Door" block type · blacksmith as a building not
a unit · sally as a pure order template · dig sound-presence for counter-mining
· carts capturable like the logbook.

**Note:** OBSCOST and DMGMODEL are **closed** — the first by the resonance
proposal's least-detection routing, the second by angle-of-attack.

## Next build rungs, in agreed order
1. **Blocking fixes**: GUARDLOC + SELFORD.
2. **Companies in `sim.py`** — officers, membership, lifecycle; the executor on
   real company objects (the sim only knows units today).
3. **Wire `commander.decide()` into the loop** — called on messenger arrival,
   actions applied. This is where the game starts playing itself.
4. **Messengers and the quilt for real** — circuits, one-way sync, logbook,
   30 s memory. Currently test fixtures only.
5. **Credits and keep spawning** — atomic pay + validate + deploy.

Then: 2.5D planner half (column breach, walkability over stacks) ·
trace-and-scrub visualiser (replay, never live) · shot-window exposure upgrade
→ diversion test · Better Door replanning test · **campaign/sequence War
College battery** (v0 is single-decision only; thrashing, memory of one's own
orders, feints and reserve discipline are untested).

## Outstanding
Will's flat war-room playtest (interrupted by a since-fixed IndexError —
re-seal). Watchmen and messenger routes are placeable but inert. The move
manifest for the LLM phase (thin legal-move list, distinct from the
implementation spec) is unwritten — writing it is itself a fresh-player test.
