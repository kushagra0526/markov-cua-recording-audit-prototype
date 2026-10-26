import json
from collections import Counter

from . import check, gen

WANT = {"clean": [], "scale": ["COORD_SCALE"], "offset": ["COORD_OFFSET"], "scale_offset": ["COORD_SCALE_OFFSET"],
        "narr_shift": ["NARRATION_SHIFT"], "swap": ["LABEL_MISMATCH"]}


def score(seeds, held):
    t, per = Counter(), {}
    for s in seeds:
        sess = gen.make_session(s, held)
        a, b = check.audit(sess), check.schema_check(sess)
        k = sess["plant"]["kind"]
        p = per.setdefault(k, Counter())
        p["n"] += 1
        p["stopped_mine"] += a["verdict"] != "ACCEPT"
        p["stopped_schema"] += b != "ACCEPT"
        p["named"] += sorted(a["codes"]) == sorted(WANT[k])
        p["unfitted"] += a["codes"] == ["COORD_UNFITTED"]
        if a["targets"] is not None:
            right = sum(1 for x, y in zip(a["targets"], sess["truth"]) if x == y)
            p["clicks_right"] += right
        p["clicks"] += len(sess["truth"])
        t["clicks_total"] += len(sess["truth"])
        t["clicks_right_as_recorded"] += sum(1 for e, y in zip(sess["events"], sess["truth"]) if gen.hit(sess["boxes"], e["x"], e["y"]) == y)
        t["clicks_right_repaired"] += right if a["targets"] is not None else 0
    return {"by_kind": {k: dict(v) for k, v in per.items()}, "totals": dict(t)}


def main():
    out = {"dev": score(range(0, 300), False), "held_out": score(range(1000, 1400), True)}
    json.dump(out, open("out/result.json", "w"), indent=1)
    for k, v in out.items():
        print(k, v["totals"])
        for kind, c in sorted(v["by_kind"].items()):
            print("   ", kind, c)


if __name__ == "__main__":
    main()
