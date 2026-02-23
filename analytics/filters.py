from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
import pandas as pd

Op = Literal['==', '!=', '>', '>=', '<', '<=', 'in', 'between']

@dataclass(frozen=True)
class FilterClause:
    field: str
    op: Op
    value: Any
    label: str | None = None


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce')


def apply_filters(df: pd.DataFrame, clauses: list[FilterClause]) -> pd.Series:
    """Return boolean mask."""
    mask = pd.Series(True, index=df.index)
    for clause in clauses:
        if clause.field not in df.columns:
            raise KeyError(f'Unknown field: {clause.field}')
        s = df[clause.field]
        op = clause.op
        if op == '==':
            cond = s.eq(clause.value) & s.notna()
        elif op == '!=':
            cond = s.ne(clause.value) & s.notna()
        elif op in {'>', '>=', '<', '<='}:
            ns = _numeric(s)
            cond = getattr(ns, {'>':'gt','>=':'ge','<':'lt','<=':'le'}[op])(clause.value).fillna(False)
        elif op == 'in':
            vals = clause.value if isinstance(clause.value, (list, tuple, set)) else [clause.value]
            cond = s.isin(list(vals)) & s.notna()
        elif op == 'between':
            low, high = clause.value
            cond = _numeric(s).between(low, high, inclusive='both').fillna(False)
        else:
            raise ValueError(f'Unsupported op: {op}')
        mask &= cond.astype(bool)
    return mask
