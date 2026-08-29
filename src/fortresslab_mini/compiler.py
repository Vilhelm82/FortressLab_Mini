"""
The compiler: grammar order -> resonance performance (§25 architecture).

    interface (orders.py / UI)  ->  COMPILER  ->  runtime (resonance.py)

Humans and the AI commander author in the ruled grammar; this translates each
validated order into sheet music — an address tuning plus extension notes per
part — and refuses what cannot be sung. Compilation failure is a legality
filter (§25): an order that cannot be sung is an order the game does not
permit. Clock and elapsed guards are refused by §14 (the clock is scrapped).

Release mapping (the three ruled mechanisms, plus their own-state family):

    count(enemy, assigned) >= 1      -> SILENCE      (objective lost)
    count(cls, here|visible) >= n    -> CANCELLATION (interference present)
    eq count(cls, .) 0 / not(contact)-> CLEAR        (interference absent)
    ratio_ge(losses, initial, k, n)  -> ATTRITION    (own amplitude drop)
    self(attr) <= 0                  -> SPENT        (own state; Will's §13
                                        gate example: maj-7 = out of ammo)
    hazard(kind, region)             -> HAZARD       (environmental)
    contact('messenger')             -> not a note: recall = new sheet music

AND inside one guard  -> one note that dies only when ALL conditions hold.
OR across guards/edges -> separate notes; ANY note dying releases (a drop in
richness motivates relocation — §13).
"""

from fortresslab_mini.orders import validate_order, MalformedOrder
from fortresslab_mini.resonance import (dyad_specifier, extension,
                                        region_root)

MAX_LAYERS = 6          # the scale itself is the cap (proposal, layer table)


class CompileError(Exception):
    """This order cannot be sung. That is a ruling, not a bug."""


class AddressBook:
    """The game auto-assigns frequencies (§16-addressing): regions get
    fundamentals in listed order, posts get diatonic degrees in listed
    order. Commanders never choose notes — only where and what conditions."""

    def __init__(self, regions):
        if len(regions) > 12:
            raise CompileError("a map has at most 12 addressable regions")
        self.regions = regions
        for r in regions:
            if len(r.get("posts", ())) > 6:
                raise CompileError("a region has at most 6 dyad posts")

    @staticmethod
    def _overlap(a, b):
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return not (ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0)

    def resolve(self, area):
        """area -> (region_ix, degree_ix or None). Region-level when the
        order's area covers the whole region."""
        for ri, r in enumerate(self.regions):
            if self._overlap(area, r["area"]):
                if area == tuple(r["area"]) or not r.get("posts"):
                    return ri, None
                cx = (area[0] + area[2]) / 2
                cy = (area[1] + area[3]) / 2
                best = min(range(len(r["posts"])),
                           key=lambda i: (r["posts"][i][0]-cx)**2
                                       + (r["posts"][i][1]-cy)**2)
                return ri, best
        raise CompileError("order area lies in no addressed region")


# --- guard -> mechanism conditions -------------------------------------------

def _atom(term_guard):
    op = term_guard[0]
    if op in ("ge", "le", "eq"):
        a, b = term_guard[1], term_guard[2]
        if isinstance(a, tuple):
            if a[0] in ("clock", "elapsed"):
                raise CompileError(
                    f"{a[0]} guard cannot be sung — the clock was scrapped "
                    "(§14); condition orders on the environment instead")
            if a[0] == "count":
                cls, region = a[1], a[2]
                if op == "ge":
                    if cls == "messenger":
                        return ("recall",)
                    if region == "assigned":
                        return ("silence",)
                    return ("cancellation", cls, b)
                if op == "eq" and b == 0:
                    return ("clear", cls)
            if a[0] == "self":
                if op == "le":
                    return ("spent", a[1])
                raise CompileError(f"unsingable self comparison {term_guard!r}")
            if a[0] == "hazard":
                return ("hazard", a[1], a[2])
        raise CompileError(f"unsingable guard {term_guard!r}")
    if op == "ratio_ge":
        t = term_guard[1]
        if isinstance(t, tuple) and t == ("self", "losses"):
            return ("attrition", term_guard[3], term_guard[4])
        raise CompileError(f"unsingable ratio {term_guard!r}")
    raise CompileError(f"unsingable guard {term_guard!r}")


def _conditions(guard):
    """One guard -> list of alternative condition-sets (DNF-lite):
    outer list = OR (each entry its own note), inner set = AND."""
    op = guard[0]
    if op == "or":
        out = []
        for g in guard[1:]:
            out += _conditions(g)
        return out
    if op == "and":
        combos = [[]]
        for g in guard[1:]:
            alts = _conditions(g)
            combos = [c + a for c in combos for a in alts]
        return combos
    if op == "not":
        inner = guard[1]
        if inner[0] == "ge" and isinstance(inner[1], tuple) \
                and inner[1][0] == "count":
            return [[("clear", inner[1][1])]]
        raise CompileError("unsingable negation — say what IS, not what isn't")
    return [[_atom(guard)]]


def _release_guards(order):
    out = [e["when"] for e in order.get("global_edges", []) if "release" in e]
    for node in order["nodes"].values():
        out += [e["when"] for e in node["edges"] if "release" in e]
    return out


def _detachments(order):
    for node in order["nodes"].values():
        for e in node["edges"]:
            if "detach" in e:
                yield e["detach"]


def compile_order(order, book, rank="sergeant"):
    """Validated grammar order -> performance dict:
       {address, tuning, parts:[{filter,address,tuning,notes}], recall}"""
    ok, why = validate_order(order, rank)
    if not ok:
        raise MalformedOrder("; ".join(why))

    def compile_part(sub, filt):
        region, degree = book.resolve(tuple(sub["scope"]["area"]))
        tuning = [region_root(region)]
        if degree is not None:
            tuning.append(dyad_specifier(region, degree))
        notes, recall = [], False
        for g in _release_guards(sub):
            for conds in _conditions(g):
                if ("recall",) in conds:
                    recall = True
                    conds = [c for c in conds if c != ("recall",)]
                    if not conds:
                        continue
                notes.append(conds)
        if len(notes) > MAX_LAYERS:
            raise CompileError(
                f"order needs {len(notes)} extension notes; the scale caps "
                f"complexity at {MAX_LAYERS} layers above the root")
        sung = [{"note": extension(region, i), "conditions": conds,
                 "label": f"ext{i}"} for i, conds in enumerate(notes)]
        return {"filter": filt, "region": region, "degree": degree,
                "tuning": tuning, "notes": sung, "recall": recall}

    parts = [compile_part(order, ("company", None))]
    for d in _detachments(order):
        parts.append(compile_part(d["order"], ("count", d["n"])))
    return {"parts": parts,
            "recall_via_messenger": any(p["recall"] for p in parts)}


class PerformanceState:
    """Executes one compiled part against the shared world dict.

    v0 conformance runtime: mechanism conditions read the same ground truth
    the grammar executor reads, so the two systems can be proven to release
    on the same tick. The field-integrated version replaces these proxies
    with real spectra (interference, own amplitude, root silence) — the
    physics side is already proven by tests/test_resonance.py; this proves
    the MAPPING."""

    def __init__(self, part):
        self.part = part
        self.dead = [False] * len(part["notes"])
        self.released = None

    @staticmethod
    def _cond(c, world):
        kind = c[0]
        if kind == "silence":
            return world["count"].get(("enemy", "assigned"), 0) >= 1 \
                or world.get("root_silent", False)
        if kind == "cancellation":
            return world["count"].get((c[1], "here"), 0) >= c[2] \
                or world["count"].get((c[1], "visible"), 0) >= c[2]
        if kind == "clear":
            return world["count"].get((c[1], "here"), 0) == 0
        if kind == "attrition":
            s = world["self"]
            return s["losses"] * c[2] >= c[1] * s["initial"]
        if kind == "spent":
            return world["self"][c[1]] <= 0
        if kind == "hazard":
            return world["hazard"].get((c[1], c[2]), 0) >= 1
        raise ValueError(c)

    def step(self, world):
        if self.released is not None:
            return None
        for i, note in enumerate(self.part["notes"]):
            if not self.dead[i] and all(self._cond(c, world)
                                        for c in note["conditions"]):
                self.dead[i] = True          # the note falls silent
                self.released = note["label"]
                return ("release", note["label"])
        return None
