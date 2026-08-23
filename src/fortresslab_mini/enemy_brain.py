"""
Enemy-brain planner — the attacker's cost-field engine.

A wall is not an obstacle; it is an expensive edge. Cost of entering a cell:
    1 (travel tick) + breach(cell) + LAMBDA_RISK * exposure(cell)

Dijkstra over that graph IS the path of least resistance. No siege logic,
no "attack the weak point" rule -- weakness is just the cheapest path,
discovered. Integer arithmetic throughout.

This same engine later becomes the defender's threat model ("if I were them,
where does current flow?") and the individual unit's risk-aware router.
"""

import heapq

from fortresslab_mini.worldmap import DIRS8, BREACH

LAMBDA_RISK = 8         # ticks-equivalent price of crossing one fire line


def edge_cost(wm, exp, x, y):
    return 1 + BREACH[wm.cell[y][x]] + LAMBDA_RISK * exp[y][x]


def cost_field(wm, exp, source):
    """Dijkstra distances from `source` to every cell. dist[y][x] or None."""
    dist = [[None] * wm.w for _ in range(wm.h)]
    sx, sy = source
    dist[sy][sx] = 0
    pq = [(0, sx, sy)]
    while pq:
        d, x, y = heapq.heappop(pq)
        if dist[y][x] != d:
            continue
        for dx, dy in DIRS8:
            nx, ny = x + dx, y + dy
            if not wm.inside(nx, ny):
                continue
            nd = d + edge_cost(wm, exp, nx, ny)
            if dist[ny][nx] is None or nd < dist[ny][nx]:
                dist[ny][nx] = nd
                heapq.heappush(pq, (nd, nx, ny))
    return dist


def best_path(wm, exp, dist, target):
    """Walk back from target along steepest cost descent."""
    if dist[target[1]][target[0]] is None:
        return None
    path = [target]
    x, y = target
    while dist[y][x] != 0:
        best = None
        for dx, dy in DIRS8:
            px, py = x + dx, y + dy
            if wm.inside(px, py) and dist[py][px] is not None:
                need = dist[y][x] - edge_cost(wm, exp, x, y)
                if dist[py][px] == need and (best is None or dist[py][px] < best[0]):
                    best = (dist[py][px], px, py)
        if best is None:
            return None
        _, x, y = best
        path.append((x, y))
    path.reverse()
    return path


def breakdown(wm, exp, path):
    """Where did the cost go? travel / breach / exposure, plus entry points."""
    travel = breach = exposure = 0
    entries = []
    for (x, y) in path[1:]:
        travel += 1
        b = BREACH[wm.cell[y][x]]
        breach += b
        if b:
            entries.append((x, y))
        exposure += LAMBDA_RISK * exp[y][x]
    return {"travel": travel, "breach": breach, "exposure": exposure,
            "total": travel + breach + exposure, "entries": entries}


def plan(wm):
    """Full stage-1 report: cost field, chosen path, breakdown, and the
    conductance ranking -- the top alternative ways in, because current divides
    across parallel paths rather than taking only one."""
    exp = wm.exposure_field()
    d_s = cost_field(wm, exp, wm.start)
    d_t = cost_field(wm, exp, wm.target)
    path = best_path(wm, exp, d_s, wm.target)

    cands = []
    for y in range(wm.h):
        for x in range(wm.w):
            if BREACH[wm.cell[y][x]] and d_s[y][x] is not None \
                    and d_t[y][x] is not None:
                thru = d_s[y][x] + d_t[y][x] - edge_cost(wm, exp, x, y)
                cands.append((thru, (x, y)))
    cands.sort()

    return {"exp": exp, "dist": d_s, "path": path,
            "report": breakdown(wm, exp, path) if path else None,
            "breach_ranking": cands[:5]}


def render(wm, result):
    """ASCII: the world with the chosen path drawn as 'o'."""
    from fortresslab_mini.worldmap import WALL, PALISADE, GATE
    glyph = {WALL: '#', PALISADE: '=', GATE: 'G'}
    grid = [[glyph.get(wm.cell[y][x], '.') for x in range(wm.w)]
            for y in range(wm.h)]
    for ax, ay in wm.archers:
        grid[ay][ax] = 'A' if grid[ay][ax] == '.' else 'W'
    if result["path"]:
        for (x, y) in result["path"]:
            if grid[y][x] in '.=G':
                grid[y][x] = 'o'
    sx, sy = wm.start
    tx, ty = wm.target
    grid[sy][sx], grid[ty][tx] = 'S', 'T'
    return "\n".join("".join(r) for r in grid)
