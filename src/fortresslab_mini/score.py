"""
Scores — the resonance-native order representation.

Replaces the legacy predicate grammar (`orders.py`, deleted 26 Aug 2026).
Orders are performances, not prose: a commander names WHERE and WHAT KILLS
THE RICHNESS, and the game auto-assigns frequencies. There is no clock, no
lookup table, and no guard that reads anything a unit cannot hear.

A note is an extension carrying one condition-set. Notes die when their
conditions hold; a dying note is a drop in richness, which motivates
relocation. That is the whole release mechanism.

THE THREE RULED MECHANISMS, plus their own-state family:

    SILENCE      objective lost — the location's fundamentals stop
    CANCELLATION opposed signal present — enemy interference
    ATTRITION    own amplitude falls — losses against initial strength
    SPENT        an own resource reaches zero (ammo; the gate example's 7th)
    CLEAR        opposed signal absent
    HAZARD       an environmental kind in a region

Locality is structural, not checked: every condition above is something the
unit hears or knows of itself. GUARDLOC cannot recur here — there is no
ground truth to read.
"""

MAX_LAYERS = 6          # the scale caps order complexity (6 non-root degrees)
MAX_REGIONS = 12
MAX_POSTS = 6

CONDITION_KINDS = {"silence", "cancellation", "attrition", "spent",
                   "clear", "hazard"}
SELF_RESOLVING = {"attrition", "spent"}     # will fall without an arrival
HAZARDS = {"fire", "water", "smoke"}
CLASSES = {"enemy", "friend", "civilian"}


def silence():
    """The objective's fundamentals fall silent — the location is lost."""
    return ("silence",)


def cancellation(cls="enemy", n=1):
    """Opposed signal present: n or more of cls interfering."""
    if cls not in CLASSES:
        raise ValueError("unknown class %r" % (cls,))
    return ("cancellation", cls, n)


def clear(cls="enemy"):
    """Opposed signal absent."""
    return ("clear", cls)


def attrition(num=1, den=2):
    """Own amplitude down to num/den of initial strength."""
    return ("attrition", num, den)


def spent(attr="ammo"):
    """An own resource reaches zero."""
    return ("spent", attr)


def hazard(kind, region="here"):
    if kind not in HAZARDS:
        raise ValueError("unknown hazard %r" % (kind,))
    return ("hazard", kind, region)


def note(*conditions, **kw):
    """One extension. Several conditions = the note dies only when ALL hold
    (the AND of the gate example). Separate notes = ANY may release."""
    conds = tuple(conditions)
    if not conds:
        raise ValueError("a note needs at least one condition")
    for c in conds:
        if c[0] not in CONDITION_KINDS:
            raise ValueError("unsingable condition %r" % (c,))
    label = kw.get("label") or "+".join(c[0] for c in conds)
    return {"conditions": conds, "label": label}


def part(notes, filter=("company", None), area=None, kinds=None):
    return {"filter": filter, "notes": list(notes), "area": area,
            "kinds": set(kinds) if kinds else None}


def score(area, notes, kinds=("defend", "move"), parts=(), recall=True):
    """recall=True means a messenger may deliver new sheet music. That is not
    a release: replacement, not relocation."""
    body = part(notes, ("company", None), tuple(area), kinds)
    return {"area": tuple(area), "kinds": set(kinds),
            "parts": [body] + list(parts), "recall": recall}


class MalformedScore(Exception):
    pass


def validate_score(sc):
    """(ok, problems). An unsingable score is unissuable."""
    problems = []
    if not sc["parts"]:
        problems.append("bare score: nobody is given anything to sing")
    for p in sc["parts"]:
        if not p["notes"]:
            problems.append("part %r has no notes: nothing can ever release it"
                            % (p["filter"],))
            continue
        if len(p["notes"]) > MAX_LAYERS:
            problems.append(
                "part %r needs %d notes; the scale caps complexity at %d "
                "layers above the root" % (p["filter"], len(p["notes"]),
                                           MAX_LAYERS))
        if not any(any(c[0] in SELF_RESOLVING for c in n["conditions"])
                   for n in p["notes"]):
            problems.append(
                "part %r has no self-resolving note: every release waits on "
                "something that may never arrive" % (p["filter"],))
        if p["kinds"] and not set(p["kinds"]) <= set(sc["kinds"]):
            problems.append("part %r exceeds the granted kinds (scope "
                            "attenuates, never amplifies)" % (p["filter"],))
    return (not problems), problems


class ScoreExec:
    """Performs one part. Deterministic: notes are checked in listed order,
    and the first whose conditions all hold falls silent and releases."""

    def __init__(self, sc, part_ix=0, _validated=False):
        if not _validated:
            ok, why = validate_score(sc)
            if not ok:
                raise MalformedScore("; ".join(why))
        self.score = sc
        self.part = sc["parts"][part_ix]
        self.dead = [False] * len(self.part["notes"])
        self.released = None

    def can_retask(self):
        """Order-lock: only new sheet music, or a release, changes the task."""
        return self.released is not None

    def current_area(self):
        return self.part["area"] or self.score["area"]

    def current_scope(self):
        return {"kinds": self.part["kinds"] or self.score["kinds"],
                "area": self.current_area()}

    def richness(self):
        """Live notes. Falls as conditions resolve — the order's own state."""
        return sum(1 for d in self.dead if not d)

    @staticmethod
    def _holds(c, w):
        k = c[0]
        if k == "silence":
            return bool(w.get("root_silent")) or \
                w["count"].get(("enemy", "assigned"), 0) >= 1
        if k == "cancellation":
            return max(w["count"].get((c[1], "here"), 0),
                       w["count"].get((c[1], "visible"), 0)) >= c[2]
        if k == "clear":
            return w["count"].get((c[1], "here"), 0) == 0
        if k == "attrition":
            s = w["self"]
            return s["losses"] * c[2] >= c[1] * s["initial"]
        if k == "spent":
            return w["self"].get(c[1], 0) <= 0
        if k == "hazard":
            return w["hazard"].get((c[1], c[2]), 0) >= 1
        raise ValueError(c)

    def step(self, world):
        if self.released is not None:
            return None
        for i, n in enumerate(self.part["notes"]):
            if not self.dead[i] and all(self._holds(c, world)
                                        for c in n["conditions"]):
                self.dead[i] = True
                self.released = n["label"]
                return ("release", n["label"])
        return None


ORDERED, STALE, SELF_DIRECTED, AWAITING = ("ordered", "stale",
                                           "self_directed", "awaiting")


def company_status(officer_alive, exec_):
    """STALE = cut from the chain, but the location still sings so the score
    holds. SELF_DIRECTED = no leader and no live score."""
    live = exec_ is not None and exec_.released is None
    if live:
        return ORDERED if officer_alive else STALE
    return AWAITING if officer_alive else SELF_DIRECTED
