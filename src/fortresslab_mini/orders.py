"""
Orders rung — grammar, validator, executor.

    order := (scope, release conditions)

An order is a guarded decision tree over a CLOSED predicate vocabulary.
Granularity grows the order, not the engine: the executor is the same
guard-evaluate-transition loop whether the tree has one clause or nine.

Rulings implemented here (2026-08-20):
  * bare Hold is malformed — an order must carry release conditions
  * release validity: releases must be definite outcomes, success and failure
    both covered; at least one exit the unit can trigger from its own local
    observation ("until recalled" alone soft-locks a company)
  * scope lattice: a detached sub-order's scope must sit inside the parent's
  * instruction capacity: tree size is bounded by the rank that carries it
  * order-lock: no re-tasking until a release fires
  * ferality: officer dead AND order complete/unfollowable -> feral
  * auto-join: a feral friendly within detection of an under-capacity company
    fills the open slot

Malformed orders are UNISSUABLE — excluded at legality, never punished.
Integer arithmetic only (attrition thresholds are integer fractions).
"""

from fortresslab_mini.kernel import cheb


# --- The closed predicate vocabulary ------------------------------------------
# local: verifiable by the unit from its own observation, no messenger needed.
# failure_exit: an outcome the unit itself can reach -- the guaranteed branch
# of the x-or-y release rule. "Arrival" predicates are local but NOT guaranteed
# (the messenger may never come), so they cannot be an order's only exit.

PREDICATES = {
    "always":             dict(local=True,  failure_exit=False),
    "time_at_or_after":   dict(local=True,  failure_exit=False),  # diegetic clock
    "messenger_contact":  dict(local=True,  failure_exit=False),
    "enemy_contact":      dict(local=True,  failure_exit=False),
    "no_enemy_contact":   dict(local=True,  failure_exit=False),
    "attrition_at_least": dict(local=True,  failure_exit=True),   # (num, den)
    "position_lost":      dict(local=True,  failure_exit=True),
    "remote_fact":        dict(local=False, failure_exit=False),  # far-side facts
}


def eval_guard(g, world):
    """Guards are tuples: (name, *args) or ('and', g1, g2, ...)."""
    op = g[0]
    if op == "and":
        return all(eval_guard(x, world) for x in g[1:])
    if op == "always":
        return True
    if op == "time_at_or_after":
        return world["hour"] >= g[1]
    if op == "messenger_contact":
        return bool(world.get("messenger_contact"))
    if op == "enemy_contact":
        return bool(world.get("enemy_contact"))
    if op == "no_enemy_contact":
        return not world.get("enemy_contact")
    if op == "attrition_at_least":
        lost, total = world["losses"]
        num, den = g[1], g[2]
        return lost * den >= num * total          # integers only
    if op == "position_lost":
        return bool(world.get("position_lost"))
    if op == "remote_fact":
        return bool(world.get("remote", {}).get(g[1]))
    raise ValueError(f"unknown predicate {op!r}")


def leaf_predicates(g):
    if g[0] == "and":
        return [n for x in g[1:] for n in leaf_predicates(x)]
    return [g[0]]


# --- Scope: the attenuating grant ---------------------------------------------
# scope := {"kinds": set of activity kinds, "area": (x0, y0, x1, y1)}

def area_within(inner, outer):
    ix0, iy0, ix1, iy1 = inner
    ox0, oy0, ox1, oy1 = outer
    return ox0 <= ix0 and oy0 <= iy0 and ix1 <= ox1 and iy1 <= oy1


def scope_within(sub, parent):
    """Attenuation, never amplification: kinds subset, area contained."""
    return set(sub["kinds"]) <= set(parent["kinds"]) \
        and area_within(sub["area"], parent["area"])


# --- Instruction capacity: tree size bounded by the head that carries it ------
# Measured in guards (edges), the branch points of the drafted tree,
# including any embedded sub-orders.

RANK_CAPACITY = {"sergeant": 8, "knight": 8, "captain": 24}


def order_size(order):
    n = len(order.get("global_edges", []))
    for node in order["nodes"].values():
        for e in node["edges"]:
            n += 1
            if "detach" in e:
                n += order_size(e["detach"]["order"])
    return n


# --- Validator: the compile-time check ----------------------------------------

def _release_edges(order):
    out = list(e for e in order.get("global_edges", []) if "release" in e)
    for node in order["nodes"].values():
        out += [e for e in node["edges"] if "release" in e]
    return out


def _release_reachable(order):
    """Every node must be able to reach a release. Global release edges apply
    everywhere, so their presence satisfies all nodes at once."""
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
                    if "goto" in e and reaches.get(e["goto"]):
                        reaches[nid] = True
                        changed = True
                    if "detach" in e and reaches.get(e["detach"]["goto"]):
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
        # Every release must be verifiable by the unit itself.
        for e in releases:
            names = leaf_predicates(e["when"])
            if not all(PREDICATES[n]["local"] for n in names):
                problems.append(f"release on non-local predicate(s) {names}")
        # The x-or-y rule: at least one release the unit can reach on its own
        # -- a guaranteed outcome of failure, not an arrival that may never come.
        if not any(all(PREDICATES[n]["local"] for n in leaf_predicates(e["when"]))
                   and any(PREDICATES[n]["failure_exit"]
                           for n in leaf_predicates(e["when"]))
                   for e in releases):
            problems.append("no guaranteed self-triggerable exit "
                            "(release could depend on an arrival that never comes)")

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
                ok, why = validate_order(sub, rank)
                problems += [f"sub-order: {p}" for p in why]

    size = order_size(order)
    cap = RANK_CAPACITY[rank]
    if size > cap:
        problems.append(f"order has {size} guards; {rank} capacity is {cap}")

    return (not problems), problems


# --- Executor: guard-evaluate-transition, one edge per tick -------------------

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
        self.released = None            # release reason once fired
        self.stale = False              # officer dead, order still live
        self.detachments = []           # (n_units, OrderExec)

    def can_retask(self):
        """The order-lock: no new orders until the release fires."""
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
        sub = OrderExec(d["order"], _validated=True)   # validated at parent issue
        self.detachments.append((d["n"], sub))
        self.node = d["goto"]
        return ("detach", d["n"], sub)


# --- Unit lifecycle: obedient -> stale -> feral -> rallied --------------------

ORDERED, STALE, FERAL, AWAITING = "ordered", "stale", "feral", "awaiting"


def company_status(officer_alive, exec_):
    """The leash, the wind-up toy, and the slipped leash.

    * order live + officer alive        -> ORDERED
    * order live + officer dead         -> STALE  (executes unchanged)
    * order done/absent + officer alive -> AWAITING new orders
    * order done/absent + officer dead  -> FERAL  (raw bloodlust)
    """
    order_live = exec_ is not None and exec_.released is None
    if order_live:
        return ORDERED if officer_alive else STALE
    return AWAITING if officer_alive else FERAL


def try_rally(feral_pos, companies, detection_radius):
    """Auto-join: a feral friendly within detection of an under-capacity
    company fills the open slot. First eligible company in listed order."""
    for c in companies:
        if c["members"] < c["capacity"] \
                and cheb(feral_pos, c["pos"]) <= detection_radius:
            c["members"] += 1
            return c
    return None
