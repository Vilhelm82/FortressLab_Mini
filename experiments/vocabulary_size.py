"""
How many distinguishable orders can the resonance system express?

The answer has two parts and they differ by orders of magnitude:
  1. GLOBAL vocabulary  — how many distinct performances exist at all
  2. LOCAL simultaneous — how many can sound near each other and stay
                          individually identifiable

(2) is the number that actually bounds play, and (1) is reused spatially, the
way a cellular network reuses frequencies outside the interference radius.
"""
from itertools import combinations

SEMITONES = 12
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)      # Home; Away uses the minor set


def chords_in_one_key(min_notes=3, max_notes=6):
    """Rooted chords drawn from one diatonic scale."""
    n = 0
    for root in MAJOR_SCALE:
        others = [p for p in MAJOR_SCALE if p != root]
        for k in range(min_notes - 1, max_notes):
            n += len(list(combinations(others, k)))
    return n


def report():
    per_key = chords_in_one_key()
    keys = SEMITONES                       # 12 major keys for Home
    chord_space = per_key * keys

    releases = 2 ** 3 - 1                  # 3 ruled mechanisms, >=1 required
    db_levels = 4                          # full / reduced / quiet / near-silent
    parts = 4                              # voices within a company

    global_vocab = chord_space * releases * db_levels * parts

    print("GLOBAL VOCABULARY")
    print(f"  rooted chords per key (3-6 notes) : {per_key:,}")
    print(f"  x 12 keys                          : {chord_space:,}")
    print(f"  x {releases} release sets (2^3-1)           : {chord_space*releases:,}")
    print(f"  x {db_levels} dB gate levels                : "
          f"{chord_space*releases*db_levels:,}")
    print(f"  x {parts} parts per company            : {global_vocab:,}")
    print()

    # Local limit: two performances collide if they share too many pitch
    # classes. Require a minimum Hamming-style separation between chord sets.
    print("LOCAL SIMULTANEOUS LIMIT (within one acoustic neighbourhood)")
    for min_diff in (2, 3, 4):
        # greedy max set of chords pairwise differing by >= min_diff notes
        allc = []
        for root in MAJOR_SCALE:
            others = [p for p in MAJOR_SCALE if p != root]
            for k in (2, 3):
                for c in combinations(others, k):
                    allc.append(frozenset((root,) + c))
        chosen = []
        for c in allc:
            if all(len(c ^ d) >= min_diff for d in chosen):
                chosen.append(c)
        print(f"  min {min_diff} pitch-classes of separation -> "
              f"{len(chosen)} co-audible orders")
    print()
    print("Interpretation: the global vocabulary is effectively unbounded for")
    print("this game's needs; the binding constraint is the co-audible set,")
    print("which is small — and reused spatially outside the interference")
    print("radius. Chord collision (proposal 16) is therefore a LOCAL failure,")
    print("never a global one.")


if __name__ == "__main__":
    report()
