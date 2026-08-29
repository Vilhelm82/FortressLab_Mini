"""
How many distinct orders can the resonance system express?

REVISED (Will, 26 Aug): all units spawn at the SAME location and head out from
there, so a unit must be able to tell every location apart from one origin.
Therefore **every location needs a globally unique fundamental** — no spatial
reuse. Both teams share the same location vocabulary; only the phase differs.
The front gate resonates the same fundamental for everyone.

So commanders do NOT choose notes. They choose WHERE and WHAT CONDITIONS; the
game auto-assigns frequencies. Two commanders can never disagree about what a
location sounds like.
"""

SEMITONES = 12          # pitch classes = the address space
RELEASES = 2 ** 3 - 1   # 3 ruled mechanisms (cancellation, attrition, silence)
DB_LEVELS = 4           # full / reduced / quiet / near-silent
PARTS = 4               # voices within a company (sergeant's licence, future)

# Confusability within the 12: a fundamental's own harmonic series contains
# its octave (2nd), its fifth (3rd), its major third (5th). Those intervals
# partially mask; the tritone shares least.
HARMONIC_COLLISIONS = {1: "octave-equivalent (2nd harmonic)",
                       7: "perfect fifth (3rd harmonic)",
                       4: "major third (5th harmonic)"}


def main():
    print("ADDRESS SPACE")
    print(f"  locations addressable        : {SEMITONES}")
    print("  (octaves do NOT extend this — the 2nd harmonic of a bass tone IS")
    print("   its octave, so octave-separated addresses genuinely collide)")
    print()
    print("COMMANDER'S CHOICE SPACE (per company)")
    print(f"  where     : {SEMITONES} locations")
    print(f"  when-to-leave : {RELEASES} release sets")
    print(f"  loudness  : {DB_LEVELS} dB gate levels")
    core = SEMITONES * RELEASES * DB_LEVELS
    print(f"  -> {core:,} distinct orders")
    print(f"  x {PARTS} parts per company    : {core * PARTS:,} (parts = future)")
    print()
    print("SIMULTANEOUS ORDERS IN PLAY")
    print(f"  hard ceiling = {SEMITONES} locations occupied at once, per side")
    print("  practical = fewer; harmonically adjacent addresses mask:")
    for iv, why in sorted(HARMONIC_COLLISIONS.items()):
        print(f"    {iv:>2} semitones apart : {why}")
    print("  6 semitones (tritone) shares least — maximally distinguishable")
    print()
    print("DESIGN CONSEQUENCE")
    print("  A castle has at most 12 addressable places. Not 576 cells — 12")
    print("  named locations, like squares on a board both players call by the")
    print("  same name. Castle design must therefore resolve into a small set")
    print("  of strategically meaningful posts, which is a constraint on the")
    print("  PLAYER, not just on the engine.")


if __name__ == "__main__":
    main()
