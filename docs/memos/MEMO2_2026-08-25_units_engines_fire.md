# FortressLab Mini — Rulings Memo #2, 25 Aug 2026

Everything ruled after the comms/spawn memo. Companions:
`ESCALATION_LADDER.md` (gap register), `TWO_GAMES.md` rev 2.

## 1. Unit design law

**RULED.** Every unit needs a unique ability AND a matching weakness. The
**blank unit** is the baseline: 1× speed, 1× perception, 1× health. Every
unit is a diff from it; an all-plus diff does not ship.

| unit | ability | weakness |
|---|---|---|
| man-at-arms | the blank unit | — |
| archer | ranged attack | no armour; finite ammo |
| watchman | better perception; relays to anyone in range | non-combat; 30 s memory |
| messenger | routes, orders, the logbook | non-combat |
| scout | 2× speed, extended perception, stations until release | non-combat; 30 s memory |
| knight | armour (arrow-immune) | upgraded sergeant: credits + blacksmith time + armour delivery |

Corrections: archers are **not** half speed — identical to a man-at-arms,
with a bow. An archer out of ammo is a **non-combatant** until resupplied,
not a de facto man-at-arms. Resupply is the archer's entire balance.

## 2. The war-room map is the ledger

**RULED.** Shows everything received, by messenger or personal observation.
White = no data · yellow ≤ 50% · orange ≤ 90% · red ≤ 99% · black =
destroyed. Mechanisms: containing structure's colour, plus **blue**
functioning / **black** disabled.

**The map is static** — a colour stays until new intel says otherwise, never
fades to white. Enemy sightings decay; estate knowledge does not. The map
lies by being out of date, precisely about things that worsened unwatched.

## 3. Ambiguity as first-class concern

**RULED.** Unreported ground could be the first domino — an unobstructed
walk-in ending with a knife in the commander's back. Concern scales with
**fragility × consequence**. Game A consequence: a good footprint makes all
areas of concern easily observable; a weak section that is a hassle to check
is a quick way to lose a siege. Observability cost per sector is gradeable.

## 4. Game A is pure castle design

**RULED. Zero unit control.** Verbs: site choice, terrain and material,
height and depth, gate composition, subsurface works. Nothing else. The AI
Castellan spawns cold and does everything from what he inherits. Campaign
mode is **parked** until the main game is solid.

## 5. Attacker camp siting

**RULED** (supersedes corner-spawn-and-march). The Lord Constable picks his
location **before tick 1** from highlighted legal areas and spawns **in the
camp**; only the war-room tent pre-exists, credits unspent. **Balance
requirement:** no defender unit may be able to reach the camp faster than
the Constable can spawn units — minimum camp distance is a computed,
castle-dependent property of the highlighting.

## 6. Siege engines

**RULED — ladders** (closes ESCALADE). Higher wall → longer ladder → more
carriers → more exposure on the approach. Wall height now prices sight, dig
time, and escalade at once.

**RULED — push-off.** Defenders can push ladders off; risk is covering
archers. Leaving a ladder up to farm climbers is equally valid: *"why
interrupt your enemy while they hand themselves over to you?"*

**RULED — projectile engines.** Build duration in ticks, then ticks between
salvos. **The counter is time + telegraphing**, not sortie: build time is
defender prep, and committing to bombardment broadcasts the single entry
point. *"Good luck pushing that kill zone now."* Ballistics historically
cleared walls (anti-personnel) more than they destroyed them.

## 7. Damage model (closes DMGMODEL)

**RULED.** Damage = projectile × **angle of attack**; square-on full, each
degree off diminishes. Granularity is an LLM balance knob. Wall orientation
and curvature become design levers; the attacker gets a siting problem.
Projectiles do percentage health; digging does tick-cost — different verbs.
**No wall repair** (leaning; revisit only if the loop demands). Damage is
monotone; the termination string stays finite.

## 8. Fire

**RULED.** Burning projectiles consume wooden fortifications over time;
extinguished with water buckets; proximity pulls nearby units to bucket-run,
so water access is a commander consideration.

**RULED — stun.** A stun radius outside the kill radius disorients for **5
ticks** — the design's first hard timer. Stun-and-push is a real tactic.
Three bands (kill / stun / distraction) let one impact do graded work; a
deliberate short shot strips a wall without damaging it. Spacing becomes an
architectural decision.

**Retracted:** bucket-running is not an "involuntary behaviour" exception.
Will's question — *is taking an arrow something a unit chose?* — dissolved
the category. It is the existing instrumental logic one level out (*must
hold, but if the wall burns I can't hold*), already expressible as a
`hazard(kind, region)` guard. Only the weighting is a parameter.

## 9. Engine accuracy — ranging, not RNG

**RULED.** An engine carries an **aim error that starts large because the
range is unknown; each observed shot reduces it toward a floor set by the
engine's inherent precision.** Deterministic; the historical behaviour is
convergence, not scatter.

- Correction requires **observation**: blind lobs never converge → forward
  observers → **kill the spotter and the bombardment stays wild**.
- Switching targets resets ranging — commitment is physical.
- Ranging shots telegraph the aim point salvos early.

## 10. The Home time economy

**RULED.** Unchallenged defenders: survey grounds → buy units, set watchmen →
companies to positions with orders → logistics (routes; carpenters and
labourers producing arrows, pole arms, hooks for anti-ladder work) →
**blacksmith** commissioned to produce armour → **knights are upgraded
sergeants** → enough knights unlocks **sally raids**, the concrete
counter-attack. *"How do you decide what to focus on? That's the game."*

The sally gate is mechanically motivated: knight armour is arrow-immune, the
one class the exposure field cannot price normally. And the player's
architecture sets the exchange rate on the Castellan's time — a legible
castle frees the prep window for quality and offense; a sprawling one eats
it on intelligence.

## Still open → see ESCALATION_LADDER.md register and config_balance.py
