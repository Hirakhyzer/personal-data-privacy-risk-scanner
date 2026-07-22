"""Access-log privacy audit checks."""

from __future__ import annotations

from datetime import datetime
import pandas as pd


def audit_access_events(access_log: pd.DataFrame, documents: pd.DataFrame, risk: pd.DataFrame) -> pd.DataFrame:
    """Flag access events that deserve privacy review."""
    if access_log.empty:
        return pd.DataFrame(columns=["access_event_id", "document_id", "suspicious_access_flag", "access_risk_score", "access_risk_drivers"])
    doc_info = documents[["document_id", "owner_role", "access_level", "document_type"]].merge(
        risk[["document_id", "privacy_risk_class", "privacy_risk_score"]], on="document_id", how="left"
    )
    out = access_log.merge(doc_info, on="document_id", how="left")
    flags = []
    scores = []
    drivers = []
    for row in out.itertuples(index=False):
        row_drivers = []
        score = 0.0
        if str(row.actor_role) != str(row.owner_role):
            row_drivers.append("role_mismatch")
            score += 0.28
        if str(row.access_level) == "restricted":
            row_drivers.append("restricted_document")
            score += 0.18
        if str(row.privacy_risk_class) in {"high", "critical"}:
            row_drivers.append("high_risk_document")
            score += 0.22
        if _after_hours(str(row.timestamp)):
            row_drivers.append("after_hours_access")
            score += 0.18
        if str(row.access_channel) == "bulk_export":
            row_drivers.append("bulk_export_channel")
            score += 0.18
        if str(row.action) == "download":
            row_drivers.append("download_action")
            score += 0.08
        scores.append(round(min(score, 1.0), 4))
        flags.append(int(score >= 0.48))
        drivers.append("|".join(row_drivers) if row_drivers else "routine_access")
    out["access_risk_score"] = scores
    out["suspicious_access_flag"] = flags
    out["access_risk_drivers"] = drivers
    return out.sort_values(["suspicious_access_flag", "access_risk_score"], ascending=[False, False]).reset_index(drop=True)


def access_summary(access_audit: pd.DataFrame) -> pd.DataFrame:
    """Summarize suspicious access by actor role."""
    if access_audit.empty:
        return pd.DataFrame(columns=["actor_role", "access_events", "suspicious_events", "mean_access_risk_score"])
    return access_audit.groupby("actor_role", as_index=False).agg(
        access_events=("access_event_id", "count"),
        suspicious_events=("suspicious_access_flag", "sum"),
        mean_access_risk_score=("access_risk_score", "mean"),
    ).sort_values(["suspicious_events", "mean_access_risk_score"], ascending=[False, False]).reset_index(drop=True)


def _after_hours(timestamp: str) -> bool:
    try:
        hour = datetime.fromisoformat(timestamp).hour
    except ValueError:
        return False
    return hour < 6 or hour >= 20
