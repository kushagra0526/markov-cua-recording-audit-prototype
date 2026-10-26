"""Audit a recorded session: which coordinate space are the clicks in, and does the narration match what was clicked?

Click -> candidate transform (scale, offset) -> UI element under it. The transform that puts the most clicks on an
interactive element wins; narration time shift and label mismatches are then judged under that transform.
"""
from .gen import H, W, hit

SCALES = [0.5, 0.667, 0.75, 1.0, 1.25, 1.33, 1.5, 2.0, 3.0]
OFFSETS = [(0, 0), (1920, 0), (-1920, 0), (0, 1080), (0, -1080), (2560, 0), (-2560, 0), (1920, 1080), (-1920, 1080)]
SHIFTS = [i * 0.25 for i in range(-24, 25)]


def to_screen(e, s, o):
    return (e["x"] - o[0]) / s, (e["y"] - o[1]) / s


def element_rate(boxes, events, s, o):
    n = sum(1 for e in events if hit(boxes, *to_screen(e, s, o)) not in (None, "CANVAS"))
    return n / len(events)


def fit_transform(boxes, events):
    best = max(((element_rate(boxes, events, s, o), -abs(s - 1) - (o != (0, 0)), s, o) for s in SCALES for o in OFFSETS))
    return best[2], best[3], best[0]


def match(events, narration, delta):
    """Narration line for each click: the closest line after shifting, within 0.5 s of the usual 0.6 s lead."""
    out = []
    for e in events:
        c = min(narration, key=lambda n: abs(n["t"] - delta - e["t"] + 0.6))
        out.append(c["label"] if abs(c["t"] - delta - e["t"] + 0.6) <= 0.5 else None)
    return out


def audit(sess):
    boxes, ev, nar = sess["boxes"], sess["events"], sess["narration"]
    s, o, rate = fit_transform(boxes, ev)
    if rate < 0.5:  # no known transform puts most clicks on UI elements
        return {"verdict": "REJECT", "codes": ["COORD_UNFITTED"], "scale": None, "offset": None, "delta": None, "flags": [], "targets": None}
    hits = [hit(boxes, *to_screen(e, s, o)) for e in ev]

    def agree(d):
        lab = match(ev, nar, d)
        return sum(1 for h, l in zip(hits, lab) if l is not None and h == l)

    delta = max(SHIFTS, key=lambda d: (agree(d), -abs(d)))
    lab = match(ev, nar, delta)
    flags = [i for i, (h, l) in enumerate(zip(hits, lab)) if l is not None and h != l and h not in (None,) and l != "CANVAS" and h != "CANVAS"]
    codes = []
    if s != 1.0 and o == (0, 0):
        codes.append("COORD_SCALE")
    elif o != (0, 0) and s == 1.0:
        codes.append("COORD_OFFSET")
    elif s != 1.0:
        codes.append("COORD_SCALE_OFFSET")
    if abs(delta) >= 1.0:
        codes.append("NARRATION_SHIFT")
    if flags:
        codes.append("LABEL_MISMATCH")
    return {"verdict": "ACCEPT" if not codes else "FIX", "codes": codes, "scale": s, "offset": o, "delta": delta,
            "flags": flags, "targets": hits}


def schema_check(sess):
    """Baseline: timestamps increase and every click is inside the 1920x1080 screen."""
    ev = sess["events"]
    ok = all(a["t"] < b["t"] for a, b in zip(ev, ev[1:])) and all(0 <= e["x"] <= W and 0 <= e["y"] <= H for e in ev)
    return "ACCEPT" if ok else "FIX"
