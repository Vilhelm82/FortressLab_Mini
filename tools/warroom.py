"""
War-room prototype — the design loop in miniature.

    design -> seal -> the enemy brain analyses -> adversarial report

Stdlib only. Serves one page and calls the REAL planner, so the verdict you
get is the same cost field the tests run against. No mocked feedback, no
duplicated logic.

    python3 tools/warroom.py     ->  http://localhost:8770
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fortresslab_mini.worldmap import WorldMap                    # noqa: E402
from fortresslab_mini.enemy_brain import plan                     # noqa: E402

HERE = Path(__file__).resolve().parent

# Credits: 250 non-renewable, spendable any time (ruled 2026-08-20).
COSTS = {"archer": 1, "watchman": 1, "messenger": 1,
         "sergeant": 10, "captain": 50}


def flatten(cells, ents, w, h):
    """2.5D design -> the flat map the current planner reads.

    INTERIM (heights + subsurface ruled 2026-08-20): the planner is still 2D.
    Excavated galleries are DESIGNED but not yet read -- mining, counter-mining
    and collapse need the 2.5D planner. A column
    flattens to its BASE block type -- you breach a wall at its foot -- and
    an archer on a stack becomes 'W' (on a wall) or 'A' (on the ground).
    Height therefore does NOT yet affect breach cost, sightlines or vantage
    range. That is the next planner upgrade, not a silent approximation.
    """
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            stack = cells[y][x]
            ent = ents.get(f"{x},{y}")
            if ent in ("T", "S"):
                line.append(ent)
            elif ent == "A":
                line.append("W" if stack else "A")
            elif stack:
                line.append(stack[0])
            else:
                line.append(".")
        rows.append("".join(line))
    return rows


def analyse(cells, ents, w, h, subs=None):
    wm = WorldMap(flatten(cells, ents, w, h))
    if wm.start is None or wm.target is None:
        return {"error": "map needs both an attacker start (S) and a war-room (T)"}
    r = plan(wm)
    if not r["path"]:
        return {"error": "no path — the target is unreachable"}
    return {
        "path": r["path"],
        "report": r["report"],
        "ranking": [[c, list(xy)] for c, xy in r["breach_ranking"]],
        "exposure": r["exp"],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = (HERE / "warroom.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        try:
            out = analyse(payload["cells"], payload.get("ents", {}),
                          payload["w"], payload["h"],
                          payload.get("subs"))
        except Exception as exc:                       # surface, never swallow
            out = {"error": f"{type(exc).__name__}: {exc}"}
        body = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    print(f"war-room on http://localhost:{port}  (ctrl-c to stop)")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
