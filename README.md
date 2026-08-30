# FortressLab Mini

A castle siege game built as a spiritual expansion to chess: a finite, closed
rule set with everything else falling out of how two commanders navigate it.

The player designs; the player never fights. Both sides are AI-commanded, and
the defenders inherit a castle they have to read for themselves. You cannot
leave them a guidebook — the architecture *is* the guidebook.

## Design spine

* **Bounded sandbox.** Design where the walls are and how the sand behaves.
  No scenario rules, no penalties triggered by detecting a strategy.
* **A wall is an expensive edge**, not an obstacle. Weakness is the cheapest
  path, discovered — never a rule saying "attack the weak point".
* **Orders are impedance.** Every unit is already violence; command constrains
  it, never causes it. No order can tell a unit not to kill.
* **The circuit.** Away is potential, Home is the neutral return, and the
  design is the impedance between them. Both extremes lose: R→0 is the dead
  short (mutual annihilation), R→∞ is the tomb (no work done, no kill).
* **Chess shape.** Any legal move is legal; a move's value is only what it
  contributes to the position.

## Layout

A Rust workspace of two crates. Python is retired. Godot 4 will wrap the sim
through GDExtension for the mobile build; the engine stays a thin viewer over
a replayed deviation log, so the engine choice is reversible.

    rust/soma/          the behavioural substrate — a general model
        src/lib.rs        arousal, load, concern, the border, the bath
        tests/            proves the model with no game in scope
        examples/maze.rs  controlled scenarios, nothing castle in them
        examples/sweep.rs dials the constants against ruled targets

    rust/sim/           this game
        src/world.rs      voxel columns, stairs, loudest-path sound, 3D sight
        src/field.rs      notes, addressing, perception, the inversion cascade
        src/balance.rs    acoustic constants, all provisional
        src/anchor.rs     the bridge: resonance chord -> one number for soma
        src/devmap.rs     the development castle

    docs/RULINGS.md       the authoritative ruling ledger
    docs/RESONANCE.md     the command system as a specification

**`soma` knows nothing about castles, sieges or sound**, and is meant to carry
into other games unchanged. What it wants is small: three bearings to things a
man cares about, one number for how firmly he knows where he is, whatever has
just happened to him, and how many uninjured mates are in reach. Supplying
those is the game's business, and `sim/src/anchor.rs` is where this game does
it. Compute cost and scale get looked at once the model is right.

## Running

    cd rust
    cargo test                                  # everything
    cargo test -p soma                          # the model, standing alone
    cargo run -p soma --example maze            # watch men in a corridor
    cargo run -p soma --release --example sweep # dial the constants
    cargo run -p fortress_sim --example anchored

## Status

Field and world proven. The behavioural substrate runs, with the panic loop
closing on its own: losing the song frightens a man and being frightened costs
him more of it. Nothing the commander touches is built.

Constants are **knobs, not rulings**. What gets ruled is the target — how long
a formed company should stand a bad corridor, how fast a lone man should come
apart — and the sweep finds numbers that satisfy all of them at once. Targets
currently in `sweep.rs` are placeholders and flagged as such in the source.

## Open rulings

* Are timber gates opaque to arrows? Currently they block movement but not
  sight, so a gate archer covers his own approach lane.
* Trauma floor, if the aptitude system is ever built: a unit degradable
  without limit becomes catatonic, which the design elsewhere forbids.
