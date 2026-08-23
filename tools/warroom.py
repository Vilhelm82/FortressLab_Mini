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


def analyse(rows):
    wm = WorldMap(rows)
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
            out = analyse(payload.get("rows", []))
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
