"""
Assignment 11 — Audit Log (forensic record of every interaction).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


def default_audit_log_path() -> str:
    """Always resolve to <repo>/outputs/… (safe when cwd is src/)."""
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / "outputs" / "audit_log.json")


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, float] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """Store input + start timestamp keyed by request_id/user_id."""
        rid = request_id or f"{user_id}-{len(self.logs)}"
        self._open[rid] = time.time()
        self.logs.append(
            {
                "request_id": rid,
                "user_id": user_id,
                "direction": "input",
                "text": text[:500],
                "blocked": False,
                "layer": None,
                "latency_ms": None,
                "at": utc_now_iso(),
            }
        )
        return rid

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ):
        """Store output, layer decision, latency; append to self.logs."""
        start = self._open.pop(request_id, None) if request_id else None
        latency_ms = round((time.time() - start) * 1000, 2) if start else None
        self.logs.append(
            {
                "request_id": request_id,
                "user_id": user_id,
                "direction": "output",
                "text": text[:500],
                "blocked": blocked,
                "layer": layer,
                "latency_ms": latency_ms,
                "at": utc_now_iso(),
            }
        )

    def export_json(self, filepath: str | None = None):
        """Write logs to disk (JSON array) under repo-root ``outputs/`` by default."""
        path = Path(filepath or default_audit_log_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(path)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
