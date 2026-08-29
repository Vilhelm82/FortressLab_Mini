"""
The development map — one castle, used throughout.

A fixture, not a scenario. It exists so every subsystem is exercised against
the same geometry: stone and timber side by side, height variation, a gate
that opens into a cul-de-sac, a hollow keep, a postern, and open field to
approach across.

Legend (worldmap.WorldMap):
    .  open ground        =  palisade (timber)     G  gate
    #  stone, 1 high      2  stone, 2 high         3  stone, 3 high
    4  stone, 4 high      S  attacker start        T  the war room

Geometry, west to east:

    x 0-11   open field. The attacker's ground.
    x 12     west curtain, with the MAIN GATE at y10-11.
    x 13-17  the BARBICAN POCKET — a cul-de-sac. The gate opens into it and
             the only way out is north. Anything that comes through the gate
             is in a box.
    x 18     the spur wall making that box, y6-13, closed along y14.
    x 19-32  the bailey.
    x 26-30  the KEEP, hollow, 4 high, one doorway south at (28,12).
             The war room sits inside at (28,10).
    x 24-31  on y19: TIMBER palisade — the one stretch that leaks sound.
    corners  towers, 3 high. Curtain elsewhere 2 high.
    x 26     on y2: the POSTERN.

Twelve regions are named here, which is the maximum. A castle may use
fewer — the address space simply goes unused. The designer assigns them;
the game assigns which fundamental each receives.
"""

W, H = 36, 22
GATE_Y = (10, 11)
POSTERN_X = 26
KEEP = (26, 8, 30, 12)          # x0, y0, x1, y1 — hollow, 4 high
KEEP_DOOR = (28, 12)
WAR_ROOM = (28, 10)
SPUR_X = 18
SPUR_Y = (6, 13)
POCKET = (13, 3, 17, 13)        # the cul-de-sac behind the gate
PALISADE_X = (24, 31)           # timber stretch on the south wall
CASTLE = (12, 2, 33, 19)


def _blank():
    return [["." for _ in range(W)] for _ in range(H)]


def _build():
    g = _blank()
    x0, y0, x1, y1 = CASTLE

    for x in range(x0, x1 + 1):                     # north and south curtain
        g[y0][x] = "2"
        g[y1][x] = "=" if PALISADE_X[0] <= x <= PALISADE_X[1] else "2"
    for y in range(y0, y1 + 1):                     # west and east curtain
        g[y][x0] = "2"
        g[y][x1] = "2"
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        g[cy][cx] = "3"                             # corner towers

    g[y0][POSTERN_X] = "G"                          # postern, north face
    for y in range(GATE_Y[0], GATE_Y[1] + 1):       # main gate, west face
        g[y][x0] = "G"

    for y in range(SPUR_Y[0], SPUR_Y[1] + 1):       # the spur
        g[y][SPUR_X] = "#"
    for x in range(x0 + 1, SPUR_X + 1):             # closing the pocket
        g[SPUR_Y[1] + 1][x] = "#"

    kx0, ky0, kx1, ky1 = KEEP                       # the keep, hollow
    for x in range(kx0, kx1 + 1):
        g[ky0][x] = "4"
        g[ky1][x] = "4"
    for y in range(ky0, ky1 + 1):
        g[y][kx0] = "4"
        g[y][kx1] = "4"
    g[KEEP_DOOR[1]][KEEP_DOOR[0]] = "."

    g[WAR_ROOM[1]][WAR_ROOM[0]] = "T"
    g[GATE_Y[0]][2] = "S"                           # attacker start, in field
    return ["".join(row) for row in g]


ROWS = _build()


# --- the twelve addressable regions ------------------------------------------
# Names only. Which fundamental each receives is auto-assigned by the game
# (ruled): this is the division, not the tuning. A region is a list of
# rectangles — real regions are not rectangles, and the west curtain is cut
# in two by its own gate.
# Regions do not partition the map: they name the places worth addressing.

REGIONS = {
    "field":         [(0, 0, 11, 21)],
    "main-gate":     [(12, 9, 12, 12)],
    "barbican":      [(13, 3, 17, 13)],
    "west-curtain":  [(12, 2, 12, 8), (12, 13, 12, 19)],
    "north-curtain": [(13, 2, 25, 2)],
    "postern":       [(26, 2, 26, 2)],
    "east-curtain":  [(33, 2, 33, 19)],
    "south-curtain": [(13, 19, 23, 19)],
    "palisade":      [(24, 19, 31, 19)],
    "bailey-north":  [(19, 3, 32, 7)],
    "bailey-south":  [(19, 14, 32, 18)],
    "keep":          [(26, 8, 30, 12)],
}


def worldmap():
    """A WorldMap over this castle. Import and use; do not copy the strings."""
    from fortresslab_mini.worldmap import WorldMap
    return WorldMap(ROWS)


def material_cells():
    """(stone, timber) cell sets, for resonance.Grid until it reads the map
    directly (DEBT D3)."""
    stone, timber = set(), set()
    for y, row in enumerate(ROWS):
        for x, ch in enumerate(row):
            if ch == "=":
                timber.add((x, y))
            elif ch in "#234G":
                stone.add((x, y))
    return stone, timber


def render():
    """The map with axis rulers, for eyeballing."""
    tens = "   " + "".join(str((x // 10) % 10) for x in range(W))
    ones = "   " + "".join(str(x % 10) for x in range(W))
    body = ["%2d %s" % (y, r) for y, r in enumerate(ROWS)]
    return "\n".join([tens, ones] + body)


if __name__ == "__main__":
    print(render())
