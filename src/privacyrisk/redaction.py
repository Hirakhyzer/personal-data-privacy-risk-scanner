"""Redaction planning and masked document previews."""

from __future__ import annotations

import pandas as pd

ACTION_BY_TYPE = {
    "email": "mask_email",
    "phone": "mask_phone",
    "person_name": "mask_name",
    "address": "generalize_address",
    "location": "generalize_location",
    "date_of_birth": "redact_date_of_birth",
    "national_id_like": "redact_identifier",
    "financial_account_like": "redact_financial_account",
    "medical_term": "redact_medical_term",
    "sensitive_phrase": "remove_sensitive_phrase",
}


def build_redaction_plan(documents: pd.DataFrame, entities: pd.DataFrame, risk: pd.DataFrame) -> pd.DataFrame:
    """Create entity-level redaction recommendations with document risk context."""
    if entities.empty:
        return pd.DataFrame(columns=["document_id", "entity_type", "entity_value", "redaction_action", "replacement_text", "requires_human_review", "privacy_risk_class"])
    risk_cols = risk[["document_id", "privacy_risk_class", "requires_human_review"]]
    out = entities.merge(risk_cols, on="document_id", how="left").copy()
    out["redaction_action"] = out["entity_type"].map(ACTION_BY_TYPE).fillna("review_and_minimize")
    out["replacement_text"] = out.apply(lambda row: _replacement(str(row.entity_type), str(row.entity_value)), axis=1)
    out["redaction_priority"] = out.apply(lambda row: _priority(str(row.privacy_risk_class), str(row.entity_type)), axis=1)
    return out[[
        "document_id", "document_type", "entity_type", "entity_value", "start_char", "end_char", "redaction_action",
        "replacement_text", "redaction_priority", "requires_human_review", "privacy_risk_class", "rule_name",
    ]].sort_values(["document_id", "start_char"]).reset_index(drop=True)


def redaction_action_summary(plan: pd.DataFrame) -> pd.DataFrame:
    """Summarize redaction actions."""
    if plan.empty:
        return pd.DataFrame(columns=["redaction_action", "action_count"])
    return plan.groupby("redaction_action", as_index=False).agg(action_count=("entity_value", "count")).sort_values("action_count", ascending=False).reset_index(drop=True)


def masked_preview(text: str, document_entities: pd.DataFrame) -> str:
    """Return a simple masked preview by applying spans from end to start."""
    if document_entities.empty:
        return text
    out = str(text)
    ordered = document_entities.sort_values("start_char", ascending=False)
    for row in ordered.itertuples(index=False):
        replacement = _replacement(str(row.entity_type), str(row.entity_value))
        out = out[: int(row.start_char)] + replacement + out[int(row.end_char):]
    return out


def _replacement(entity_type: str, value: str) -> str:
    if entity_type == "email":
        return "[EMAIL_MASKED]"
    if entity_type == "phone":
        return "[PHONE_MASKED]"
    if entity_type == "person_name":
        return "[NAME_MASKED]"
    if entity_type in {"address", "location"}:
        return "[GENERALIZED_LOCATION]"
    if entity_type == "date_of_birth":
        return "[DOB_REDACTED]"
    if entity_type == "national_id_like":
        return "[IDENTIFIER_REDACTED]"
    if entity_type == "financial_account_like":
        return "[FINANCIAL_ACCOUNT_REDACTED]"
    if entity_type == "medical_term":
        return "[MEDICAL_INFO_REDACTED]"
    if entity_type == "sensitive_phrase":
        return "[SENSITIVE_PHRASE_REDACTED]"
    return "[REVIEW_REDACTION]"


def _priority(risk_class: str, entity_type: str) -> str:
    if risk_class in {"critical", "high"} or entity_type in {"national_id_like", "financial_account_like", "medical_term", "date_of_birth"}:
        return "high"
    if entity_type in {"address", "sensitive_phrase", "email", "phone"}:
        return "medium"
    return "low"
