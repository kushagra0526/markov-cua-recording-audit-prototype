from cuaqa import check, gen


def sess(kind=None, seeds=range(200)):
    return [gen.make_session(s) for s in seeds if kind is None or gen.make_session(s)["plant"]["kind"] == kind]


def test_clean_sessions_accepted():
    for s in sess("clean", range(60)):
        assert check.audit(s)["verdict"] == "ACCEPT"


def test_scale_and_offset_are_named_and_repaired():
    for kind, code in (("scale", "COORD_SCALE"), ("offset", "COORD_OFFSET")):
        for s in sess(kind, range(60)):
            a = check.audit(s)
            assert a["codes"] == [code]
            assert a["targets"] == s["truth"]


def test_narration_shift_found():
    for s in sess("narr_shift", range(60)):
        a = check.audit(s)
        assert abs(a["delta"] - s["plant"]["delta"]) <= 0.5


def test_swap_flags_the_swapped_line():
    for s in sess("swap", range(60)):
        assert check.audit(s)["flags"] == [s["plant"]["swap_idx"]]
