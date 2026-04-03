from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import sqrt
from typing import Any

import pandas as pd

from analytics.filters import FilterClause, apply_filters
from analytics.targets import Target


@dataclass(frozen=True)
class HypothesisCandidate:
    clauses: tuple[FilterClause, ...]

    @property
    def label(self) -> str:
        return ' AND '.join(c.label or f"{c.field} {c.op} {c.value}" for c in self.clauses)


DOMAIN_THRESHOLDS: dict[str, list[float]] = {
    'Opening_Gap_Percent': [-0.5, -0.13, 0.13, 0.5],
    'Range_12_Percent': [0.3, 0.6, 1.0],
    'Range_18_Percent': [0.3, 0.6, 1.0],
}


def _occurrence_series(df: pd.DataFrame, target: Target) -> pd.Series:
    return pd.Series(df.eval(target.occurred_expr, engine='python'), index=df.index).fillna(False).astype(bool)


def _date_mask(df: pd.DataFrame, start: str | None = None, end: str | None = None) -> pd.Series:
    if 'Date' not in df.columns:
        return pd.Series(True, index=df.index)
    dates = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
    mask = pd.Series(True, index=df.index)
    if start:
        mask &= dates >= pd.Timestamp(start)
    if end:
        mask &= dates <= pd.Timestamp(end)
    return mask.fillna(False)


def _is_event_bar(col: str, s: pd.Series) -> bool:
    if col.endswith('_Bar'):
        return True
    vals = pd.to_numeric(s, errors='coerce').dropna()
    if vals.empty:
        return False
    return bool(((vals == 0) | ((vals >= 1) & (vals <= 81))).mean() > 0.95)


def _candidate_clauses_for_field(df: pd.DataFrame, field: str) -> list[FilterClause]:
    s = df[field]
    out: list[FilterClause] = []
    if field.startswith('Prev_') and s.notna().sum() == 0:
        return out

    if _is_event_bar(field, s):
        out.append(FilterClause(field=field, op='>', value=0, label=f'{field} occurred'))
        return out

    num = pd.to_numeric(s, errors='coerce')
    numeric_ratio = float(num.notna().mean()) if len(num) else 0.0
    if numeric_ratio > 0.85:
        vals = num.dropna()
        if vals.empty:
            return out
        unique_small = sorted(pd.unique(vals))
        if len(unique_small) <= 5 and set(unique_small).issubset({-1, 0, 1}):
            for v in unique_small:
                out.append(FilterClause(field=field, op='==', value=int(v), label=f'{field} == {int(v)}'))
            return out

        q_grid = sorted(set(float(vals.quantile(q)) for q in [0.1, 0.25, 0.5, 0.75, 0.9]))
        for q in q_grid:
            out.append(FilterClause(field=field, op='>', value=round(q, 4), label=f'{field} > {q:.4g}'))
            out.append(FilterClause(field=field, op='<=', value=round(q, 4), label=f'{field} <= {q:.4g}'))
        if len(q_grid) >= 2:
            out.append(FilterClause(field=field, op='between', value=(round(q_grid[1], 4), round(q_grid[-2], 4)), label=f'{field} mid-range'))
        for t in DOMAIN_THRESHOLDS.get(field, []):
            out.append(FilterClause(field=field, op='>', value=t, label=f'{field} > {t}'))
            out.append(FilterClause(field=field, op='<=', value=t, label=f'{field} <= {t}'))
        # de-duplicate by (op,value)
        dedup = {}
        for c in out:
            dedup[(c.field, c.op, str(c.value))] = c
        return list(dedup.values())

    vals = s.dropna()
    if vals.empty:
        return out
    counts = vals.astype(str).value_counts()
    for cat in counts.head(5).index.tolist():
        out.append(FilterClause(field=field, op='==', value=cat, label=f'{field} == {cat}'))
    return out


def generate_candidate_clauses(df: pd.DataFrame, allowed_fields: list[str]) -> list[FilterClause]:
    clauses: list[FilterClause] = []
    for field in allowed_fields:
        if field not in df.columns or field == 'Date':
            continue
        clauses.extend(_candidate_clauses_for_field(df, field))
    # stable de-dup across fields
    dedup: dict[tuple[str, str, str], FilterClause] = {}
    for c in clauses:
        dedup[(c.field, c.op, str(c.value))] = c
    return list(dedup.values())


def _eval_combo(df: pd.DataFrame, occ: pd.Series, clauses: tuple[FilterClause, ...], cohort_mask: pd.Series, baseline_mask: pd.Series, min_n: int) -> dict[str, Any] | None:
    combo_mask = apply_filters(df, list(clauses)) & cohort_mask
    n = int(combo_mask.sum())
    if n < min_n:
        return None
    hits = int((combo_mask & occ).sum())
    p = hits / n if n else None
    base_n = int(baseline_mask.sum())
    base_hits = int((baseline_mask & occ).sum())
    p0 = (base_hits / base_n) if base_n else None
    if p is None or p0 is None:
        return None
    lift = p - p0
    reliability = lift * sqrt(n)
    return {
        'clauses': [c.__dict__ for c in clauses],
        'label': ' AND '.join(c.label or f"{c.field} {c.op} {c.value}" for c in clauses),
        'n': n,
        'hits': hits,
        'p': p,
        'p0': p0,
        'lift': lift,
        'reliability': reliability,
    }


def search_hypotheses(
    df: pd.DataFrame,
    target: Target,
    allowed_fields: list[str],
    max_clauses: int = 2,
    min_n: int = 100,
    objective: str = 'max_probability',
    discovery_start: str | None = None,
    discovery_end: str | None = None,
    validation_start: str | None = None,
    validation_end: str | None = None,
    max_candidates_per_fieldset: int = 20000,
) -> pd.DataFrame:
    """Enumerate 1-3 clause hypotheses and score them on discovery (+ optional validation split)."""
    if max_clauses < 1 or max_clauses > 3:
        raise ValueError('max_clauses must be in [1,3]')

    occ = _occurrence_series(df, target)
    disc_mask = _date_mask(df, discovery_start, discovery_end)
    val_mask = _date_mask(df, validation_start, validation_end) if (validation_start or validation_end) else pd.Series(True, index=df.index)
    clauses = generate_candidate_clauses(df, allowed_fields)

    rows: list[dict[str, Any]] = []
    eval_count = 0
    for k in range(1, max_clauses + 1):
        for combo in combinations(clauses, k):
            # avoid combining multiple clauses on same field (usually redundant/conflicting)
            fields = [c.field for c in combo]
            if len(set(fields)) != len(fields):
                continue
            eval_count += 1
            if eval_count > max_candidates_per_fieldset:
                break
            disc = _eval_combo(df, occ, combo, disc_mask, disc_mask, min_n)
            if disc is None:
                continue

            row = {'num_clauses': k, 'target_id': target.id, **disc}

            # Validation split support (persist same lift sign)
            if validation_start or validation_end:
                val = _eval_combo(df, occ, combo, val_mask, val_mask, min_n)
                if val is None:
                    continue
                same_sign = (disc['lift'] == 0 and val['lift'] == 0) or (disc['lift'] > 0 and val['lift'] > 0) or (disc['lift'] < 0 and val['lift'] < 0)
                if not same_sign:
                    continue
                row.update({
                    'validation_n': val['n'],
                    'validation_hits': val['hits'],
                    'validation_p': val['p'],
                    'validation_p0': val['p0'],
                    'validation_lift': val['lift'],
                    'validation_reliability': val['reliability'],
                    'lift_sign_persisted': True,
                })
            else:
                row['lift_sign_persisted'] = None

            # objective-specific score
            if objective == 'min_probability':
                row['score'] = (row['p0'] - row['p']) * sqrt(max(row['n'], 1))
            else:
                row['score'] = row['lift'] * sqrt(max(row['n'], 1))
            rows.append(row)
        if eval_count > max_candidates_per_fieldset:
            break

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    sort_cols = ['score', 'reliability', 'n'] if objective != 'min_probability' else ['score', 'n']
    asc = [False] * len(sort_cols)
    return out.sort_values(sort_cols, ascending=asc, na_position='last').reset_index(drop=True)
