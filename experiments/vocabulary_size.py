"""
Resonance address space — REVISED (Will, 26 Aug).

Locations are AREA-specific and hierarchical, like a postal address:
country / postcode / street / number. The 12 fundamentals are the chromatic
bass-clef frequencies; a dyad names a position WITHIN that area.

Stone absorbs everything above B2 (123.47 Hz), and the low-pass crossover in
open air moves with distance. So from far away a unit hears only the area;
the position resolves on approach. Coarse-to-fine, by physics.
"""

BASS = {"C": 65.41, "C#/Db": 69.30, "D": 73.42, "D#/Eb": 77.78,
        "E": 82.41, "F": 87.31, "F#/Gb": 92.50, "G": 98.00,
        "G#/Ab": 103.83, "A": 110.00, "A#/Bb": 116.54, "B": 123.47}

STONE_CUTOFF_HZ = 123.47      # everything above is fully absorbed by stone
RELEASES = 2 ** 3 - 1         # cancellation / attrition / silence
DB_LEVELS = 4


def main():
    n = len(BASS)
    print("THE 12 FUNDAMENTALS (bass clef chromatic) — the AREA component")
    for k, v in BASS.items():
        print(f"  {k:<6} {v:>7.2f} Hz")
    print()
    print(f"Stone cutoff: {STONE_CUTOFF_HZ} Hz. Above it, nothing survives stone.")
    print()

    print("ADDRESSING")
    print(f"  areas (fundamental alone)      : {n}")
    print(f"  positions per area (dyad)      : {n}")
    print(f"  total addresses                : {n * n}")
    print(f"  (triads would give             : {n ** 3:,})")
    print()

    print("COMMANDER'S CHOICE SPACE")
    total = n * n * RELEASES * DB_LEVELS
    print(f"  {n*n} addresses x {RELEASES} release sets x {DB_LEVELS} dB levels "
          f"= {total:,} distinct orders")
    print()

    print("WHY THIS WORKS FROM ONE SPAWN POINT")
    print("  Far away  : only the bass carries -> you know the AREA")
    print("  Approach  : the crossover rises   -> the POSITION resolves")
    print("  Behind stone: area only, forever  -> position needs line of sight")
    print()
    print("INTELLIGENCE CONSEQUENCE")
    print("  An enemy outside the walls hears WHICH AREA is being reinforced,")
    print("  never which posts. Stone gives away the sector and hides the")
    print("  detail — the exact fog structure the game already wants.")


if __name__ == "__main__":
    main()
