"""Hash-chained audit ledger for reproducible privacy review events."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def append_record(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Append one hash-chained JSONL audit record."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = _last_hash(p)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_hash": previous_hash,
        "payload": payload,
    }
    record["record_hash"] = _hash_payload(record)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
    return record


def verify_log(path: str | Path) -> dict[str, int | bool | str]:
    """Verify hash chain integrity."""
    p = Path(path)
    if not p.exists():
        return {"valid": True, "records": 0, "last_hash": "GENESIS"}
    previous = "GENESIS"
    count = 0
    last_hash = previous
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        expected = record.get("record_hash")
        actual_payload = {k: v for k, v in record.items() if k != "record_hash"}
        actual = _hash_payload(actual_payload)
        if record.get("previous_hash") != previous or actual != expected:
            return {"valid": False, "records": count, "last_hash": last_hash}
        previous = str(expected)
        last_hash = str(expected)
        count += 1
    return {"valid": True, "records": count, "last_hash": last_hash}


def _last_hash(path: Path) -> str:
    if not path.exists():
        return "GENESIS"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return "GENESIS"
    return str(json.loads(lines[-1])["record_hash"])


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
