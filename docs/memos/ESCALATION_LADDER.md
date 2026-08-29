# The Escalation Ladder — gap register (25 Aug 2026)

One row per minimal addition to the legal move space; the register tracks
what each row opened and closed. Statuses updated end-of-day.

| # | + Addition | Opens | Closes |
|---|---|---|---|
| 1 | C vs C, flat void | — | — |
| 2 | +1 man-at-arms | — | — |
| 3 | symmetric squads | — | — |
| 4 | + archer | AMMO, SHOTWIN | — |
| 5 | + wall | DMGMODEL (latent) | — |
| 6 | + materials | — | — |
| 7 | + gate (composed) | GATETRANS, DOOR | one-cell-hole |
| 8 | + height stacks | PLANNER25D, ESCALADE | flat-shadow |
| 9 | + perception & fog | STALL | — |
| 10 | + officer, company, orders | GUARDLOC, SELFORD, RETASK | STALL |
| 11 | + messenger | LOGCAP | RETASK (mechanism) |
| 12 | + watchman | CHAINBAL | watchmen-inert |
| 13 | + scout | — | — |
| 14 | + credits & spawning | SPAWNTIME | — |
| 15 | + camp & tent | TENT, CAMPDIST | lone-constable |
| 16 | + war-room ledger | DMGMODEL (acute) | working-memory |
| 17 | + labour & production | CARTRULES, REPAIR, PRODRATE | AMMO (mechanism) |
| 18 | + subsurface | COLLAPSE, UNDERPERC | — |
| 19 | + engines | ENGINES | ESCALADE ✓ (ladders ruled) |
| 20 | + captains / fractal | FRACTALIMPL | sector partition (candidate) |

## Register (end-of-day status)

| ID | Status |
|---|---|
| AMMO | mechanism ruled (labour → carts); rates in config_balance |
| SHOTWIN | engineering, agreed rung |
| DMGMODEL | **CLOSED** — projectile × angle-of-attack (health %); digging stays tick-cost |
| GATETRANS | recommended: doors opaque, portcullis arrow-transparent both ways — awaiting ratification |
| DOOR | awaiting ratification |
| PLANNER25D | engineering, agreed rung |
| ESCALADE | **CLOSED** — ladders ruled, scaling carry parties, push-off ruled |
| STALL | **CLOSED** — self-directed ruling |
| GUARDLOC | fix agreed: locality on ALL guards; "locally observable" includes watchman relay in range — awaiting ratification |
| SELFORD | recommendation pending ratification: self-ordered (commanders/detached officers, restrained) vs self-directed (remnants, unrestrained) |
| RETASK | coherent, formal ruling due: orders flow outward by messenger only |
| LOGCAP | **CLOSED** — drop on death, stand to capture, same info any reader |
| CHAINBAL | balance sweep |
| SPAWNTIME | float default set in config_balance — LLM sweep item |
| TENT | recommendation pending: wooden structure, burnable, spawning stops without it, labour-rebuildable |
| CAMPDIST | computable once SPAWNTIME default accepted |
| REPAIR | **CLOSED** — no repair (revisit only if the loop demands) |
| CARTRULES | recommendation pending: slow, capturable like the logbook |
| PRODRATE | float defaults set in config_balance |
| COLLAPSE | future design (subsurface rung) |
| UNDERPERC | recommendation pending: digging emits sound-presence through ground |
| ENGINES | partially closed: ladders, projectiles, ranging, fire, stun ruled; crews/build details in config_balance |
| OBSCOST | recommendation pending: observation term in the attacker cost field |
| FRACTALIMPL | engineering, agreed rung |
