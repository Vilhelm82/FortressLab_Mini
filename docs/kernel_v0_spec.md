# Kernel v0 Specification — "The Dead Short"

**Status:** items tagged `[impl]` are implementation fiat and open to veto.
Everything else transcribes rulings of 2026-08-20.

**Purpose:** the smallest legal game. A proving ground for simultaneity,
contact lethality, bloodlust, and termination. Every later system — orders,
ranks, credits, perception, architecture, engines — is impedance layered on
top of what this document defines. The kernel agent *is* the feral unit of
the full game, and also its ground state: strip a commander of everything and
this is what remains.

---

## 1. World

- **W1.** Cells indexed by integer coordinates. Featureless: no terrain, no
  occlusion.
- **W2.** The map is **finite**, and its edge is an array limit, not a game
  element. "Infinite" in the original ruling made the point that the boundary
  is arbitrary and strategically irrelevant. Map size is a swept parameter;
  boundary irrelevance is *certified by test* (T3), never assumed.
- **W3.** At most one unit stops on a cell in any live state.

## 2. Forces & units

- **U1.** Two sides: **Home** (the castle) and **Away** (the siege army).
- **U2.** v0 rosters: one **Commander** each, optionally one **Man-at-Arms**.
  The zero-soldier configuration is Game One.
- **U3.** All units have identical stats — all men are created equal. Zero HP:
  any unit in lethal contact is removed. The Commander differs only in that
  the win condition points at him. He wears no armour.
- **U4.** v0 has no orders, no ranks, no credits, no perception state. Every
  unit is **feral** — pure bloodlust, universally mutually aware.

## 3. State

- **S1.** A state is the set of living units, each with side, kind, and cell.
  No side-to-move (simultaneous game), no tick counter (Markov).
- **S2.** `[impl]` Canonical anchoring and dihedral symmetry reduction are
  **optional optimisations only**, valid in the interior of a finite map.
  Not used in v0.
- **S3.** **Live-state invariant (Tier 1):** no hostile pair at Chebyshev
  distance ≤ 1. Such pairs die during resolution, so a live state holding one
  is unreachable. Property-tested, not assumed.

## 4. Actions

- **A1.** Each living unit takes exactly one action per tick: a step to one of
  its 8 Moore neighbours, or **Stay** (null displacement). 9 actions per unit.
- **A2.** Stay is legal, carries no conditions, and has no special status. It
  is a physical primitive, not an instruction. No rule may make standing still
  illegal — compulsory movement would make sentries, held positions, and
  ambushes unrepresentable.
- **A3.** *Naming reservation.* **Hold** is reserved for the orders rung,
  where `order := (action scope, release conditions)` and a bare Hold is
  malformed. The tick-level primitive is never called Hold.
- **A4.** **Occupancy is a property of stopping, not transit.** No two units
  may stop on the same cell. A cell held by a unit that is staying is not a
  legal destination; a cell held by a unit that is itself moving off *is*.
  Units in transit pass freely through each other. No transit reservation, no
  swap-through blocking, and therefore no collision resolution anywhere:
  illegal configurations are excluded at legality, never resolved at runtime.
- **A5.** A side's **joint action** is one action per living unit, subject to
  A4. Both sides choose simultaneously. Friendly destination-distinctness is
  intra-side bookkeeping and crosses no information between sides, so
  simultaneity is untouched.
- **A6.** *Consequences, not rules.* A file of units advances one cell in a
  single tick. A one-tick friendly cell exchange is physically legal. What
  keeps a posted man at his post is the **order-lock**, not the movement
  rules — hence *relief*, a command procedure (§10).

## 5. Tick resolution

Deterministic, order-free, integer-only. Four stages:

1. **Intent.** Each unit's destination is its own cell (Stay) or a neighbour.
   Friendly conflicts cannot arise: A4 excluded them from the action space.
2. **Placement.** Final positions set.
3. **Contact.** Every hostile pair at Chebyshev ≤ 1 — overlap or adjacency,
   "contact is contact", no collision geometry computed — both die. All deaths
   simultaneous.
4. **Terminal check.** See §6.

Hostile swap-through is unreachable: hostiles never begin a tick adjacent
(S3), and any tick bringing them within 1 kills both. A Man-at-Arms reaching
the enemy Commander trades 1-for-1 and *ends the game* — so a Commander's
entire defence is never being contactable by any aware enemy unit. The war
room is derived from this fact, not decreed.

## 6. Terminal states and values

- **T1.** Home Commander dead, Away alive → **Away wins** (−1).
- **T2.** Away Commander dead, Home alive → **Home wins** (+1).
- **T3.** Both dead on the same tick → **Tie** (0). The dead short.
- **T4.** No surrender, no resignation, no clock, no draw by agreement. A
  commander whose force is spent goes feral — in v0 every commander already is.
- **T5.** Non-termination: ruled "a situation that will never occur", and the
  reason is stronger than graph theory. Cycles exist in the state graph and
  always will, but nothing that walks it can produce one: producing a cycle
  requires a creature capable of declining to close, and no such creature
  exists here. The solver carries an internal convention for unresolved loops
  which must never bind on a played line — promoted to a test, not trusted.

  **Known trap:** valuing non-termination as 0 conflates *both commanders dead*
  (the Tie) with *nobody dead*, which are opposites under bloodlust, and hands
  a losing commander a free draw by running. Any solver that models commanders
  as free optimisers will take it. See §7.

## 7. Agent layer — bloodlust and the potentiometer

- **B1.** The value layer knows only §6. Backward induction from "standing over
  the body" is the entirety of motivation. No desire module exists.
- **B2.** `[impl]` **Bloodlust tiebreak:** among value-equal actions, close the
  distance to the enemy commander; remaining ties break by fixed action order.
  This is what makes two bare commanders charge rather than circle.
- **B3.** **Scope of B1–B2.** Zero-hesitation bloodlust is the default once all
  impedance is removed — a commander must exhaust his offensive before it is
  unshackled. The whole game space is a **potentiometer**: full resistance at
  the start (all credits unspent, every environmental element intact), and
  commanders slide the wiper. The aim is not to blitz to zero, because the
  resistance is also the **load that does the work**. Both ends lose:
  R→0 is the dead short, R→∞ is the tomb. v0 sits at R = 0 by construction.
- **B4.** Survival is **instrumental, never terminal** — "must kill, but if I'm
  dead I can't kill". Risk shapes *how* a unit attacks, never *whether*. One
  objective in the whole game: no morale system, no caution slider, and rout
  emerges as the kill-drive taking a longer road.

## 8. Solver — scope

- **V1.** Zero-sum, simultaneous, perfect information (kernel scaffolding
  grant; the world itself is not perfect-information).
- **V2.** Per state the stage game is a matrix solved exactly as a zero-sum
  game by LP over rationals. Integers and exact rationals only, no floats.
- **V3.** Global values by iteration to fixpoint.
- **V4.** **v0 is a conformance instrument, not a balance instrument.** With no
  impedance layer, the agents have no strategy space to optimise over — the
  value is determined, not chosen. Free-optimiser modelling at this scale
  invents behaviours (evasion) the design does not contain. The solver becomes
  a balance instrument once credits, orders, and terrain give a commander
  something to tune.
- **V5.** Port trigger: 5×5 with three units took ~232s in pure Python with
  `Fraction`. Any rung needing larger boards needs a fast core, cross-checked
  against this implementation on identical counts.

## 9. Verification

**Tier 1 — proof by induction (permanent).** Legality, resolution, invariant
S3, value definitions. The compass: prove the generator, and every state it
reaches is valid without being visited. You cannot verify a circle by checking
its points.

**Tier 2 — proof by enumeration (kernel scaffolding).** A luxury of smallness,
not the standard. Chess is unsolved and has never needed solving.
- **T0 Dead Short** — bare commanders, every separation → TIE, terminating in
  mutual death. *Weak by construction:* nothing here can produce a non-zero
  value, so an engine that always returned 0 would pass. The 2v1 probe is the
  discriminating case, and it returns +1.
- **T1 Mirror** — symmetric positions solve symmetrically. Engine bug detector.
- **T2 Termination** — no played line fails to terminate.
- **T3 Boundary** — optimal play never touches the edge; if it does, the map is
  too small and results are contaminated.

**Tier 3 — evidence by sampling.** Everywhere enumeration cannot reach.
Balance is measured, never proven: the target signature is an **inverted U** of
value against commitment rate. A monotonic curve means the rule set is broken
however elegant the physics reads.

## 10. Banked rungs (specced, not built)

Orders (`order := (scope, release conditions)`; bare Hold malformed; conditions
range over own-group attrition, world facts, area bounds; **release validity,
ruled 2026-08-20:** the release must be a definite outcome of the order —
success and failure both covered, guaranteed to trigger. At least one branch
must be verifiable by the unit from its own local observation. "Until recalled"
alone is malformed: a dead messenger soft-locks the company. "Until recalled OR
half losses" validates — one exit the commander controls, one the unit can
trigger itself. Malformed orders are unissuable: excluded at legality, never
punished) · scope lattice and
order-lock, where the release clause is the lock's key · relief as a command
procedure · ranks, armour arcs, movement cadence, ammo · credits (250,
non-renewable, spendable at any time), keep-spawning, promotion at the
difference, auto-join rally · perception capacitor, facing arcs, stealth kill ·
terrain, architecture, vantage height, tunnels · camp, tents as forward
reinforcement, engines, labour · the Castle/Attacker balance thesis.

## 11. Interface `[impl]`

    initial_state(config)              roster + starting offsets
    legal_joint_actions(state, side)   subject to A4
    resolve(state, ja_home, ja_away)   the pipeline of §5
    terminal(state)                    None | Outcome
