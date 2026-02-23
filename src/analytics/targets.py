from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pandas as pd
import yaml

from analytics.ci import wilson_ci
from analytics.timing import event_bar_series, histogram_counts

@dataclass(frozen=True)
class Target:
    id: str
    label: str
    occurred_expr: str
    event_bar_col: str | None = None
    group: str | None = None


def load_targets_from_yaml(path: str) -> list[Target]:
    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    out = []
    for item in raw.get('targets', []):
        out.append(Target(
            id=item['id'],
            label=item['label'],
            occurred_expr=item.get('occurred_rule') or item.get('occurred_expr'),
            event_bar_col=item.get('event_bar_col'),
            group=item.get('group'),
        ))
    return out


def _eval_occured(df: pd.DataFrame, expr: str) -> pd.Series:
    s = df.eval(expr, engine='python')
    return pd.Series(s, index=df.index).fillna(False).astype(bool)


def compute_target_stats(df: pd.DataFrame, mask: pd.Series, target: Target, baseline_mask: pd.Series | None = None) -> dict[str, Any]:
    """Returns dict with n, hits, p, p0, lift, CI, median_bar/IQR/peak if event_bar_col exists."""
    m = mask.reindex(df.index).fillna(False).astype(bool)
    b = baseline_mask.reindex(df.index).fillna(False).astype(bool) if baseline_mask is not None else pd.Series(True, index=df.index)
    occ = _eval_occured(df, target.occurred_expr)
    n = int(m.sum())
    hits = int((m & occ).sum())
    p = (hits / n) if n else None
    n0 = int(b.sum())
    hits0 = int((b & occ).sum())
    p0 = (hits0 / n0) if n0 else None
    lift = (p / p0) if (p is not None and p0 not in (None, 0)) else None
    ci_low, ci_high = wilson_ci(hits, n) if n else (0.0, 1.0)
    median_bar = iqr_bar = peak_bar = None
    if target.event_bar_col and target.event_bar_col in df.columns and n:
        bars = event_bar_series(df, m, target.event_bar_col)
        if not bars.empty:
            median_bar = float(bars.median())
            iqr_bar = float(bars.quantile(0.75) - bars.quantile(0.25))
            hist = histogram_counts(bars)
            if not hist.empty:
                idx = hist['count'].idxmax()
                peak_bar = int(hist.loc[idx, 'bar'])
    return {
        'target_id': target.id, 'label': target.label, 'group': target.group, 'occurred_expr': target.occurred_expr,
        'event_bar_col': target.event_bar_col, 'n': n, 'hits': hits, 'p': p, 'baseline_n': n0, 'baseline_hits': hits0,
        'p0': p0, 'lift': lift, 'ci_low': ci_low, 'ci_high': ci_high, 'reliability': ci_high - ci_low,
        'median_bar': median_bar, 'iqr_bar': iqr_bar, 'peak_bar': peak_bar,
    }
