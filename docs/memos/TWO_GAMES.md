# FortressLab Mini — The Two Games

Rev 2, 25 Aug 2026. One engine, two games. Everything below is either a
transcribed ruling or an **[OPEN]** item needing one.

## The relationship

**Game B is the engine. Game A is a mode built on it.** They share every
rule. What differs is who the player is and what they touch. The same rule
set must be legible two ways: Game A's player meets the rules **indirectly**
— through consequences, with the debrief as the entire teacher. Game B's
player meets them **directly** — drafting orders, reading the stale quilt,
feeling the latency. Game A can hide complexity behind AI competence; Game B
can hide nothing.

# GAME A — The Castle Designer

**Player role:** architect. Never a commander, ever.
**Win:** the castle holds — the attacking commander dies.
**Real metric:** cost imposed, not the binary.

## The philosophy (RULED 25 Aug)

Game A is **pure castle design** — that is precisely what makes it a
strategy game. The depth: every aspect of the design must be considered
against how well a **cold commander**, spawning in with no knowledge of the
player's intent, can navigate and defend what was built. Design choices
carry real consequences: build beside high cliffs and the attacker rains
arrows down; over-complicate the footprint and your own commander cannot
read his own castle. **You cannot move a wall or a tower once the enemy is
at the gate.**

## The loop

1. **Survey.** Site choice on the topographic map.
2. **Build.** Stone, heights, gates composed of parts, subsurface works.
3. **Seal.** No further input of any kind. The Lord Constable picks his camp
   from the highlighted legal areas and the siege runs.
4. **Watch.** Replay with scrub and step, not a live spectacle. [OPEN 2]
5. **Debrief.** What they saw, probed, rejected; where the information
   network went dark; which company fought blind.
6. **Iterate.**

## Mechanics the player touches

Site choice · terrain and material · height and depth · gate composition ·
subsurface galleries and counter-mines · **nothing else**.

**Zero unit control.** No purchasing, no posting, no routes, no orders, no
mid-siege spending. The AI Castellan spawns cold, spends the credits,
garrisons the walls, sites his own watchmen and runs his own circuits — all
from what he inherits. The architecture is the only thing carrying the
player's intent into the fight.

## How complexity punishes — emergently, never by rule

- **Circuit arithmetic.** Companies forget in 30 s; a sprawling castle
  cannot be kept synced, and its commander permanently works from an older
  quilt.
- **Sightline fragmentation.** Interior clutter blinds your own garrison.
- **Sector coupling.** A castle whose mutual-support structure decomposes
  cleanly contains breaches; one that doesn't cascades — computable from
  the drawn geometry (LloydFlow cross-ratio candidate).
- **Terrain adjacency already works.** Eye-height LOS treats a cliff as a
  tall stack; the exposure field shows the attacker's firing position with
  no cliff rule anywhere.

## Scoring

Grade on **cost imposed** (the adversarial report's total), with hold/fall
as a threshold rather than the score. A castle that falls at 400 is better
designed than one that holds at 90; iteration stays meaningful on a win.

## The failure mode to design against

The player is a spectator for the whole siege. The debrief and replay
controls are not polish — they are the product.

# GAME B — The Command System

**Player role:** Castellan or Lord Constable. **Win:** kill the enemy
commander; same tick = tie.

## The loop

Receive (a circuit completes; the quilt updates, each patch its own vintage)
→ Read (work out what is happening from stale partial patches — the core
skill) → Decide (real attack vs feint; who is re-taskable vs locked) →
Draft (scope, guards, releases; every order carries a guaranteed exit) →
Dispatch (orders arrive when the runner arrives) → Wait (the world moved;
find out next circuit).

## What makes it a game rather than an RTS

Fog is real and asymmetric · latency is the core friction — command is a
physical act performed by a man who can be killed · order-lock is the
commitment device · information has topology (watchmen relay outward,
messengers collect inward, companies hold 30 s) · losing an officer
releases men rather than removing them.

## Modes

| mode | Home | Away | notes |
|---|---|---|---|
| A (designer) | AI | AI | the shipping solo game |
| Human vs AI | either side | — | default human to **attacker** first: easier to learn |
| PVP | human | human | the acceptance test for the rule set |

**PVP castles [OPEN 6]:** alternating sieges recommended — I build, you
attack, then swap on the same terrain and budget; score cost imposed and
paid across both legs. Castle-vs-castle ruled out: two impedances, no
source — nothing pressurises.

# Open items

**[OPEN 1] GUARDLOC** — internal `goto` guards read ground truth; only
releases are locality-checked. Fix agreed in principle: locality on all
guards; "locally observable" includes watchman relay in range. Blocks fog.
**[OPEN 2]** Watching tempo in Game A (replay scrub vs live speed).
**[OPEN 3] SELFORD** — self-ordered (commanders, detached officers:
restrained) vs self-directed (remnants: unrestrained). Needs ratification.
**[OPEN 4] TENT** — durability; recommendation in ladder register.
**[OPEN 5]** Human order-drafting under time pressure — template library
doubles as the AI's COA generator.
**[OPEN 6]** PVP castle provenance — recommendation above.
**[OPEN 7]** Captured-logbook presentation to a human reader.
**[OPEN 8] RETASK** — orders flow outward by messenger only; a company with
no recall branch cannot be re-tasked. Coherent; needs formal statement.
**[OPEN 9]** Small ratifications: gate arrow-transparency · "Door" block
type · scouts share the 30 s window (ruled: no logbook, no exemption).

# Parked

**Campaign mode** — fixed scripted scenarios, each teaching one mechanic,
each with a specific win condition to progress. Deferred until the main
game is solid; the open question travels with it (do scenario win
conditions depart from commander-death, or do scenarios teach by
constraining budget, terrain and threat?).
