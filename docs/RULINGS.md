# FortressLab Mini — Complete Ruling Ledger

Authoritative record of every design ruling. Detail that used to live only in
Claude's memory now lives here. Companions: `docs/memos/` (dated memos, the
escalation ladder, TWO_GAMES, the resonance proposal), `docs/HANDOFF.md`
(session pickup), `src/fortresslab_mini/config_balance.py` (all provisional
numbers).

**Role split:** Will designs and rules everything; Claude transcribes rulings
into spec and code, presenting loose ends as multiple choice. Claude has three
times attributed its own suggestions to Will (repetition ruling, half-hour
rule, and re-raising the settled Game A scope) — challenge attributions.

**Adoption bar:** nothing enters because it is Will's research. It must
materially beat the existing method on a measured test. Negative results stay
in the repo.

---

## 1. Philosophy

- **Bounded sandbox / plumbing.** "We are building the plumbing, making sure
  it doesn't leak and then we let the water pressurise. We don't tell the
  water what to do or how to be water, we just contain where and how it
  flows." No scenario rules, no strategy detectors, no penalties triggered by
  detecting a strategy. Unintended AI behaviour is a leak to be fixed at the
  joint, never patched with a behavioural rule.
- **Chess shape.** Finite pieces and legal moves; a move's value is what it
  contributes to the position. A "spiritual expansion to chess".
- **Circuit / potentiometer.** Away = potential, Home = neutral return, the
  design = impedance. R→0 is the dead short (tie), R→∞ the tomb; both lose.
- **Counter-play law (25 Aug).** Every play a commander can make must have a
  direct counter-play available. Brilliant plays succeed from strategy using
  legal levers, never from an unanswerable exploit.
- **Home team first (25 Aug).** Full Home play mechanics before attacker
  mechanics.
- **Anti-band-aid.** Rejected: torus boards, feudal-service clocks, the
  "coward commander" (Claude's invention). Board size irrelevant. Wandering
  off loses emergently.
- **Soft stalemates** never artificially punished; barricading to drain the
  attacker is valid, but must never work as a wall-clock run-down.
- **Castle vs castle: REJECTED** (25 Aug) — takes away what makes the design
  interesting. Two impedances, no source.
- **Verification: the pi/circle principle.** Prove the generator, not the
  enumeration. Balance is measured, never proven; target signature is an
  inverted U of value vs commitment.

## 2. Kernel (20 Aug)

Simultaneous resolution, not turns. Map finite; edge = array limit, certified
irrelevant. 8-direction single step plus "Stay" ("Hold" is reserved for
orders). All units identical stats; **zero HP, die on first contact**
(Chebyshev ≤ 1, both die — "a dead short not a diode"). Commander has a crown,
no armour. **Win only by commander death**; same tick = tie. Surrender
removed. Repetition will never occur (agents' nature). **Occupancy is a
property of stopping, not transit** — no collision resolution anywhere.
Commander-on-commander end states are exhaustively two: mutual awareness →
both die; stealth kill on a facing-away target. Floats permitted.

## 3. Units

**Blank unit = 1× speed, 1× perception, 1× health.** Every unit is a diff from
it; an all-plus diff does not ship. **Unit design law: unique ability AND
matching weakness.**

| unit | ability | weakness |
|---|---|---|
| man-at-arms | the blank unit | — |
| archer | ranged attack | no armour; finite ammo; **out of ammo = non-combatant**, not a de facto man-at-arms |
| watchman | better perception; relays to anyone in range, 1 tick per hop | non-combat; 30 s memory |
| messenger | routes, delivers orders, carries the logbook | non-combat |
| scout | 2× speed, extended perception, stations until release | non-combat; 30 s memory |
| knight | armour, arrow-immune | upgraded sergeant: credits + blacksmith + armour delivery |

Ranks — Castle: Castellan (all orders originate; loss = defeat), Captain of
the Guard, Knights, Sergeants, Men-at-Arms, Archers, Watchmen/Levies. Siege:
Lord Constable, Earl Marshal, Master of the Siege, Labourers.

**Bloodlust & risk.** All units attack on sight unless orders channel them; no
order can forbid killing. Risk gates HOW, never WHETHER — survival is
instrumental, never terminal.

**Self-directed (25 Aug, retiring "feral").** Losing the command chain means
**unrestrained bloodlust**, not absence of orders: attack anything reachable,
seek a company to fold into, else work back to the barracks, aggro anything
sighted en route. **No goalless state exists anywhere in the game.**

**SCOPE CUT (26 Aug):** knights, blacksmith, archers, mining and carts are
**future implementations**. Minimal loop = commanders, men-at-arms, comms
units, walls/dig, orders, spawn.

## 4. Economy

250 credits per side, never refreshed, **spendable at any time for any
reason** — the reserve is a strategic instrument, latent force with no
position. Spawning is atomic at **company** granularity (officer + 9, mixed).
Spawn = order transaction: no valid order, nobody leaves the keep. Units spawn
from the keep, never the war room. Enemy spend knowable only by causal
observation. Provisional numbers live in `config_balance.py`.

## 5. Orders

`order := (action scope, release conditions)`. Bare Hold is malformed.
Releases must guarantee a definite outcome — x-or-y; "until recalled" alone
soft-locks. **Order-lock:** no re-tasking until release fires. Contingency
trees legal (the 10 am order is the canonical fixture). Capacity bounded by
rank. **Scope attenuates, never amplifies.** No predicate lookup tables — a
closed term/comparator grammar. Relief is a command procedure, not movement.
Officer killed → messenger fetches new orders; nothing self-issues.

**Fractal command:** knights/sergeants order their 9 with the same engine;
captains run it over companies within granted scope.

## 6. Perception

Peripheral/diagonal = half of frontal. Presence → identified on second contact
within the alert cooldown. Range degrades identically (one mechanic: marginal
contact). Vantage height extends reach. Facing = awareness. **Height: units
stand ON blocks, eye = stack height + 1; varied height is the sole source of
cover** — flat manned walls cast no shadow.

## 7. Comms and intelligence (25 Aug)

**Messengers** run scheduled or continuous routes to company leaders and
return. **Sync is ONE-WAY**: the messenger updates his own map; leaders are
never updated and keep only local information. **Only after a full circuit**,
at the war room, does the commander's map sync. Company leaders may **request**
new orders via messenger once theirs completes.

**Two memories.** Units and companies hold a **30-second rolling window**.
Messengers carry a **logbook** — static snapshot per report, last-write-wins
per area, refreshed only at the war room. **Logbook drops on death; the enemy
must stand on the body to capture it**; it reads the same for anyone.

**Watchmen** have a better perception stat and share to anyone in range — not
a stat buff. Relay is watchman-to-watchman at **1 tick per hop**. They are the
distribution half of the network; messengers collect, watchmen relay outward.

**The war-room map is the ledger.** White = no data · yellow ≤ 50% · orange
≤ 90% · red ≤ 99% · black = destroyed. Mechanisms take the structure's colour
plus **blue functioning / black disabled**. **The map is STATIC** — colours
persist until new intel, never fading to white. Enemy sightings decay; estate
knowledge does not.

**Ambiguity is a first-class concern**, scaling with fragility × consequence.
Observability cost per sector is a gradeable property of the player's design.

## 8. The two games

**Game A = pure castle design. ZERO unit control.** Verbs: site choice,
terrain and material, height and depth, gate composition, subsurface works.
Nothing else. The AI Castellan spawns **cold** and does everything from what he
inherits. Campaign mode **parked** until the main game is solid.

**Game B = the command system.** Modes: AI-vs-AI (ships Game A), Human vs AI,
PVP (the acceptance test).

**Attacker siting (25 Aug):** the Lord Constable picks his camp **before tick
1** from highlighted legal areas and spawns **in the camp**; only the war-room
tent pre-exists. Legal siting must guarantee no defender reaches the camp
faster than he can spawn.

## 9. Siege and damage (25 Aug)

**Ladders** (closing ESCALADE): higher wall → longer ladder → more carriers →
more exposure. **Push-off legal**; leaving a ladder up to farm climbers is
equally valid.

**Projectile engines**: build ticks, then ticks between salvos. **The counter
is time + telegraphing, not sortie** — build time is defender prep, and
bombardment broadcasts the entry point.

**Damage = projectile × angle of attack.** Square-on full; each degree off
diminishes. Wall orientation and curvature become design levers. Projectiles
do percentage health; digging stays tick-cost — different verbs.

**NO WALL REPAIR** (leaning; revisit only if the loop demands). Damage is
monotone; the termination string stays finite.

**Fire**: burning projectiles consume wooden fortifications; water buckets
extinguish; proximity pulls units to bucket-run. **Stun radius outside the
kill radius, 5 ticks** — the design's first hard timer. Three bands: kill /
stun / distraction. Bucket-running needs **no** precedence rule; it is
instrumental logic expressible as a `hazard()` guard.

**Engine accuracy by ranging, no RNG.** Aim error starts large and each
**observed** shot reduces it toward the engine's precision floor. Blind lobs
never converge → forward observers → **kill the spotter and bombardment stays
wild**. Target switch resets ranging. Ranging shots telegraph the aim point.

## 10. The Home time economy (25 Aug)

Survey grounds → buy units and set watchmen → companies to positions with
orders → logistics (routes, carpenters, labourers producing arrows, pole arms,
hooks) → blacksmith commissioned for armour → **knights are upgraded
sergeants** → enough knights unlocks **sally raids**. *"How do you decide what
to focus on? That's the game."*

## 11. Testing doctrine

**LLM play-through protocol:** no rulebook, no constraints. They get **only
the win/lose conditions and the list of legal moves** and work it out cold.
Good and bad plays are the natural learning curve. *"Give them the sandbox and
the toys, don't tell them how to play."* Every LLM session is therefore also a
**fresh-player test**. The artifact they receive is a **move manifest**, not a
spec.

**Bounding programme.** Max arrows = an *interior* optimum over allocations
(rate × duration), not the all-in endpoint. Fastest attacker win = minimum
camp distance + ticks to gank a facing-away commander. **Longest game** = the
intrinsic tether — *"a ball attached to a string"* — derived from monotone
resource exhaustion, not state enumeration. **Credits are the game's clock.**
String length = baseline closure + 500 credits at maximum delay-per-credit;
unbounded delay-per-credit is the termination leak.
