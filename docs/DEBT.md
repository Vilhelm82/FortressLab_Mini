# Debt list — what stands between here and a basic game loop

State at `7b4303a`: `resonance.py` + `score.py` are the system. `kernel.py`,
`worldmap.py`, `solver.py` are neutral and kept. 16 tests green. The old
model (commander, sim, enemy brain, perception capacitor, belief field) is
deleted, not migrated.

Ordered by what blocks what. **Design debts are Will's to rule; build debts
are Claude's to write once the rulings above them exist.**

---

## A. Design debts — nothing can be built past these

**A1. What a commander is allowed to write.**
The order shapes are undesigned. `hold_score` / `strike_score` /
`watch_score` were Claude's, and went with `commander.py`. A score today is
an area plus notes drawn from three conditions; what an actual order *looks
like* has never been designed.

**A2. What ends a strike.**
A company sent to remove interference has no note that dies when the
interference is gone. Attrition alone means it fights to half strength
whether it wins or loses.

**A3. Whether a score needs a guaranteed exit.**
The old x-or-y rule is deleted. Under a gradient a unit always has somewhere
to go, so soft-lock may not exist — or may.

**A4. How the map is divided into 12 regions and 6 posts each.**
Addressing works (proved), but nothing assigns fundamentals to castle areas.
Auto-assigned by the game (ruled) — the algorithm is undesigned.

**A5. How fire and other hazards enter a score.**
Bucket-running is instrumental logic needing no override (ruled). The route
by which fire reaches a unit's decision is not designed.

**A6. Whether own-state conditions exist.**
The three ruled mechanisms are all field-audible. Ammo, fatigue and the like
are known rather than heard. Whether that category exists is open.

**A7. What the commander does, now that he does not pathfind.**
He tunes addresses and states conditions. What he reasons over — freshness,
mass, what is at stake — and how he decides, is undesigned.

**A8. SPAWNTIME and camp distance.**
A float default sits in `config_balance`; the camp-distance rule is defined
in terms of it and remains uncomputed.

**A9. SELFORD.**
Self-ordered (commanders, detached officers: restrained) vs self-directed
(remnants: unrestrained). Carried since 25 Aug, never ruled.

---

## B. Build debts — writable once the design above exists

**B1. The sim, rebuilt on the field.** The tick loop is deleted. It needs to
be written against `resonance.Field`: units hear, harmonise, route by least
detection, contact resolves by the kernel's dead short.

**B2. Companies as choirs.** Leader in the octave above, members folding out
when the location's deeper root dominates. `follow_target` exists and is
tested in isolation; nothing runs it over a real company.

**B3. The inversion cascade in the loop.** `WanderingUnit` is proved
standalone. Wiring it in means a company whose leader dies degrades and folds
into whoever sings its note.

**B4. Messengers as root cursors.** Arrival replaces the root. Proved in
concept (§30), not implemented.

**B5. Credits and spawning.** Pay, validate the score, deploy. Blocked on A8.

**B6. The commander, rebuilt.** Blocked on A7.

**B7. `tools/warroom.py` is broken** — imports the deleted `enemy_brain`.
Either rewire to `least_detection_route` or leave it dark until the sim
exists.

**B8. The move manifest.** The thin legal-move list the LLM phase receives.
Blocked on A1; writing it is itself a fresh-player test.

---

## C. Standing, unblocked

- **Field physics** — nine conformance tests green, no known gaps.
- **Addressing** — 72 addresses, stone hides the dyad, timber leaks it.
- **Score representation** — three conditions, six-layer cap, locality
  structural.
- **Kernel** — dead short, simultaneity, terminals.
- **Worldmap** — terrain, eye-height LOS, exposure.
