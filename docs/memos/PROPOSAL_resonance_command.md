# PROPOSAL — The Resonance Command System

**Status: PROPOSITIONAL. Not ruled, not implemented, not adopted.**
Author: Will, 26 Aug 2026. Transcribed by Claude.

This document is deliberately self-contained and quarantined. The ruled
design — the discrete order grammar in `orders.py` with its validator,
lifecycle and 147 green tests — remains **the live system** and is untouched
by anything written here. If resonance proves the wrong direction, delete
this file and nothing else changes.

Will's framing: *"I'm working out the details as I go, so we will have to see
how this system works in practice and adjust or amend if required."*

---

## 1. The core idea

Music theory as the logic mechanics of command.

**The chain of command is the signal.** Only commanders produce signal. Every
link in the chain is a **modulation or echo** of that signal, never a new
signal.

Each set of orders a commander issues is produced as a specific tone or
harmony — ranging from simple frequencies through complex chords to scales.

- **Home Commander issues orders in the MAJOR keys.**
- **Away Commander issues orders in the MINOR keys.**

The game map becomes a **resonance chamber with two conflicting signal
sources**.

## 2. Locations, tuning, and navigation

Each location corresponds to a **bass tone**. Lower frequencies emit longer
sine waves that travel further, so a unit can orient itself by moving toward
**increasing resonant harmonic quality**.

When a commander issues an order requiring a unit to be posted at a specific
location, that location becomes **tuned to resonate and harmonise to that
order**. As a unit approaches, the **higher register frequencies progressively
improve the overall resonance** — which is how order priorities and release
conditions scoped to location and duration are distinguished from one another.

**Locations always resonate the harmonic fundamentals. Release conditions
gate on the extensions.**

The more complex the order, the more complex the order signal. **All units
seek the direction of maximum harmonisation.**

### Worked example (Will's)

The Home Commander directs a company to station around the main gate and
remain until either the gate is breached or they lose more than half their
men.

The order is issued; the gate location becomes fine-tuned to resonate those
orders. The gate area emits the **root, major 3rd and major 5th**; the
**release conditions emit the extensions**.

## 3. Emission, resonance, and the chain

Each unit **emits the same frequencies as the order** it is under.

The chain of command is what **maintains signal amplitude**. A unit cut off
from the chain has dropped its connection to the master signal: it **stops
emitting and only resonates** to the signal. It can therefore maintain its
orders for as long as the location continues to emit the harmonic frequencies
it resonates to.

When orders are completed, the **harmonic content simplifies** in accordance
with fulfilling and completing them.

## 4. Opposition — cancellation, not damage

**Units have no HP; interference never causes damage.** This is signal
mechanics, not combat.

Each unit broadcasts its own order's unique frequencies as a **sine wave**.
An enemy unit, under its own orders, broadcasts **180° out of phase**. Where
peaks and valleys line up they **cancel**, reducing the harmonic content of
the signal that unit is producing.

**That cancellation IS the unit's perception.** The unit actively attempts to
remove whatever is interfering with the quality of its harmonisation.
Perception and hostility are one quantity, not two systems.

**Order complexity governs how sensitively a unit senses interference.**

**Resonance does not care about phase** — it only reflects and absorbs — so
both sides can resonate to the same location. Both sides ordered to the castle
gate emit the gate location's fundamentals, which makes enemy proximity a
direct opposition to the main resonance of each side's orders.

**Gain and amplitude of each side's sine wave scale to the strength and
proximity of their numbers**, and **the stronger cancellation source
determines a unit's offensive priority**.

## 5. Loss of a location

Extensions sit in **higher frequency bands**, are **less susceptible to
cancellation**, and so remain present and distinguishable under opposition.

Consequently an order under pressure **degrades toward its own release
condition**: the fundamentals go first, the extensions last.

But **losing the fundamentals is itself the signal that the location has been
lost** — and a release condition gated on losing a location therefore **kills
the extensions too**. Losing the gate to the enemy immediately kills the
location's resonance.

One signal does three jobs: it is the order's content, the unit's perception
of whether the ground still holds, and the trigger that ends the order.

## 6. The clock is not gutted

Orders can still be conditioned on specific time-of-day events. The commander
can have **any part of the order's frequency bands filtered inline with what
time it is** — so a contingency branch is simply inaudible until its hour.

**Messenger routes carry a rolling band-pass filter linked to the game
clock.** The messenger is *pushed along* the route in lockstep with the
intended schedule, because **the resonance behind him is worse than in front**.

*Claude's note:* scheduling stops being a timetable a unit consults and
becomes a gradient that carries him. A messenger delayed by a detour needs no
rescheduling logic — the sweet spot has moved on and the gradient still points
at it.

## 7. Attrition (confirmed reading)

Since amplitude scales with the strength and proximity of numbers, a company
that loses half its men **halves its own emitted amplitude**. A release gated
on half losses therefore fires when a unit's own signal drops below a
threshold of what it was — self-cancellation by subtraction rather than by
opposition.

---

## 8. What this system unifies

Every predicate class in the ruled grammar becomes a **filter operation on one
signal**. Nothing ever queries the world; a unit only listens, and the world
filters what it hears.

| ruled grammar predicate | resonance mechanism |
|---|---|
| location / region scope | bass tone gradient; harmonic quality increases on approach |
| clock, time-of-day | band-pass gating linked to the game clock |
| elapsed / schedule | rolling band-pass along a route |
| enemy count, contact | phase cancellation; strongest canceller = priority |
| own losses | fall in own emitted amplitude |
| order completion | harmonic simplification |
| loss of the objective | fundamentals fall silent; extensions die with them |

### Ruled behaviours the metaphor independently re-derives

These were all ruled *before* the resonance idea existed, which is the
strongest argument in its favour:

1. **Stale-order persistence** (a company continues after its officer dies)
   = cut from the chain, stop emitting, keep resonating while the location
   sings.
2. **Scope attenuates, never amplifies** = amplitude is maintained by the
   chain and can only fall as it descends.
3. **Self-directed units** (unrestrained bloodlust after losing the command
   chain) = losing the master signal.
4. **Guard locality (GUARDLOC)** dissolves rather than being fixed: there is
   no ground truth to leak into a guard, because a unit's only input is its
   own signal quality.

---

## 9. Open objections — the case against, kept honestly

Per the standing **adoption bar** (nothing enters for being elegant; it must
materially beat the existing method):

1. **Expressiveness gap.** The ruled grammar composes arbitrary predicates
   with and/or/not. The canonical 10 am contingency order is a five-branch
   tree with nested detachments. Whether harmony can carry that without
   degenerating into a frequency→predicate lookup table — the exact thing the
   generalised grammar was written to abolish — is unproven.
2. **Cost of replacement.** `orders.py` plus validator, lifecycle and 147
   green tests would be rewritten.
3. **Unproven in practice.** Will's own position: work out the details as we
   go, see how it behaves, adjust or amend.

**Retracted objection:** Claude initially argued interference conflicted with
the ruled dead-short contact model. That was Claude importing damage into a
mechanism that never mentioned it. Withdrawn — units have no HP and
cancellation is informational only.

## 10. The fallback split (Claude's proposal, NOT ruled)

If resonance does not survive as a replacement, it may still be worth keeping
as a layer:

- **Grammar = the score.** Composition and validation stay discrete, legal
  and tested.
- **Resonance = the performance.** Sub-order execution: formations, spacing,
  cohesion, persistence when cut off, the fold-in of self-directed units.
- **Sonified war room.** Major versus minor as the two sides' identity; a
  castle you can *hear* going dissonant sector by sector.

## 11. If adopted, first things to build

1. A resonance field over the map: per-location bass tone; harmonic content
   as a function of position and the orders tuned there.
2. Emission and amplitude per unit, scaled by chain connection and numbers.
3. Phase cancellation between opposed emitters; strongest-canceller targeting.
4. Band-pass filtering driven by the game clock; the rolling route filter.
5. A translation test: express the canonical 10 am order in resonance terms
   and check the resulting behaviour against the existing order tests. **That
   test is the adoption bar for this proposal.**

---

## 12. Computational cost — does "trivial overhead" track?

Will's claim (26 Aug): once matured, this can be a sophisticated and powerful
game logic system while being trivial in computation. **Assessment: yes, with
two conditions and one hard limit.**

### Why it is cheap — the field formulation

If the field is **steady-state superposition**, nothing is ever propagated
through time. Each tuned location contributes a closed-form attenuation per
band; the field is the signed sum.

Store a per-cell band vector. On a 24×24 map with 12 bands that is 6,912
floats — a texture. Rebuild by splatting each source: 576 cells × ~20 tuned
sources ≈ 11.5k splats per rebuild. Every unit then does an **O(1) lookup**
plus 8 neighbour reads to find its gradient.

Direct per-unit evaluation is comparably trivial: 130 units × 20 sources ×
12 bands ≈ 31k multiply-adds per tick. Microseconds in numpy.

Phase cancellation costs nothing extra: Home and Away are 180° apart, so
opposition is a **signed sum per band**, not a simulation.

**Compare what it replaces.** Every unit currently runs guard evaluation
against the world each tick. The field turns that into a texture lookup. It
is plausibly *cheaper* than the ruled system, not merely comparable.

### Condition 1 — the field must follow WALKABLE paths, not acoustics

If the bass tone propagates acoustically — through and over walls — units
following the gradient will walk into stone. The field must attenuate along
**traversable** paths.

Which means the bass gradient is the **existing Dijkstra cost field**, with
harmonic content layered on top. Already built, already cheap, already the
thing the enemy brain uses. This is the single most important implementation
note in this document.

### Condition 2 — reflections must be precomputed, or dropped

"The map becomes a resonance chamber" implies reflection off geometry. Real
reflection is room acoustics: expensive, and the one part of this that could
blow the budget.

The escape is already ruled: **no wall repair**, so castle geometry is
**monotone** — it only ever loses material. So the location→cell transfer can
be precomputed once at seal and patched incrementally when a wall falls.
Rare, local updates on static geometry.

*If reflections are dropped entirely and attenuation is purely geodesic, cost
is trivial with no precompute at all.*

### The hard limit — bit depth, not cycles

The real constraint is **not** computation. It is how many distinguishable
orders fit in the frequency space. Finite bands and finite distinguishable
intervals mean a finite vocabulary of expressible orders.

This is the expressiveness gap of §9 restated in engineering terms: the
system's ceiling is not speed, it is **how much order can be encoded in a
chord** before two different orders become indistinguishable to a unit that
can only listen.

**Conclusion:** the compute assumption tracks. Steady-state superposition over
the existing cost-field topology is cheap enough to be free. Whether the
system is *sophisticated enough* is a separate question, and it is answered
by the §11 translation test, not by profiling.
