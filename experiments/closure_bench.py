"""
Closure probation bench — does holonomy-driven dispatch EARN its place?

Scenario (the Better Door, belief edition): the enemy squad sits in one
sector; at a hidden tick it relocates to another. The commander learns only
from patrol reports delivered ON RETURN (messenger latency, as ruled).

Two arms, identical in every respect — same belief field, same fusion rule,
same patrol speed and viewshed — except HOW the next patrol is routed:

  A  fixed rotation      NE -> NW -> SE -> SW, forever (the baseline)
  B  closure-driven      choose_next_loop: believed mass x loop staleness

Metrics per run: detection latency (ticks from the enemy ARRIVING at its new
home to the commander's belief putting >= 0.35 mass within r=4 of it) and
localisation error (argmax distance at detection). Lower is better. If B
does not beat A materially, closure dispatch is OUT — per the adoption bar.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fortresslab_mini.worldmap import WorldMap
from fortresslab_mini.beliefs import BeliefField, choose_next_loop

W, H, VIEW, THRESH = 24, 24, 2, 0.35
BASE = (12, 22)
SECTORS = {"NW": (0, 0, 11, 11), "NE": (12, 0, 23, 11),
           "SW": (0, 12, 11, 23), "SE": (12, 12, 23, 23)}
HOMES = {"NW": (5, 5), "NE": (18, 5), "SW": (5, 18), "SE": (18, 18)}


def route_for(sector):
    """A lawnmower loop through the sector, out from and back to BASE."""
    x0, y0, x1, y1 = SECTORS[sector]
    pts = []
    for i, y in enumerate(range(y0 + 1, y1, 3)):
        xs = range(x0 + 1, x1, 2)
        pts += [(x, y) for x in (xs if i % 2 == 0 else reversed(list(xs)))]
    return pts


def run(dest, t_move, mode):
    """mode: 'rotation' | 'mass' (posterior-chasing) | 'residual' (alarm)."""
    wm = WorldMap(["." * W for _ in range(H)])
    belief = BeliefField(wm)
    enemy = list(HOMES["NE"])
    target = HOMES[dest]
    stale = {s: 0 for s in SECTORS}
    rotation = ["NE", "NW", "SE", "SW"]
    rot_i = 0

    t, t_arrived, patrol, detected = 0, None, None, None
    explore_loops = 0                     # residual alarm: explore-mode budget
    while t < 900:
        # world
        if t >= t_move and (enemy[0], enemy[1]) != target:
            enemy[0] += (target[0] > enemy[0]) - (target[0] < enemy[0])
            enemy[1] += (target[1] > enemy[1]) - (target[1] < enemy[1])
            if (enemy[0], enemy[1]) == target and t_arrived is None:
                t_arrived = t
        # commander transports belief every tick
        belief.predict()
        for s in stale:
            stale[s] += 1
        # patrol lifecycle
        if patrol is None:
            if mode == "rotation":
                sector = rotation[rot_i % 4]
            elif mode == "mass":
                sector = choose_next_loop(SECTORS, belief, stale)
            else:                          # residual: alarm flips the weights
                if explore_loops > 0:
                    sector = max(SECTORS, key=lambda s_: stale[s_])
                    explore_loops -= 1
                else:
                    sector = choose_next_loop(SECTORS, belief, stale)
            rot_i += 1
            patrol = {"route": route_for(sector), "i": 0,
                      "sector": sector, "obs": []}
        else:
            p = patrol
            if p["i"] < len(p["route"]):
                x, y = p["route"][p["i"]]
                seen = max(abs(enemy[0] - x), abs(enemy[1] - y)) <= VIEW
                p["obs"].append((x, y, seen, t))
                if seen:                       # log the contact cell itself
                    p["obs"].append((enemy[0], enemy[1], True, t))
                p["i"] += 1
            else:                              # returned: report fuses NOW
                # closure residual BEFORE fusing: the transported prediction
                # vs what the loop actually saw. Loud + all-empty = the world
                # moved behind the model's back -> explore.
                resid = sum(abs((1.0 if seen else 0.0)
                                - min(1.0, belief.mass_near(x, y, VIEW)))
                            for x, y, seen, _ in p["obs"])
                any_hit = any(o[2] for o in p["obs"])
                belief.fuse(p["obs"], now=t)
                stale[p["sector"]] = 0
                if mode == "residual" and resid > 0.6 and not any_hit:
                    explore_loops = 2
                patrol = None
        # detection check
        if t_arrived is not None and detected is None:
            if belief.mass_near(*target, 4) >= THRESH:
                ax, ay = belief.argmax()
                err = max(abs(ax - target[0]), abs(ay - target[1]))
                detected = (t - t_arrived, err)
        if detected:
            return detected
        t += 1
    return (900, 99)


def main():
    rows = []
    for dest in ("NW", "SW", "SE"):
        for t_move in (20, 45, 70, 95, 120, 145, 170):
            a = run(dest, t_move, "rotation")
            b = run(dest, t_move, "mass")
            c = run(dest, t_move, "residual")
            rows.append((dest, t_move, a, b, c))
    la = sum(r[2][0] for r in rows) / len(rows)
    lb = sum(r[3][0] for r in rows) / len(rows)
    lc = sum(r[4][0] for r in rows) / len(rows)
    print(f"{'dest':>4} {'t_move':>6} | {'rot':>5} | {'mass':>5} | {'resid':>5}")
    for dest, tm, a, b, c in rows:
        print(f"{dest:>4} {tm:>6} | {a[0]:>5} | {b[0]:>5} | {c[0]:>5}")
    print("-" * 40)
    print(f"mean latency   rotation {la:6.1f}   mass {lb:6.1f}   "
          f"residual {lc:6.1f}")
    print(f"vs rotation:   mass {100*(la-lb)/la:+.0f}%   "
          f"residual {100*(la-lc)/la:+.0f}%")


if __name__ == "__main__":
    main()
