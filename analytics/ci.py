from __future__ import annotations

from math import sqrt
from statistics import NormalDist


def wilson_ci(hits: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Return (low, high) in [0,1]."""
    if not (0 < alpha < 1):
        raise ValueError('alpha must be in (0,1)')
    if n < 0 or hits < 0 or hits > n:
        raise ValueError('Require 0 <= hits <= n')
    if n == 0:
        return (0.0, 1.0)
    z = NormalDist().inv_cdf(1 - alpha / 2)
    p = hits / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z / denom) * sqrt((p * (1 - p) / n) + (z2 / (4 * n * n)))
    return (max(0.0, center - margin), min(1.0, center + margin))
