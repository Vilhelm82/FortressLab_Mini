# The Resonance Command System

The command and perception system for FortressLab Mini. Orders are
performances, not prose: a commander tunes a location and states what would
end its worth, units hear it and act, and everything they know comes to them
as sound.

The system covers **orders and perception**. Combat is unchanged: contact at
Chebyshev ≤ 1 kills both, units have no hit points, and nothing here alters
that.

---

## 1. The idea

The chain of command is a signal. Only commanders produce it; every link
below modulates or echoes, never originates.

- **Commander** — the source.
- **Chain of command** — an instrument cable. It carries and radiates
  nothing, so command itself is silent and undetectable.
- **Units** — the speakers. The only things that make sound.
- **Locations** — the cabinets. Where a signal resonates, and how well.

The wrong location is the wrong tuning: a badly built cabinet that muffles or
hollows out the signal's range.

Home sings in major keys, Away in minor, 180° out of phase. Both sides read
the same map addresses, so no two commanders can disagree about what a place
sounds like.

---

## 2. Addressing

The map is divided into **up to twelve regions** by whoever designs it. A
small castle may use four and leave the rest of the space unused. The game
assigns which fundamental each region receives; the commander never chooses
notes.

**A region is a bass tone.** Twelve of them, all inside a single octave, so no
harmonic of any lands on another and exact-frequency matching is unambiguous.

**A post is a dyad**: the region's root plus one diatonic degree, voiced above
the stone cutoff. Six degrees per region, so **72 addresses**, plus twelve
region-level addresses where the bass sounds alone.

Addressing is postal — country, postcode, street, number. The root says which
region and carries everywhere; the specifier says which post and carries only
so far.

**An order layers notes above that address.** Each additional layer adds a
note, so the vocabulary is every subset of the six non-root degrees: 64 chords
per region, **768 order signatures**. Order complexity is therefore capped at
six layers by the scale itself.

Consonance within a chord is correct and wanted. A chord is one structured
address whose notes are meant to fuse, not rival addresses competing for
attention.

### The octave stack

Depth is authority. Lower is stronger and carries further.

| band | role |
|---|---|
| **location root** | the region — strongest, penetrates stone |
| **leader** | the sergeant or knight commanding a company |
| **dyad specifier** | the post — blocked by stone |
| **extensions** | conditions and tactics |

The base pitch is arbitrary; one is picked and everything sits above it.

---

## 3. Propagation

Sound takes **the path that delivers the most energy**, not the shortest one.
A long way round through open air beats a short way through stone whenever the
material eats more than the extra distance does.

Each band propagates separately, because decay and transmission both differ by
band:

- **Higher bands die faster with distance.** That is the distance low-pass:
  far away you hear only the bass.
- **Stone absorbs everything above the cutoff.** The region penetrates it; the
  post does not.
- **Timber leaks.** It passes some of every band, so a timber wall gives away
  what a stone one hides.
- **Earth stops everything.** The ground is not a shortcut.

Nothing reflects. The specifier reaches the whole map anyway, simply by
travelling every open route there is — out of a door, along a corridor, over a
parapet. Its gradient at any cell points back along the way it actually
arrived, which is the way in.

**One mechanic covers sight and hearing.** There is no separate visibility
system: material transmission is the low-pass, and the low-pass is everything.

### Consequences

- **Material is a perception design decision.** Timber is cheaper and faster
  but leaks the detail of what stands behind it; stone is opaque but costly.
- **An enemy outside the walls hears which region is being reinforced, never
  which posts.** Stone gives away the sector and hides the detail.
- **Distance and material are confusable.** Both act as low-pass, so a muffled
  signal is either far away or behind stone. The classic detection ambiguity
  falls out of the physics.

---

## 4. Navigation

Two bands, two jobs:

| band | crosses stone | what a unit gets from it |
|---|---|---|
| **root** | yes | a **bearing** — which region, from anywhere, constant |
| **dyad specifier** | no | a **route** — it arrives only along open ways |

**The rule.** A unit steps to the neighbour where the specifier is loudest;
where two answer equally, it takes the one where the root is louder. No map,
no pathfinding — it compares what it can hear from where it stands.

**Every location a unit must path-find to has to be a dyad.** A bare root
names an area and stops there.

**Units are their own source.** A unit sings its part and navigates by what
comes back, as a bat crosses a cave. An unoccupied post is not silent; it is
unexcited, and the unit excites it.

As a unit approaches, higher registers progressively resolve: far off it knows
only the region, on approach the post, closer still the order's extensions.
Coarse to fine, out of one cutoff frequency rather than a wayfinding layer.

**Harmonisation sets the destination; least detection selects the route.**

### Cohesion

Units singing the same part reinforce each other's returns, so a company sees
further than a lone man and a scattered remnant sees worst of all. Staying
together is simply how you see — no formation rule required.

Interference degrades navigation as well as focus: an enemy cancelling your
bands takes your bearings along with your attention.

---

## 5. Perception

Four channels, ranked by how strongly they draw a unit's attention.

| channel | strength | behaviour |
|---|---|---|
| **looking** | strongest | own beam: directional, line of sight, inside the cone |
| **interference** | strong | opposed signal cancelling your own |
| **hearing** | scales with proximity | omnidirectional, reaches at any range if nothing competes |
| **being looked at** | weakest | felt only from inside the other's cone; **silent at 180°** |

**Perception is a beam, not a wave** — a laser pointer, not a floodlight.
Height is in the geometry, so a man on a tower sees over a curtain that blinds
one standing beside it, and a man one cell back from the parapet is blinded by
his own wall.

**Hearing is a wave, weighted by angle.** A unit hearing something to its
right while looking at something ahead stays on what it sees until the ratio
tips. The ratio weakens with angle off centre and is weakest at 180°, so
behind is the last direction a unit reacts to.

**The stealth kill is doubly derived.** From directly behind, the target's
hearing ratio is at its weakest angle *and* the attacker's beam registers as
nothing.

### Masking

A louder nearby signal buries a quieter one; in silence even a distant voice
eventually draws attention. So the sneaking route runs **alongside noise, not
through quiet** — and a company wanting to move unseen has reason to want a
loud engagement elsewhere.

This leaves a real navigation problem with a non-trivial optimum: noise means
masking, but noise also means men.

### dB gating

A commander may gate any unit's voice, reducing how far its song travels. This
tunes stealth **inside** the system — a quiet unit is still a singer, not an
exception.

**The perception beam is not gated.** A quiet unit still sees where it is
going and still catches anything crossing its cone. What it loses is acoustic
*resolution*: with a soft voice only the lowest register returns, so it
navigates on bass alone.

**The pulse.** For a richer return a unit sings louder, and the higher
registers come back. Any enemy nearby hears that pulse. Detail is bought by
announcing yourself.

A gated commander attenuates only his own location's resonance, never the
chain's amplitude — the cable carries regardless.

---

## 6. Opposition

Each unit broadcasts its order's frequencies as a sine wave. Opposed units are
180° out of phase; where peaks and valleys align they cancel, reducing the
harmonic content of the signal that unit is producing.

**That cancellation is the unit's perception.** A unit acts to remove whatever
is degrading its harmonisation — perception and hostility are one quantity,
not two systems. **The stronger cancellation source is its offensive
priority.**

Cancellation happens only on **shared bands**. No shared song, no
interference.

**Order complexity governs sensitivity**: a richer performance has more to
lose and notices its loss sooner.

**Resonance itself is phase-blind** — it reflects and absorbs only. So both
sides can resonate to the same location, which is what makes enemy proximity a
direct opposition to each side's own orders. Gain scales with the strength and
proximity of numbers.

Nothing here does damage. Units have no hit points; cancellation is
informational.

### The leash

A unit sits in a stable orbit around its post. An enemy's interference expands
that orbit outward to meet him, so **how far a unit will chase is the ratio of
post amplitude to interference amplitude** — a leash with no leash rule.

Consequently **discipline scales with post proximity**: a man standing on his
post resists being drawn, a man at the fringe of its influence is easily
pulled. Where a commander posts his men sets how disciplined they are.

**Walls preserve discipline.** An enemy behind stone produces no interference,
so cover protects a defender's performance and not merely his body.

---

## 7. Orders

An order is a **performance**: an address, plus notes stating what would end
its worth. The commander names where and what, and the field does the rest.

**Release conditions are not conditions to wait for.** They are the drop in
richness that motivates relocation. When part of a performance can no longer
sound where a unit stands, the unit seeks the place where it can.

Three mechanisms kill richness, all environmental:

| mechanism | what happens |
|---|---|
| **silence** | the objective is lost — its fundamentals stop |
| **cancellation** | an opposed signal is present |
| **attrition** | own amplitude falls as men are lost |

Nothing consults a clock. Time of day is not an orderable condition.

**Losing the fundamentals is itself the signal that the location is lost**, and
a condition gated on that kills the extensions with it. One signal does three
jobs: the order's content, the unit's perception of whether the ground holds,
and the trigger that ends the order.

**Extensions survive cancellation better** than fundamentals, sitting higher
and being less easily cancelled. So an order under pressure degrades toward
its own exit rather than into noise.

**Completion simplifies the chord.** A rich order sheds notes as its
conditions resolve, and its shape at any moment is its remaining state. The
music is the state machine.

**Complexity is selectivity, not instruction count.** A rich performance is a
narrower filter on acceptable locations: simple orders make a unit mobile and
substitutable, rich ones make it committed and specific.

Locality is structural. Every condition is something a unit hears or knows of
itself, so there is no ground truth for an order to read.

### Parts

An order may stipulate extensions to any combination of units within a
company, so a company's score is a **set of chords sharing a root**. The
company is administrative — spawn, leader, shared root. The part is tactical —
what these particular men do.

**Parts are addressed by type and count, never by identity.** "Two
men-at-arms," never a named man. A part is therefore a filter over the roster
and heals itself when a man falls.

### Re-tasking

A location's tuning and a unit's performance must match for attraction to
occur. Changing one without the other does nothing, so **a commander cannot
pull companies about by retuning the field** — new orders have to be carried
to them. Re-tasking remains a physical act performed by a man who can be
killed.

---

## 8. Companies

**A company is a choir.** Its leader sings the octave above the location root
and the company follows him as it would follow a tuned post.

**The handoff needs no rule.** As the company nears its destination the
location's deeper root grows until it drowns the leader out, and the men fold
off to their posts. Depth is authority; amplitude decides.

### When the leader dies

The company continues, following the root. With no leader maintaining the
signal, a rising filter narrows what the men can hear, and **each time it eats
the current root the next note shifts into the root slot** — the dyad becomes
the root, then an extension, and so on. With only a root left, a man seeks the
strongest signal matching it.

Since extensions exist at every location, the unique root-and-dyad pair is the
barrier a man must cross to join another company. A degraded man therefore
drifts toward **matching roles**, not random ones.

### Attraction

A stray is drawn to the company whose chord contains its note **and which has
a gap**. A full company sings a complete chord — nothing wanting, nothing a
newcomer can add. An under-strength one is an unresolved harmony, and
resolution is what a stray seeks.

Attraction is by **harmonic complementarity, not amplitude**. Two quantities
stay separate: dominance scales with numbers, attraction with need. A big
company holds ground better; a hollow one calls louder to the man who can
complete it.

### Messengers

A messenger runs the same logic as any unit. The difference: **arrival
replaces his root.** A route is an ordered stack of roots, and reaching a
checkpoint drops the current one so the next stop becomes it.

The root slot is a cursor, advanced two ways — by arrival, which is progress,
and by the filter, which is decay. The same operation in opposite spirits.

### The sergeant's licence

A company leader may **modulate and attenuate** his company's signal, never
change it. Delivery and amplitude are his; the harmonic content — the order
itself — is not.

---

## 9. Routing

**Least detection is the routing preference of all units**, not a stealth
special case. A stealth kill is therefore deterministic from the environment
rather than a coded behaviour: if a covered approach exists, someone finds it.

Consequences: watchman placement shapes attack routes by gradient rather than
by rule, and whether a castle admits a covered approach to its war room is a
property of what was built.

Seeing and being seen are asymmetric. Looking is the strongest channel; being
looked at is the weakest. **A unit can be spotted clearly while barely
registering that anyone is watching.**

---

## 10. Reproducibility

Every cell records only **how far its signal deviated from baseline, and at
what tick**. Most cells at most ticks deviate not at all, so the trace is
sparse and a quiet sector costs nothing. Nothing is random, so the same trace
replays identically.

One substrate serves three purposes that were otherwise three systems:

| view | what it is |
|---|---|
| replay | the deviation log, played back |
| intelligence | what a unit heard — the deviations reaching its cell |
| the war-room map | a commander's accumulated subset of that log |

The log is derived state: it gives perfect playback and verification, but
branching still needs the seed — initial geometry, siting, and the orders
issued. Both are small.

---

## 11. Compute

The field is steady-state superposition: nothing propagates through time.
Each band is a shortest-path solve in −log(amplitude) space from each source,
and a unit reads its own cell and its neighbours.

The binding limit is not speed but **bit depth** — how many distinguishable
orders fit in the frequency space. That limit is wanted: the vocabulary is
finite by design.

---

## 12. Open

**What a commander is allowed to write, and what authors it.** The whole
command layer waits behind this: the order representation, the commander, and
the interface.

**What a unit does when it hears a location clearly but has no local slope
toward it.** In three dimensions sound crosses roofs as well as doorways, so a
tall building can put a listener in a region of uniform strength with no
gradient in it. The rule of §4 holds wherever the specifier's loudest path is
walkable; this is where it does not.
