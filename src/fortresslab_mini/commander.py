"""
Commander v0 — the decision loop, built to be examined.

Input:  a SITUATION — the commander's quilt (timestamped patches), his roster,
        his credits, the clock.
Output: a DECISION — orders dispatched, purchases made, scouts sent, or
        explicitly nothing. Every emitted order passes the real validator; an
        illegal order from the commander is a harness failure, not a bad play.

v0 is deliberately simple and legible: fuse the quilt (last-write-wins per
area, freshness-weighted), cluster sightings into threats, score by
mass x freshness / response distance, match unlocked companies to threats,
convert credits when uncovered threat remains, and close dark loops with
scouts. The point is not sophistication — it is that the WAR COLLEGE battery
(tests/test_war_college.py) defines the behavioural contract every smarter
commander must also pass.

Every tunable in CONFIG. Floats permitted (ruled 2026-08-20).
"""

from collections import deque

from fortresslab_mini.orders import validate_order, contact, losses_at_least

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


def defend_order(area):
    sc = {"kinds": {"defend", "move"}, "area": area}
    return {"scope": sc, "start": "hold",
            "nodes": {"hold": {"scope": sc, "edges": [
                {"when": contact("messenger"), "release": "recalled"}]}},
            "global_edges": [{"when": losses_at_least(1, 2),
                              "release": "return"}]}


def strike_order(area):
    sc = {"kinds": {"attack", "move"}, "area": area}
    return {"scope": sc, "start": "strike",
            "nodes": {"strike": {"scope": sc, "edges": [
                {"when": contact("messenger"), "release": "recalled"}]}},
            "global_edges": [{"when": losses_at_least(1, 2),
                              "release": "return"}]}


def scout_order(area):
    sc = {"kinds": {"observe", "move"}, "area": area}
    return {"scope": sc, "start": "watch",
            "nodes": {"watch": {"scope": sc, "edges": [
                {"when": contact("messenger"), "release": "relieved"}]}},
            "global_edges": [{"when": losses_at_least(1, 2),
                              "release": "return"}]}


def _area_around(sit, x, y, r=3):
    return (max(0, x - r), max(0, y - r),
            min(sit.w - 1, x + r), min(sit.h - 1, y + r))


def decide(sit, cfg=CONFIG):
    """The loop, v0. Returns a list of actions:
       ("task", cid, order) | ("spawn", order) | ("scout", order) | ("hold",)
    Every order emitted is validator-checked — the commander cannot issue
    what the grammar refuses."""
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
                             strike_order(_area_around(sit, g["x"], g["y"]))))
                free.remove(near)
            break

    # 2. Threats by score: nearest free company each; else convert credits.
    for g in ths:
        if "C" in g["cls"] and g["n"] <= cfg["strike_guard_max"] + 1:
            continue
        area = _area_around(sit, g["x"], g["y"])
        if free:
            dist = bfs_field(sit, (g["x"], g["y"]))
            near = min(free, key=lambda c: dist.get(tuple(c["pos"]), 1e9))
            acts.append(("task", near["cid"], defend_order(area)))
            free.remove(near)
        elif credits >= cfg["company_cost"]:
            acts.append(("spawn", defend_order(area)))
            credits -= cfg["company_cost"]

    # 3. Dark loops: a sector unseen too long gets a scout.
    for name in sit.sectors:
        age = sector_age(sit, name)
        if (age is None or age > cfg["dark_age"]) \
                and credits >= cfg["scout_cost"]:
            acts.append(("scout", scout_order(sit.sectors[name])))
            credits -= cfg["scout_cost"]
            break

    if not acts:
        acts.append(("hold",))

    for a in acts:                       # the law: nothing leaves malformed
        if a[0] in ("task", "spawn", "scout"):
            ok, why = validate_order(a[-1])
            assert ok, f"commander emitted an illegal order: {why}"
    return acts
