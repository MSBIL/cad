from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_latest_update(path: str | Path, last_trade_date: str, data_file: str | Path | None = None) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'last_trade_date': last_trade_date,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_version_hash': _sha256(Path(data_file)) if data_file and Path(data_file).exists() else None,
    }
    p.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return p


def read_latest_update(path: str | Path) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
