# FortressLab Mini — Rulings Memo, 25 Aug 2026

Session was phone-only (Will at work). No code written. Everything below is a
ruling to be transcribed into `docs/kernel_v0_spec.md` and implemented at the
Linux box this evening.

---

## 1. Spawn: orders are part of the transaction

**RULED.** No unit is ever without orders. Spawning from the barracks must
coincide with the unit's orders before it can leave. A spawned unit is either
**under orders** or **self-directed** (see the terminology ruling below —
"feral" is retired).

Consequences:

- The order validator now gates spawning. A malformed order doesn't get
  refused in the abstract — the men never walk out of the keep.
- This dissolves the fogged-search stall at the unit level. "Unordered unit
  with no contact and no goal" is not a legal game state.
- **Terminology RULED:** "feral" was the wrong word — it implied absence of
  drive. The behaviour is **unrestrained bloodlust**, the price of losing the
  command chain: attack anything reachable, do your own thing until you die
  or another company folds you in. Units are never without orders — the
  orders become **self-directed**: find a company to join, else work back to
  the barracks, aggro anything sighted en route. No goalless state exists
  anywhere in the game.

## 2. Spawn granularity: the company is atomic

**RULED.** Units are never spawned individually. The atomic spawn is a
**company**: a knight or sergeant plus 9, composed as a man-at-arms / archer
mix. Labour units spawn the same way.

- Spawn granularity = command granularity = order granularity. One
  transaction: pay, draft the order, deploy.
- Resolves the tension with "commanders cannot order 1-credit units except
  messengers" — commanders address *companies* through their officer.

## 3. Economy — PROVISIONAL, balance items only

Chosen to unblock implementation; **not rulings**. Live in
`config_balance.py` for the R&D sweep.

| item | provisional value |
|---|---|
| company | 19 cr (officer 10 + 9 bodies @ 1) → ~13 companies/side |
| messenger | 2 cr, bought and ordered individually |
| composition | chosen at spawn; drifts as auto-rally backfills losses |
| self-directed spawn | legal, 1 cr/body, no officer — preserves the ruled 250-body zerg |

**RULED:** the 250 credits belong to the **commander**, spendable at any time
for any reason — never a forced up-front dump. The reserve is a strategic
instrument: latent force with no position.

## 4. Comms: two varieties

**RULED.**

**Messengers.** Run designated routes to selected company leaders, then return
to the commander. Routes can be scheduled for specific times or set as
continuous loops. They stop at each company leader and sync map knowledge.
Only after a **full circuit**, on return to the war-room, is the commander's
map finally synced. Company leaders can use messengers to **request new
orders** once their current order completes — so companies hold position
instead of draining back to the keep.

**Scouts / watchmen.** Fast non-combat units — 2× speed, extended perception.
Ordered to a designated location, they remain until a release criterion is
met, then return to the war-room. Messengers can sync with scouts and
watchmen so those stay at their posts.

**Watchman relay RULED:** watchmen have a better perception stat and share
what they see with anyone in range to hear them — **not** a stat buff; two
watchmen side by side do not double their radius. Reports pass
watchman-to-watchman like a person relaying what they heard, **one tick per
hop**. A ring of watchmen is a chain with latency, not realtime awareness.

## 5. Sync is ONE-WAY

**RULED.** Messengers update **their own** map while out on route. Company
leaders are never updated by the messenger; they retain only local
information. The commander is the sole fusion centre — only **one belief
field exists in the game**. Companies are pure sensors.

## 6. Two different memories

**RULED.**

**Unit / company memory — 30-second rolling window.** A unit's picture holds
only what was spotted in the last 30 seconds. Enemy at 12:00:00, another at
12:00:20, sync at 12:00:30 → only the second is carried.

A sync record: the coordinate area visible to that company · the time of the
sync · units and assets spotted in the last 30 seconds.

**Messenger memory — the logbook.** Messengers carry a logbook recording
which intel was received at what time — that artifact is why they have no
cooldown. Static snapshot per report; same area reported twice in one run →
**overwritten by the newest** (last-write-wins per area). Refreshes only at
the war-room. Watchmen and scouts have **no logbook** and share the 30 s
window.

**RULED — logbook capture:** messengers **drop the logbook on death**, and
the enemy must **stand on the body** to capture it. The logbook carries the
same information regardless of who reads it.

### Why this matters

- Route period is a hard constraint: a sighting older than 30 s is *gone*.
- Watchmen posts only pay off if a route passes them — route topology is a
  designed artifact.
- The messenger is a moving archive with no backup; the 10 am order's "clear
  messenger routes" clause was already defending it.
- The commander's map is a quilt of vintages, each patch timestamped.

---

## Convergence with what's already built

A messenger circuit **is** the loop the adopted holonomy instrument measures
(`beliefs.py`, commit `71e767f`). `BeliefField.fuse` already takes
`(x, y, seen, t)` with per-observation age discounting — exactly the shape a
sync record produces. The belief layer needs no changes; only the messenger
and the sync record do.

---

## Implementation order

1. Transcribe into `docs/kernel_v0_spec.md`.
2. `config_balance.py`; company spawn transaction wired into `sim.py`.
3. Messenger and scout unit kinds; route orders as first-class shapes.
4. 30 s observation buffer on companies; logbook on messengers; war-room
   sync feeding `BeliefField.fuse`.
5. Then the 2.5D planner half.
