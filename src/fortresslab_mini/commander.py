"""
Commander — the decision loop, resonance-native (rewritten 26 Aug 2026).

Input:  a SITUATION — the commander's quilt (timestamped patches), his roster,
        his credits.
Output: a DECISION — scores dispatched, purchases made, scouts sent, or
        explicitly nothing. Every emitted score passes validate_score; an
        unsingable score from the commander is a harness failure, not a bad
        play.

The commander does not assign units to threats one by one. He TUNES
LOCATIONS: he picks an address and states what would kill its richness. Units
find their own way by harmonisation (resonance.navigate_target) and route by
least detection. This module decides WHERE and WHAT CONDITIONS — never HOW.

No clock. No predicate grammar. Conditions come from the closed vocabulary in
score.py, all of which a unit can hear or know of itself.
"""

from collections import deque

from fortresslab_mini.score import (attrition, cancellation, clear, note,
                                    score, silence, spent, validate_score)

CONFIG = {
    "decay": 0.97,          # per-tick freshness discount on a sighting
    "cluster_r": 2,         # Chebyshev radius that merges sightings
    "dark_age": 90,         # a sector unseen this long has a dead loop
    "strike_guard_max": 2,  # commander sighted with <= this many guards = prey
    "company_cost": 19,
    "scout_cost": 2,
}

DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


class Situation:
    """What the commander actually has: his castle, his quilt, his men."""

    def __init__(self, walls, w, h, keep, now, credits, patches, companies,
                 sectors):
        self.walls = set(walls)
        self.w, self.h = w, h
        self.keep = keep
        self.now = now
        self.credits = credits
        self.patches = sorted(patches, key=lambda p: p["t"])
        self.companies = companies
        self.sectors = sectors


def _in(area, x, y):
    x0, y0, x1, y1 = area
    return x0 <= x <= x1 and y0 <= y <= y1


def fuse_quilt(sit):
    """Last-write-wins per area (ruled): a later patch clears every earlier
    sighting inside its area, INCLUDING clearing to empty — a fresh patch with
    no sightings is the report that the ground is clear."""
    live = []
    for p in sit.patches:
        live = [s for s in live if not _in(p["area"], s[0], s[1])]
        live += [(x, y, cls, n, p["t"]) for x, y, cls, n in p["sightings"]]
    return live


def bfs_field(sit, src):
    """Response distance over open ground — defenders route around their own
    stone, they do not breach it."""
    dist, q = {src: 0}, deque([src])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS8:
            n = (x + dx, y + dy)
            if 0 <= n[0] < sit.w and 0 <= n[1] < sit.h \
                    and n not in sit.walls and n not in dist:
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def threats(sit, cfg=CONFIG):
    """Cluster fused sightings; score = mass x freshness / (1 + distance)."""
    pts = [s for s in fuse_quilt(sit) if s[2] in ("enemy", "C")]
    groups = []
    for x, y, cls, n, t in sorted(pts):
        for g in groups:
            if max(abs(x - g["x"]), abs(y - g["y"])) <= cfg["cluster_r"]:
                tot = g["n"] + n
                g["x"] = (g["x"] * g["n"] + x * n) // tot
                g["y"] = (g["y"] * g["n"] + y * n) // tot
                g["n"] = tot
                g["t"] = max(g["t"], t)
                g["cls"] |= {cls}
                break
        else:
            groups.append({"x": x, "y": y, "n": n, "t": t, "cls": {cls}})
    dist = bfs_field(sit, sit.keep)
    for g in groups:
        d = dist.get((g["x"], g["y"]), sit.w + sit.h)
        fresh = cfg["decay"] ** max(0, sit.now - g["t"])
        g["score"] = g["n"] * fresh / (1.0 + d)
    return sorted(groups, key=lambda g: -g["score"])


def sector_of(sit, x, y):
    for name, area in sit.sectors.items():
        if _in(area, x, y):
            return name
    return None


def sector_age(sit, name):
    """Newest patch touching the sector; None = never seen."""
    area = sit.sectors[name]
    ages = [p["t"] for p in sit.patches
            if not (p["area"][2] < area[0] or area[2] < p["area"][0]
                    or p["area"][3] < area[1] or area[3] < p["area"][1])]
    return (sit.now - max(ages)) if ages else None


# --- the three score shapes the commander writes ----------------------------

def hold_score(area):
    """Hold this address. Richness dies if the ground is lost, or if we are
    halved. Both are self-audible; attrition guarantees the exit."""
    return score(area, [note(silence(), label="ground-lost"),
                        note(attrition(1, 2), label="halved")],
                 kinds=("defend", "move"))


def strike_score(area):
    """Go and remove the interference. Richness dies when the opposition is
    gone, or when we are halved."""
    return score(area, [note(clear("enemy"), label="cleared"),
                        note(attrition(1, 2), label="halved")],
                 kinds=("attack", "move"))


def watch_score(area):
    """Stand and listen. Dies on contact or attrition — a watchman is
    non-combat, so cancellation is his cue to leave, not to fight."""
    return score(area, [note(cancellation("enemy", 1), label="contact"),
                        note(attrition(1, 2), label="halved")],
                 kinds=("observe", "move"))


def _area_around(sit, x, y, r=3):
    return (max(0, x - r), max(0, y - r),
            min(sit.w - 1, x + r), min(sit.h - 1, y + r))


def decide(sit, cfg=CONFIG):
    """The loop. Returns a list of actions:
       ("task", cid, score) | ("spawn", score) | ("scout", score) | ("hold",)
    Every score emitted is validated — the commander cannot issue what cannot
    be sung."""
    acts = []
    credits = sit.credits
    free = [c for c in sit.companies if not c["locked"]]
    ths = threats(sit, cfg)

    # 1. Opportunity first: their commander, lightly guarded, in reach.
    for g in ths:
        if "C" in g["cls"] and g["n"] <= cfg["strike_guard_max"] + 1 and free:
            dist = bfs_field(sit, (g["x"], g["y"]))
            near = min(free, key=lambda c: dist.get(tuple(c["pos"]), 1e9))
            if dist.get(tuple(near["pos"]), 1e9) < (sit.w + sit.h):
                acts.append(("task", near["cid"],
                             strike_score(_area_around(sit, g["x"], g["y"]))))
                free.remove(near)
            break

    # 2. Threats by score: tune the location; the nearest free company hears
    #    it. Else convert credits into a new voice.
    for g in ths:
        if "C" in g["cls"] and g["n"] <= cfg["strike_guard_max"] + 1:
            continue
        area = _area_around(sit, g["x"], g["y"])
        if free:
            dist = bfs_field(sit, (g["x"], g["y"]))
            near = min(free, key=lambda c: dist.get(tuple(c["pos"]), 1e9))
            acts.append(("task", near["cid"], hold_score(area)))
            free.remove(near)
        elif credits >= cfg["company_cost"]:
            acts.append(("spawn", hold_score(area)))
            credits -= cfg["company_cost"]

    # 3. Dark loops: a sector unseen too long gets a scout.
    for name in sit.sectors:
        age = sector_age(sit, name)
        if (age is None or age > cfg["dark_age"]) \
                and credits >= cfg["scout_cost"]:
            acts.append(("scout", watch_score(sit.sectors[name])))
            credits -= cfg["scout_cost"]
            break

    if not acts:
        acts.append(("hold",))

    for a in acts:                       # the law: nothing unsingable leaves
        if a[0] in ("task", "spawn", "scout"):
            ok, why = validate_score(a[-1])
            assert ok, "commander emitted an unsingable score: %s" % (why,)
    return acts
