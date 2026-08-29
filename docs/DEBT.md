# Debt list

State at `369a9d9`. Five modules, 16 tests green, pyflakes clean.

Scope rule for this file: **only debt against code and rulings that exist
right now.** Nothing is listed for the command layer, order representation,
sim loop or commander — those were removed pending the map and resonance
redesign, and listing debt for them would assume mechanics that may not need
to exist.

---

## Debt in what stands

**D1. `resonance.py` has never run against a map.**
Every conformance test builds its own bare `Grid`. The field has never been
driven by a `WorldMap` — real terrain, height stacks, materials read from the
map rather than passed in as sets of cells.

**D2. Height is absent from the field.**
`worldmap.py` knows stacks and eye-height LOS. `resonance.py` treats the
world as flat: `Grid` has stone and timber cells and nothing else. Sound
does not care about elevation and the beam does not use eye height.

**D3. Materials are declared per-cell, not read from the map.**
`Grid(w, h, stone=(), timber=())` takes explicit cell sets. The map's own
block types are ignored.

**D4. `config_balance.py` carries eight sections for systems that do not
exist.** AMMO, ENGINES, DAMAGE, FIRE, PRODUCTION, SALLY, UNDERGROUND, TENT —
provisional numbers for ruled-but-unbuilt features. PERCEPTION_EXTRA and
COST_FIELD are superseded by RESONANCE. Keep or cut is a call, not a defect.

**D5. Every RESONANCE constant is unvalidated.**
Layer weights, decay rates, transmission coefficients, the angular hearing
curve, the masking threshold, the cascade sweep rate. Claude picked all of
them to express orderings Will ruled. The tests pin structure, never values.

**D6. The nine conformance tests are static-field only.**
No motion over time except the two that step manually. Nothing tests
interference degrading navigation, the pulse, or two sides at once.

---

## Rulings that exist and are unimplemented

**D7. SPAWNTIME / camp distance.** A float default sits in
`config_balance`; the ruled camp-distance requirement is defined in terms of
it and has never been computed.

**D8. SELFORD.** Self-ordered (commanders, detached officers: restrained) vs
self-directed (remnants: unrestrained). Ruled as a distinction on 25 Aug,
never specified.

---

## Standing, no known gaps

- Field physics: superposition, loop closure, addressing, echolocation,
  detection channels, masking, least-detection routing, cascade, attraction.
- Kernel: dead short, simultaneity, terminals.
- Worldmap: terrain, height, eye-height LOS, exposure.
