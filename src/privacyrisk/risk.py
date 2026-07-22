"""Document-level privacy risk scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd

ENTITY_WEIGHTS = {
    "email": 0.45,
    "phone": 0.45,
    "person_name": 0.40,
    "address": 0.60,
    "location": 0.25,
    "date_of_birth": 0.85,
    "national_id_like": 1.00,
    "financial_account_like": 1.00,
    "medical_term": 0.90,
    "sensitive_phrase": 0.80,
}

CRITICAL_TYPES = {"national_id_like", "financial_account_like", "date_of_birth", "medical_term"}


def score_document_risk(documents: pd.DataFrame, entities: pd.DataFrame) -> pd.DataFrame:
    """Compute transparent privacy risk score and risk class per document."""
    rows = []
    grouped = {doc_id: group.copy() for doc_id, group in entities.groupby("document_id")} if not entities.empty else {}
    for doc in documents.itertuples(index=False):
        group = grouped.get(doc.document_id, pd.DataFrame(columns=entities.columns if not entities.empty else []))
        counts = group["entity_type"].value_counts().to_dict() if not group.empty else {}
        weighted = sum(float(counts.get(entity_type, 0)) * weight for entity_type, weight in ENTITY_WEIGHTS.items())
        unique_types = len(counts)
        critical_hits = int(sum(counts.get(entity_type, 0) for entity_type in CRITICAL_TYPES))
        restricted_boost = 0.18 if str(doc.access_level) == "restricted" else 0.05
        risk_score = float(np.clip(0.18 * weighted + 0.06 * unique_types + 0.12 * min(critical_hits, 3) + restricted_boost, 0, 1))
        rows.append({
            "document_id": doc.document_id,
            "document_type": doc.document_type,
            "owner_role": doc.owner_role,
            "access_level": doc.access_level,
            "finding_count": int(len(group)),
            "unique_entity_types": int(unique_types),
            "critical_entity_count": int(critical_hits),
            "privacy_risk_score": round(risk_score, 4),
            "privacy_risk_class": _risk_class(risk_score),
            "risk_drivers": _risk_drivers(counts, str(doc.access_level)),
            "requires_human_review": bool(risk_score >= 0.55 or critical_hits > 0),
        })
    return pd.DataFrame(rows).sort_values(["privacy_risk_score", "finding_count"], ascending=[False, False]).reset_index(drop=True)


def summarize_privacy_risk(risk: pd.DataFrame, entities: pd.DataFrame, access_audit: pd.DataFrame) -> dict[str, float | int | str]:
    """Compact summary for JSON, report, and audit logs."""
    return {
        "document_count": int(len(risk)),
        "detected_entity_count": int(len(entities)),
        "high_or_critical_document_count": int(risk["privacy_risk_class"].isin(["high", "critical"]).sum()) if len(risk) else 0,
        "human_review_document_count": int(risk["requires_human_review"].sum()) if len(risk) else 0,
        "mean_privacy_risk_score": float(risk["privacy_risk_score"].mean()) if len(risk) else 0.0,
        "suspicious_access_event_count": int(access_audit["suspicious_access_flag"].sum()) if len(access_audit) else 0,
        "data_origin": "synthetic fictional privacy documents and access logs",
        "decision_boundary": "privacy review support only; not legal compliance certification or release approval",
    }


def risk_by_document_type(risk: pd.DataFrame) -> pd.DataFrame:
    """Aggregate privacy risk by document type."""
    if risk.empty:
        return pd.DataFrame(columns=["document_type", "document_count", "mean_privacy_risk_score", "high_or_critical_count"])
    return risk.groupby("document_type", as_index=False).agg(
        document_count=("document_id", "count"),
        mean_privacy_risk_score=("privacy_risk_score", "mean"),
        high_or_critical_count=("privacy_risk_class", lambda s: int(s.isin(["high", "critical"]).sum())),
    ).sort_values("mean_privacy_risk_score", ascending=False).reset_index(drop=True)


def _risk_class(score: float) -> str:
    if score >= 0.82:
        return "critical"
    if score >= 0.62:
        return "high"
    if score >= 0.32:
        return "medium"
    return "low"


def _risk_drivers(counts: dict, access_level: str) -> str:
    drivers = []
    for entity_type in ["national_id_like", "financial_account_like", "medical_term", "date_of_birth", "sensitive_phrase", "address", "email", "phone"]:
        if counts.get(entity_type, 0) > 0:
            drivers.append(entity_type)
    if access_level == "restricted":
        drivers.append("restricted_document")
    return "|".join(drivers) if drivers else "minimal_detected_personal_data"
