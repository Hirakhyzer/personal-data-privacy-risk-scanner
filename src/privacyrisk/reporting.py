"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_report(
    path: str | Path,
    summary: dict,
    risk: pd.DataFrame,
    entities: pd.DataFrame,
    redactions: pd.DataFrame,
    access_audit: pd.DataFrame,
    type_summary: pd.DataFrame,
) -> None:
    """Write an advisor/reviewer-facing privacy-risk report."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    high_docs = risk.head(12) if not risk.empty else risk
    entity_summary = entities.groupby("entity_type", as_index=False).size().rename(columns={"size": "finding_count"}).sort_values("finding_count", ascending=False) if not entities.empty else pd.DataFrame()
    redaction_summary = redactions.groupby("redaction_action", as_index=False).size().rename(columns={"size": "action_count"}).sort_values("action_count", ascending=False) if not redactions.empty else pd.DataFrame()
    access_summary = access_audit.loc[access_audit["suspicious_access_flag"] == 1].head(12) if not access_audit.empty else access_audit
    lines = [
        "# Synthetic Privacy Risk Report",
        "",
        "> This report uses fictional synthetic documents and access logs. It is privacy review support only, not legal compliance certification or release approval.",
        "",
        "## Run summary",
        "",
        _dict_table(summary),
        "",
        "## Highest-risk documents",
        "",
        _table(high_docs[["document_id", "document_type", "access_level", "finding_count", "critical_entity_count", "privacy_risk_score", "privacy_risk_class", "risk_drivers"]] if not high_docs.empty else high_docs),
        "",
        "## Entity findings by type",
        "",
        _table(entity_summary),
        "",
        "## Redaction action summary",
        "",
        _table(redaction_summary),
        "",
        "## Suspicious access examples",
        "",
        _table(access_summary[["access_event_id", "document_id", "actor_role", "owner_role", "action", "access_channel", "access_risk_score", "access_risk_drivers"]] if not access_summary.empty else access_summary),
        "",
        "## Risk by document type",
        "",
        _table(type_summary),
        "",
        "## Recommended governance",
        "",
        "- Treat high and critical documents as requiring human privacy review.",
        "- Verify redaction quality before disclosure, sharing, or retention decisions.",
        "- Investigate role-mismatch, after-hours, bulk-export, and restricted-document access events.",
        "- Do not use synthetic thresholds as legal or regulatory conclusions.",
    ]
    p.write_text("\n".join(lines), encoding="utf-8")


def _dict_table(values: dict) -> str:
    rows = pd.DataFrame([{"metric": key, "value": value} for key, value in values.items()])
    return _table(rows)


def _table(frame: pd.DataFrame) -> str:
    if frame is None or frame.empty:
        return "_No rows generated._"
    return frame.to_markdown(index=False)
