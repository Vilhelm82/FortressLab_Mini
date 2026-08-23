"""
Orders rung — generalised doctrine.

    order := (scope, release conditions)

RULED 2026-08-20: the language must cover anything that could happen without
listing possibilities. No named situations, no lookup table of patterns.
Conditions are composed from a small closed set of TERMS and COMPARATORS, so
any situation a commander could care about is a composition, never a new rule.

    guard := (cmp, term, term) | ("ratio_ge", term, term, num, den)
           | ("and"|"or"|"not", guard...)
    term  := ("count", class, region) | ("self", attr)
           | ("clock",) | ("elapsed",) | ("hazard", kind, region) | int

"Enemy contact" is not a predicate; it is count(enemy, here) >= 1.
"Position lost" is count(enemy, assigned) >= 1. "Out of ammo" is
self(ammo) <= 0. When fire, water, tunnels or engines land they register
CLASSES and HAZARD kinds -- the grammar does not change, and doctrine drafted
today keeps working.

Bounded on purpose: total operators, no loops, no recursion outside scope
nesting. General over the game's observables, not general computation --
which is what keeps validation decidable and compile-time refusal possible.
"""

from fortresslab_mini.kernel import cheb

CLASSES = {"enemy", "friend", "messenger", "officer", "civilian"}
HAZARDS = {"fire", "water", "smoke"}
SELF_ATTRS = {"strength", "initial", "losses", "ammo"}
LOCAL_REGIONS = {"here", "assigned", "visible"}

CMP = {"ge": lambda a, b: a >= b,
       "le": lambda a, b: a <= b,
       "eq": lambda a, b: a == b}


def region_is_local(r):
    return r in LOCAL_REGIONS


def eval_term(t, world):
    if isinstance(t, int):
        return t
    op = t[0]
    if op == "clock":
        return world["clock"]
    if op == "elapsed":
        return world["elapsed"]
    if op == "self":
        return world["self"][t[1]]
    if op == "count":
        return world["count"].get((t[1], t[2]), 0)
    if op == "hazard":
        return world["hazard"].get((t[1], t[2]), 0)
    raise ValueError(f"unknown term {t!r}")


def eval_guard(g, world):
    op = g[0]
    if op == "and":
        return all(eval_guard(x, world) for x in g[1:])
    if op == "or":
        return any(eval_guard(x, world) for x in g[1:])
    if op == "not":
        return not eval_guard(g[1], world)
    if op == "ratio_ge":
        a, b, num, den = eval_term(g[1], world), eval_term(g[2], world), g[3], g[4]
        return a * den >= num * b
    if op in CMP:
        return CMP[op](eval_term(g[1], world), eval_term(g[2], world))
    raise ValueError(f"unknown guard {op!r}")


def terms_of(g):
    op = g[0]
    if op in ("and", "or", "not"):
        return [t for x in g[1:] for t in terms_of(x)]
    return [t for t in g[1:] if isinstance(t, tuple)]


def guard_is_local(g):
    """Observable by the unit unaided: every region referenced is local."""
    for t in terms_of(g):
        if t[0] in ("count", "hazard") and not region_is_local(t[2]):
            return False
    return True


def guard_is_self_triggerable(g):
    """Depends only on the unit's own state or the passage of time.

    The general form of the x-or-y release rule. An arrival -- anything
    counting another party -- may never happen, so it can never be an
    order's only exit. Own attrition, own ammo, and elapsed time resolve.
    Nothing here names a situation; it reads the term types.
    """
    ts = terms_of(g)
    return bool(ts) and all(t[0] in ("self", "clock", "elapsed") for t in ts)


def area_within(inner, outer):
    ix0, iy0, ix1, iy1 = inner
    ox0, oy0, ox1, oy1 = outer
    return ox0 <= ix0 and oy0 <= iy0 and ix1 <= ox1 and iy1 <= oy1


def scope_within(sub, parent):
    """Attenuation, never amplification."""
    return set(sub["kinds"]) <= set(parent["kinds"]) \
        and area_within(sub["area"], parent["area"])


RANK_CAPACITY = {"sergeant": 8, "knight": 8, "captain": 24}


def order_size(order):
    n = len(order.get("global_edges", []))
    for node in order["nodes"].values():
        for e in node["edges"]:
            n += 1
            if "detach" in e:
                n += order_size(e["detach"]["order"])
    return n


def _release_edges(order):
    out = [e for e in order.get("global_edges", []) if "release" in e]
    for node in order["nodes"].values():
        out += [e for e in node["edges"] if "release" in e]
    return out


def _release_reachable(order):
    if any("release" in e for e in order.get("global_edges", [])):
        return True
    reaches = {nid: any("release" in e for e in n["edges"])
               for nid, n in order["nodes"].items()}
    changed = True
    while changed:
        changed = False
        for nid, n in order["nodes"].items():
            if not reaches[nid]:
                for e in n["edges"]:
                    tgt = e.get("goto") or (e.get("detach") or {}).get("goto")
                    if tgt and reaches.get(tgt):
                        reaches[nid] = True
                        changed = True
    return all(reaches.values())


def validate_order(order, rank="sergeant"):
    """Returns (ok, problems). Malformed orders are unissuable."""
    problems = []
    releases = _release_edges(order)

    if not releases:
        problems.append("bare order: no release conditions at all")
    else:
        for e in releases:
            if not guard_is_local(e["when"]):
                problems.append("release depends on a region the unit "
                                "cannot observe")
        if not any(guard_is_self_triggerable(e["when"]) for e in releases):
            problems.append("no guaranteed self-triggerable exit "
                            "(every release could depend on something "
                            "that never arrives)")

    if not _release_reachable(order):
        problems.append("a node cannot reach any release")

    for nid, node in order["nodes"].items():
        if not scope_within(node["scope"], order["scope"]):
            problems.append(f"node {nid!r} exceeds the order's granted scope")
        for e in node["edges"]:
            if "detach" in e:
                sub = e["detach"]["order"]
                if not scope_within(sub["scope"], order["scope"]):
                    problems.append("detached sub-order exceeds parent scope")
                _, why = validate_order(sub, rank)
                problems += [f"sub-order: {p}" for p in why]

    size, cap = order_size(order), RANK_CAPACITY[rank]
    if size > cap:
        problems.append(f"order has {size} guards; {rank} capacity is {cap}")

    return (not problems), problems


class MalformedOrder(Exception):
    pass


class OrderExec:
    """Runs one drafted order for one company. Deterministic: global edges
    first, then the current node's edges, in listed order; first true guard
    fires; at most one transition per tick."""

    def __init__(self, order, rank="sergeant", _validated=False):
        if not _validated:
            ok, why = validate_order(order, rank)
            if not ok:
                raise MalformedOrder("; ".join(why))
        self.order = order
        self.node = order["start"]
        self.released = None
        self.detachments = []

    def can_retask(self):
        """The order-lock: no new orders until a release fires."""
        return self.released is not None

    def current_scope(self):
        return self.order["nodes"][self.node]["scope"]

    def step(self, world):
        if self.released is not None:
            return None
        edges = list(self.order.get("global_edges", [])) \
            + list(self.order["nodes"][self.node]["edges"])
        for e in edges:
            if eval_guard(e["when"], world):
                return self._fire(e)
        return None

    def _fire(self, e):
        if "release" in e:
            self.released = e["release"]
            return ("release", e["release"])
        if "goto" in e:
            self.node = e["goto"]
            return ("goto", e["goto"])
        d = e["detach"]
        sub = OrderExec(d["order"], _validated=True)
        self.detachments.append((d["n"], sub))
        self.node = d["goto"]
        return ("detach", d["n"], sub)


ORDERED, STALE, FERAL, AWAITING = "ordered", "stale", "feral", "awaiting"


def company_status(officer_alive, exec_):
    order_live = exec_ is not None and exec_.released is None
    if order_live:
        return ORDERED if officer_alive else STALE
    return AWAITING if officer_alive else FERAL


def try_rally(feral_pos, companies, detection_radius):
    for c in companies:
        if c["members"] < c["capacity"] \
                and cheb(feral_pos, c["pos"]) <= detection_radius:
            c["members"] += 1
            return c
    return None


# --- Doctrine helpers: the repeatable language, composed not enumerated -------

def contact(cls="enemy", region="here", n=1):
    return ("ge", ("count", cls, region), n)


def absent(cls="enemy", region="here"):
    return ("eq", ("count", cls, region), 0)


def losses_at_least(num, den):
    return ("ratio_ge", ("self", "losses"), ("self", "initial"), num, den)


def clock_at_or_after(hour):
    return ("ge", ("clock",), hour)


def spent(attr="ammo"):
    return ("le", ("self", attr), 0)


def hazard_in(kind, region="here"):
    return ("ge", ("hazard", kind, region), 1)
