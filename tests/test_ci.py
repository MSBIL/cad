from analytics.ci import wilson_ci


def test_wilson_ci_edges():
    lo, hi = wilson_ci(0, 10)
    assert 0 <= lo <= hi <= 1
    lo2, hi2 = wilson_ci(10, 10)
    assert 0 <= lo2 <= hi2 <= 1
    assert hi < hi2


def test_wilson_monotonic_midpoint():
    mids = []
    for h in range(11):
        lo, hi = wilson_ci(h, 10)
        mids.append((lo + hi) / 2)
    assert mids == sorted(mids)
