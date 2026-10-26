"""Synthetic computer-use sessions: UI element boxes, clicks, narration, with known recording defects."""
import random

W, H = 1920, 1080
LABELS = ["Save", "Open", "Undo", "Redo", "Extrude", "Sketch", "Cancel", "Export", "Fillet", "Chamfer", "Mirror", "Pattern",
          "Measure", "Section", "Render", "Layers", "Offset", "Trim", "Extend", "Rotate", "Scale", "Copy", "Paste", "Delete"]
CANVAS = (300, 200, 1700, 1000)


def make_layout(rng):
    labels = rng.sample(LABELS, rng.randint(14, 24))
    boxes = {}
    for i, lab in enumerate(labels):
        row, col = divmod(i, 12)
        x = 20 + col * 120 + rng.randint(0, 6)
        y = 50 + row * 50 + rng.randint(0, 6)
        boxes[lab] = (x, y, x + 96, y + 34)
    return boxes


def hit(boxes, x, y):
    for lab, (x0, y0, x1, y1) in boxes.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return lab
    x0, y0, x1, y1 = CANVAS
    return "CANVAS" if x0 <= x <= x1 and y0 <= y <= y1 else None


def make_session(seed, held_out=False):
    rng = random.Random(seed)
    boxes = make_layout(rng)
    kinds = ["clean", "scale", "offset", "scale_offset", "narr_shift", "swap"]
    kind = rng.choice(kinds + ["clean"])
    s, o, delta = 1.0, (0, 0), 0.0
    if kind in ("scale", "scale_offset"):
        s = rng.choice([0.5, 1.25, 1.5, 2.0] + ([1.4, 0.8] if held_out else []))
    if kind in ("offset", "scale_offset"):
        o = rng.choice([(1920, 0), (-1920, 0), (0, 1080)] + ([(-1366, 0), (2560, 0)] if held_out else []))
    if kind == "narr_shift":
        delta = rng.choice([-3.0, -2.0, 1.5, 2.5, 3.5]) if True else 0
    t, ev, narr, truth = 0.0, [], [], []
    names = list(boxes)
    for _ in range(rng.randint(40, 80)):
        t += rng.uniform(2.5, 6.0)
        lab = "CANVAS" if rng.random() < 0.2 else rng.choice(names)
        if lab == "CANVAS":
            x0, y0, x1, y1 = CANVAS
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        else:
            x0, y0, x1, y1 = boxes[lab]
            x, y = rng.uniform(x0 + 3, x1 - 3), rng.uniform(y0 + 3, y1 - 3)
        ev.append({"t": round(t, 2), "x": round(x * s + o[0], 1), "y": round(y * s + o[1], 1)})
        truth.append(lab)
        narr.append({"t": round(t - rng.uniform(0.2, 1.0) + delta, 2), "label": lab})
    swap_idx = None
    if kind == "swap":
        swap_idx = rng.choice([i for i, l in enumerate(truth) if l != "CANVAS"])
        narr[swap_idx]["label"] = rng.choice([n for n in names if n != truth[swap_idx]])
    return {"boxes": boxes, "events": ev, "narration": narr, "truth": truth,
            "plant": {"kind": kind, "scale": s, "offset": o, "delta": delta, "swap_idx": swap_idx}}
