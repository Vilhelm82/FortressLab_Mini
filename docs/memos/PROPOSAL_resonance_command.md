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

---

## 13. The Conductor and the Orchestra (Will, 26 Aug) — release conditions inverted

**The finite vocabulary is DESIRED, not a limitation.** Order mechanics must
be generalised and simple while still rich enough to cover the legal move set.
Location is covered (§2). Release conditions are what needs hardening — and
they should NOT be complex.

### The framing

**The Commander is the Conductor. The Castle is the Orchestra.** Both
commanders compete to be the only performance audible in the auditorium.
**Kill the commander and the castle goes silent.**

Commanders use units to capture or remove areas of high resonance. The more
units present at a high-resonance location, the more dominant your performance
propagates. So dispatching units to those locations is high priority.

**Dead units cannot sing. Units with no location of resonance have low
amplitude.** A unit must be both alive and somewhere that contributes to the
performance's volume.

### The problem this solves

What happens when a location no longer resonates? The commander needs a way to
relocate units that introduces the least risk of losing them and **does not
fire prematurely**.

### Sheet music

The commander hands out **sheet music**: what to sing, when and where to sing
it, and when to transition to another resonator. **The environment reports
back** whether the unit is in tune, in time, at correct pitch and key.

- **Simple orders require a simple performance** — easily harmonised to
  *many* locations.
- **Rich orders require a rich performance** — satisfiable in *few*.

Once a rich performance can no longer be audible where the unit stands, the
unit **progresses to the next area with the most resonance for its required
performance**.

### The inversion

> **Release conditions are not something a unit must complete or wait for.
> They are the drop in richness in some part of its performance that motivates
> it to seek a better location.**

So all a commander does is: specify what areas resonate at the richness needed
to attract the units, then **attach specific complexities onto conditions that
will kill that richness** and thereby direct the units elsewhere.

The commander's act becomes **negative specification** — not "here is a branch
tree", but "here is what would make this place stop being right".

---

### Claude's readings (flagged as readings, not rulings)

**1. Complexity is selectivity, not instruction count.** A rich performance is
not a longer program; it is a *narrower filter on acceptable locations*. One
knob sets how pinned versus how fungible a company is. Simple = mobile and
substitutable; rich = committed and specific.

**2. The soft-lock rule dissolves.** The ruled x-or-y guaranteed-exit
requirement existed because "hold until recalled" could strand nine men
forever. Under resonance there is no waiting state at all: the gradient always
points somewhere. A unit that stays put stays because the location is *still
rich* — which is correct behaviour, not a lock. Order-lock likewise stops being
a rule and becomes physics: a unit cannot be re-tasked remotely because new
sheet music has to be *carried* to it.

**3. The release vocabulary may already be closed — at four mechanisms**, all
of them already specified elsewhere in this document:

| kills richness by | mechanism | §|
|---|---|---|
| time of day / schedule | band-pass gating on the clock | 6 |
| enemy presence | phase cancellation | 4 |
| own attrition | fall in own emitted amplitude | 7 |
| objective lost | fundamentals fall silent | 5 |

"Recalled" is not a fifth mechanism — it is **new sheet music delivered by
messenger**, a replacement rather than a release.

**4. The 10 am translation exposes one genuine gap: PARTS.** Translating the
canonical order, most of it falls out cleanly — the 11 am branch is a clock
filter, contact is cancellation, half-losses is amplitude, "all return" is
simply the keep being the next-richest resonator once the gate dies. But
*"send two men-at-arms back to clear messenger routes"* requires two men to
carry **different sheet music from the other seven**.

Which is exactly what an orchestra is: a section plays **parts**, not one
line. So a company is not a single voice, and the score must support voices
within a company whose richness conditions differ. **This is the first thing
to test if the system is adopted.**

---

## 14. CLOCK SCRAPPED (Will, 26 Aug)

**Ruled out of the proposal.** Orders bound to what time it is are neither
more convenient nor more practical than orders bound to environmental
conditions. §6's band-pass-on-the-clock and the rolling route filter are
**withdrawn**, and the §13 release table drops from four mechanisms to three:

| kills richness by | mechanism |
|---|---|
| enemy presence | phase cancellation |
| own attrition | fall in own emitted amplitude |
| objective lost | fundamentals fall silent |

All three are *things that happen in the world*. Nothing consults a clock.

### Consequences

**The canonical 10 am order is no longer canonical.** It was the fixture that
introduced diegetic clock predicates; under this proposal its 10 am and 11 am
branches are simply not expressible, and its content re-states as: hold while
the gate resonates, leave when contact or attrition kills the richness. The
§13 translation test survives — but the thing it now tests is whether the
*environmental* half was ever doing all the work.

**Messenger routes need a new motive force.** §6 had a rolling band-pass
pushing the messenger along in lockstep with a schedule. With no clock, what
draws a messenger along a route is unresolved — **the one genuine hole this
ruling opens.** Candidate (Claude's, unruled): a messenger's performance is
satisfied only by *fresh* resonance, so a location he has already sung at is
spent for him and the richest remaining point is always the next stop —
staleness as the gradient, with no clock anywhere.

**A "schedule" becomes an emergent rhythm rather than a timetable.** Circuit
period stops being set and starts being *measured* — a consequence of route
length and unit speed. Which is what it physically is.

---

## 15. The thesis (Will, 26 Aug)

> **Orders are performances, not prose. Then the units become like water
> filling a container.**

This is the plumbing philosophy applied to the command layer itself. Prose is
read and executed — it tells the water how to be water. A performance is
*sustained*, not followed: it is a state a unit is in, and the container is
the only thing that decides where it settles.

**What this kills:** the assignment problem. `commander.py` v0 currently
matches nearest-free-company to threat, one at a time. Under this thesis the
commander assigns nobody — he tunes locations, and distribution happens.

**The tension to resolve (Claude's flag, unruled).** Water levels out because
containers have *capacity*. As specified, §13 says more units at a location
means more dominant propagation — positive feedback, which clumps every unit
onto the single richest point. That is iron filings to a magnet, not water
finding level.

For water behaviour, richness must **saturate** with occupancy. The
orchestral answer is natural and already in the metaphor: **a part has a voice
count.** You do not need twenty cellists on one line. Once a part is fully
voiced, a further unit adds nothing to its own harmonisation and the next-best
resonator wins — and units distribute exactly as water does, filling low
places first.

**Unresolved:** whether saturation is per part (voice counts) or some other
mechanism.

---

## 16. Addressing — the map is a band, not one note (Will, 26 Aug)

**Different units sing different chords with different fundamentals.** The map
is not one sustained note; it is a band of instruments playing different
roles. All in harmony — but that harmony can be built from any chord, note or
pitch combination, and **each company is assigned a combination that attracts
it specifically to where the commander requires it.**

**Isolated units still sing a note** that can match and fold into another
company.

Two locations may share some overlap in what notes resonate, but **the
location carries the fundamentals, and the lowest notes push the most air.**
So filtering units to specific locations can be fine-tuned — up to a **ceiling
of how distinct each location and order set can be made distinguishable** to
the units you wish to control there.

### Consequences

**This resolves §15's distribution question — by addressing, not saturation.**
Claude flagged that positive feedback would clump every unit onto the single
richest point. It does not arise: there is no single magnet, because units are
not all listening for the same thing. The richest location *for company A* is
not the richest *for company B*. Capacity limits and voice counts are
unnecessary. **Distribution is a design act by the commander — he assigns the
chords — not an emergent physics.** Two companies given the same address will
converge; that is then his choice, not an artefact.

**Fold-in becomes selective.** The ruled auto-rally (a stray unit joins an
under-strength company within detection) gets its mechanism: a self-directed
unit has stopped emitting but still sings a residual note, and a company whose
chord contains that note can absorb it. So remnants flow to *compatible*
companies rather than the nearest one.

**Addressing is coarse-to-fine, by physics.** Bass travels furthest, so at
long range a unit can only tell *which location*. The upper structure resolves
on approach, telling it *which part* and *what conditions*. Navigation and
instruction are the same signal at two ranges.

**The failure mode is chord collision** — two locations addressed too
similarly will pull each other's units. That is a genuine mistake a commander
can make, and it is a *desirable* one: it makes the finite vocabulary bite,
and it makes clarity of command a skill rather than a given.

---

## 17. Scope, the ISCO, and absorption (Will, 26 Aug)

**Scope of the system: ORDERS and PERCEPTION only. Combat remains exactly as
ruled** — dead short, Chebyshev ≤ 1, both die, no HP.

**The direction of destructive interference attracts the unit's focus.**

**Location and orders prevent a unit abandoning its post**, because leaving
degrades its own performance: **proximity to the post scales resonance
amplitude.**

### The ISCO

A unit sits in a geodesic **ISCO around its resonating post**. An enemy's
destructive interference creates a gravitational shift that **expands the ISCO
outward to meet the enemy**.

Archers skip the whole shift — they simply shoot the enemy once it is in range
and perception. *(Archers are currently parked as a future implementation.)*

### Absorption

**Objects absorb all sound.** Walls and other structures **reflect no
frequencies**. Therefore **perception is solely directional.**

---

### Consequences

**The expensive branch of §12 is dead.** Total absorption means no room
acoustics, no reflection precompute, no transfer-function caching. Occlusion
and directional propagation only. The compute claim is now unconditional on
that axis.

**Engagement range becomes emergent — a leash with no leash rule.** How far a
unit will chase is the ratio of post amplitude to interference amplitude.
Nothing specifies pursuit distance; it falls out.

**Discipline scales with post proximity.** A unit standing on its post has
high amplitude and resists being drawn; a unit at the fringe of its post's
influence is easily pulled. So **where the commander posts his men sets how
disciplined they are** — and, one level up, the castle's geometry sets where
posts can be. A design consequence, not a stat.

**Ranged units hold formation; melee units get drawn out.** Archers satisfy
the remove-the-interference drive without moving, so their ISCO never expands.
One mechanism, two behaviours.

**Walls preserve discipline.** With no reflection and full absorption, an
enemy behind a wall produces no interference at all — so the wall protects the
defender's *performance*, not just his body. Cover becomes a command property.

### OPEN QUESTION (not assumed)

Does absorption mean **strict line-of-sight propagation**, or does the signal
travel along **open paths**, round corners, without reflecting?

- *Strict LOS:* a unit can only be attracted to a post it can see. Very
  restrictive inside a castle — a company could not navigate to a courtyard
  post from outside the gate.
- *Open-path:* the signal follows traversable air, which is the §12 condition
  ("the field must follow walkable paths") and makes interior navigation work.

This decides whether the resonance field is a visibility field or the existing
Dijkstra cost field wearing new clothes.
