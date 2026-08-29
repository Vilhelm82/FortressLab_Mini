"""
Watch it run.

Two ways:

    python3 -m fortresslab_mini.watch                 list the scenarios
    python3 -m fortresslab_mini.watch choir           play one in the terminal
    python3 -m fortresslab_mini.watch choir --html    write a scrubbable page

The terminal view redraws the map each tick. The HTML view records the whole
run first and gives you a slider, so you can step back and forth — which is
the ruled way to watch (replay and scrub, never live-stream).

Glyphs: uppercase = a mover, lowercase = a tuned but empty post.
"""

import json
import sys

from fortresslab_mini.devmap import GATE_Y, ROWS, WAR_ROOM, H, W, \
    material_cells
from fortresslab_mini.resonance import (Emitter, Grid, dyad_specifier,
                                        leader_note, region_root)
from fortresslab_mini.stepper import (DEAD, Mover, Stepper,
                                      chase_strongest_canceller,
                                      follow_then_fold, hold, seek_harmony,
                                      sneak_to)

STONE, TIMBER = material_cells()


def grid(open_gate=False):
    g = Grid(W, H, stone=STONE, timber=TIMBER)
    if open_gate:
        g.stone = set(g.stone) - {(12, GATE_Y[0]), (12, GATE_Y[1])}
    return g


def post(xy, region, degree):
    return Emitter(xy, [region_root(region), dyad_specifier(region, degree)])


# --- scenarios ---------------------------------------------------------------
# Each returns (stepper, glyphs, ticks, blurb). glyphs maps name -> character.

def sc_march():
    bailey, decoy = post((22, 5), 4, 1), post((22, 17), 9, 3)
    m = Mover(Emitter((20, 10), bailey.notes),
              goal=seek_harmony([bailey, decoy]), name="man")
    return (Stepper(grid(), [m], statics=[bailey, decoy]),
            {"man": "M", "post": "p", "decoy": "d"}, 40,
            "One man, two tuned posts. He goes to the one he harmonises with.")


def sc_door():
    inside = post(WAR_ROOM, 11, 0)
    m = Mover(Emitter((28, 5), inside.notes), goal=seek_harmony([inside]),
              name="man")
    return (Stepper(grid(), [m], statics=[inside]),
            {"man": "M", "post": "p"}, 60,
            "The war room is inside the keep. He must find the one door.")


def sc_choir():
    tower = post((32, 3), 6, 2)
    lead = Mover(Emitter((14, 4), [leader_note(6)]), name="sergeant")
    lead.goal = lambda m, f, w: tower.pos
    man = Mover(Emitter((13, 4), []), name="man")
    man.goal = follow_then_fold(lead, tower)
    return (Stepper(grid(), [lead, man], statics=[tower]),
            {"sergeant": "S", "man": "M", "post": "p"}, 60,
            "He follows the sergeant until the post's deeper root drowns "
            "him out, then folds off to the wall.")


def sc_leader_dies():
    tower = post((32, 3), 6, 2)
    lead = Mover(Emitter((14, 4), [leader_note(6)]), name="sergeant")
    lead.goal = lambda m, f, w: tower.pos
    man = Mover(Emitter((13, 4), []), name="man")
    man.goal = follow_then_fold(lead, tower)
    s = Stepper(grid(), [lead, man], statics=[tower])
    s.kill_at = (6, lead)
    return (s, {"sergeant": "S", "man": "M", "post": "p"}, 60,
            "Same march. The sergeant is killed at tick 6 and the orders "
            "outlive him.")


def sc_duel():
    shared = [region_root(2)]
    home = Mover(Emitter((18, 17), shared, sign=+1), name="home")
    away = Mover(Emitter((26, 17), shared, sign=-1), name="away")
    home.goal = chase_strongest_canceller([away])
    away.goal = chase_strongest_canceller([home])
    return (Stepper(grid(), [home, away]),
            {"home": "H", "away": "A"}, 30,
            "Each hears the other cancelling his song and closes. Dead short.")


def sc_focus():
    shared = [region_root(2)]
    home = Mover(Emitter((20, 16), shared, sign=+1), name="home")
    weak = Mover(Emitter((20, 10), shared, sign=-1, numbers=1), name="weak")
    strong = Mover(Emitter((24, 16), shared, sign=-1, numbers=6),
                   name="strong")
    weak.goal = strong.goal = hold
    home.goal = chase_strongest_canceller([weak, strong])
    return (Stepper(grid(), [home, weak, strong]),
            {"home": "H", "weak": "a", "strong": "A"}, 20,
            "One enemy is nearer; the other is six-strong. He turns toward "
            "the louder cancellation, not the closer man.")


def sc_sneak():
    watcher = Mover(Emitter((12, 10), [], facing=(-1, 0)), goal=hold,
                    name="watchman")
    sneak = Mover(Emitter((2, 10), [region_root(0)], sign=-1, db=0.05),
                  name="sneak")
    sneak.goal = sneak_to((2, 20), [watcher])
    return (Stepper(grid(), [sneak, watcher]),
            {"sneak": "A", "watchman": "W"}, 40,
            "A quiet man crossing open ground, bending around what watches.")


def sc_killbox():
    bailey = post((24, 6), 5, 2)
    intr = Mover(Emitter((11, GATE_Y[0]), bailey.notes, sign=-1),
                 goal=seek_harmony([bailey]), name="intruder")
    return (Stepper(grid(open_gate=True), [intr], statics=[bailey]),
            {"intruder": "A", "post": "p"}, 80,
            "The gate is forced. Everything that comes through is in a box "
            "whose only way on is north, over the spur.")


SCENARIOS = {"march": sc_march, "door": sc_door, "choir": sc_choir,
             "leader-dies": sc_leader_dies, "duel": sc_duel,
             "focus": sc_focus, "sneak": sc_sneak, "killbox": sc_killbox}


# --- recording ---------------------------------------------------------------

def record(build):
    s, glyphs, ticks, blurb = build()
    kill = getattr(s, "kill_at", None)
    frames = []

    def snapshot():
        return {"t": s.tick,
                "movers": [{"n": m.name, "x": m.pos[0], "y": m.pos[1],
                            "dead": m.state == DEAD} for m in s.movers],
                "statics": [{"x": e.pos[0], "y": e.pos[1]}
                            for e in s.statics],
                "events": [e for e in s.log if e[0] == s.tick]}

    frames.append(snapshot())
    for _ in range(ticks):
        if kill and s.tick == kill[0]:
            kill[1].kill()
        before = [m.pos for m in s.movers]
        s.step()
        frames.append(snapshot())
        if all(m.state == DEAD for m in s.movers):
            break
        if before == [m.pos for m in s.movers] and s.tick > 2:
            break                                  # settled: nobody moved
    return frames, glyphs, blurb


def draw(frame, glyphs):
    grid_ = [list(r) for r in ROWS]
    for st in frame["statics"]:
        grid_[st["y"]][st["x"]] = glyphs.get("post", "p")
    for m in frame["movers"]:
        if m["dead"]:
            continue
        grid_[m["y"]][m["x"]] = glyphs.get(m["n"], "?")
    head = "   " + "".join(str(x % 10) for x in range(W))
    return "\n".join([head] + ["%2d %s" % (y, "".join(r))
                               for y, r in enumerate(grid_)])


def play(name, delay=0.25):
    import time
    frames, glyphs, blurb = record(SCENARIOS[name])
    for f in frames:
        print("\033[2J\033[H", end="")
        print("%s — tick %d/%d\n%s\n" % (name, f["t"], frames[-1]["t"], blurb))
        print(draw(f, glyphs))
        for e in f["events"]:
            print("  ! %s %s at %s" % (e[1], e[2], e[3]))
        time.sleep(delay)


HTML = """<!doctype html><meta charset=utf-8><title>%(name)s</title>
<style>
 body{background:#14110e;color:#d8cfc0;font:14px/1.45 ui-monospace,monospace;
      margin:0;padding:24px}
 h1{font-size:15px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:#c9a227;margin:0 0 4px}
 p.blurb{color:#8d8578;margin:0 0 18px;max-width:60ch}
 pre{line-height:1.15;font-size:15px;margin:0}
 .row{display:flex;gap:12px;align-items:center;margin:16px 0 8px}
 input[type=range]{flex:1;accent-color:#c9a227}
 button{background:#241f19;color:#d8cfc0;border:1px solid #443c31;
        padding:4px 12px;cursor:pointer;font:inherit}
 .ev{color:#b4483c;min-height:1.4em}
 b{color:#c9a227}i{color:#6f665a;font-style:normal}
 u{color:#7fa4b8;text-decoration:none}
</style>
<h1>%(name)s</h1><p class=blurb>%(blurb)s</p>
<div class=row><button id=pp>play</button>
<input type=range id=sl min=0 max=%(last)d value=0>
<span id=lab>0 / %(last)d</span></div>
<pre id=map></pre><div class=ev id=ev></div>
<script>
const ROWS=%(rows)s, F=%(frames)s, G=%(glyphs)s, W=%(w)d;
const head='   '+[...Array(W).keys()].map(x=>x%%10).join('');
function paint(i){
 const f=F[i], g=ROWS.map(r=>r.split(''));
 f.statics.forEach(s=>g[s.y][s.x]='p');
 f.movers.filter(m=>!m.dead).forEach(m=>g[m.y][m.x]=G[m.n]||'?');
 let out=head+'\\n'+g.map((r,y)=>String(y).padStart(2)+' '+r.join('')).join('\\n');
 out=out.replace(/[A-Z]/g,c=>'<b>'+c+'</b>').replace(/[p]/g,'<u>p</u>')
        .replace(/[#=234G]/g,c=>'<i>'+c+'</i>');
 document.getElementById('map').innerHTML=out;
 document.getElementById('lab').textContent=i+' / '+(F.length-1);
 document.getElementById('ev').textContent=
   f.events.map(e=>'! '+e[1]+' '+e[2]).join('  ');
 document.getElementById('sl').value=i;}
let i=0,timer=null;
document.getElementById('sl').oninput=e=>paint(+e.target.value);
document.getElementById('pp').onclick=function(){
 if(timer){clearInterval(timer);timer=null;this.textContent='play';return;}
 this.textContent='pause';
 timer=setInterval(()=>{i=(i+1)%%F.length;paint(i);},220);};
paint(0);
</script>"""


def write_html(name, path=None):
    frames, glyphs, blurb = record(SCENARIOS[name])
    path = path or ("%s.html" % name)
    with open(path, "w") as fh:
        fh.write(HTML % {"name": name, "blurb": blurb, "w": W,
                         "last": len(frames) - 1,
                         "rows": json.dumps(ROWS),
                         "frames": json.dumps(frames),
                         "glyphs": json.dumps(glyphs)})
    return path


def main(argv):
    if len(argv) < 2 or argv[1] not in SCENARIOS:
        print("scenarios:")
        for k, v in SCENARIOS.items():
            print("  %-12s %s" % (k, v()[3]))
        print("\nplay:  python3 -m fortresslab_mini.watch <name> [--html]")
        return
    if "--html" in argv:
        print("wrote", write_html(argv[1]))
    else:
        play(argv[1])


if __name__ == "__main__":
    main(sys.argv)
