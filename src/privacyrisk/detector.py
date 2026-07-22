"""Transparent sensitive data detection rules."""

from __future__ import annotations

import re
import pandas as pd

PATTERNS: dict[str, list[tuple[str, str, float]]] = {
    "email": [("email_regex", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", 0.98)],
    "phone": [("phone_regex", r"\b(?:\+?1[-.\s]?)?555[-.\s]?\d{4}\b", 0.93)],
    "national_id_like": [("synthetic_id_regex", r"\bSYN-\d{3}-\d{4}\b", 0.95)],
    "financial_account_like": [("account_regex", r"\bACCT-\d{8}\b", 0.94)],
    "date_of_birth": [("dob_context_regex", r"\b(?:date of birth|DOB)\s+\d{4}-\d{2}-\d{2}\b", 0.92)],
    "address": [("address_regex", r"\b\d{2,5}\s+[A-Z][A-Za-z]+\s+(?:Lane|Street|Road|Avenue|Drive),\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?\b", 0.86)],
    "location": [("city_context_regex", r"\b(?:City|location|at|for)\s*:?\s*(Lakeside|Riverton|Northbridge|Hillford|Oak Harbor|Meadow City)\b", 0.62)],
}

NAME_PATTERN = re.compile(r"\b(?:Document for|record for|profile for)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b")
MEDICAL_TERMS = {"asthma", "diabetes", "migraine", "hypertension", "allergy", "anxiety"}
SENSITIVE_PHRASES = {"immigration status", "disciplinary action", "salary dispute", "mental health concern", "financial hardship", "confidential settlement"}


def detect_sensitive_entities(documents: pd.DataFrame) -> pd.DataFrame:
    """Detect sensitive entities in a document table.

    Returns one row per finding with evidence location and rule provenance.
    """
    rows: list[dict] = []
    for doc in documents.itertuples(index=False):
        text = str(doc.text)
        for entity_type, patterns in PATTERNS.items():
            for rule_name, pattern, confidence in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    rows.append(_finding(doc, entity_type, match.group(0), match.start(), match.end(), confidence, rule_name))
        for match in NAME_PATTERN.finditer(text):
            rows.append(_finding(doc, "person_name", match.group(1), match.start(1), match.end(1), 0.84, "contextual_name_pattern"))
        lowered = text.lower()
        for term in MEDICAL_TERMS:
            pos = lowered.find(term)
            if pos >= 0:
                rows.append(_finding(doc, "medical_term", text[pos:pos + len(term)], pos, pos + len(term), 0.78, "medical_dictionary"))
        for phrase in SENSITIVE_PHRASES:
            pos = lowered.find(phrase)
            if pos >= 0:
                rows.append(_finding(doc, "sensitive_phrase", text[pos:pos + len(phrase)], pos, pos + len(phrase), 0.80, "sensitive_phrase_dictionary"))
    columns = ["document_id", "document_type", "entity_type", "entity_value", "start_char", "end_char", "confidence", "rule_name", "recommended_handling"]
    return pd.DataFrame(rows, columns=columns).sort_values(["document_id", "start_char"]).reset_index(drop=True) if rows else pd.DataFrame(columns=columns)


def entity_type_summary(entities: pd.DataFrame) -> pd.DataFrame:
    """Summarize detected entity volume by type."""
    if entities.empty:
        return pd.DataFrame(columns=["entity_type", "finding_count", "mean_confidence"])
    return entities.groupby("entity_type", as_index=False).agg(
        finding_count=("entity_value", "count"),
        mean_confidence=("confidence", "mean"),
    ).sort_values("finding_count", ascending=False).reset_index(drop=True)


def _finding(doc, entity_type: str, value: str, start: int, end: int, confidence: float, rule_name: str) -> dict:
    return {
        "document_id": doc.document_id,
        "document_type": doc.document_type,
        "entity_type": entity_type,
        "entity_value": value,
        "start_char": int(start),
        "end_char": int(end),
        "confidence": round(float(confidence), 3),
        "rule_name": rule_name,
        "recommended_handling": _handling(entity_type),
    }


def _handling(entity_type: str) -> str:
    if entity_type in {"national_id_like", "financial_account_like", "date_of_birth", "medical_term", "sensitive_phrase"}:
        return "redact_and_human_privacy_review"
    if entity_type in {"email", "phone", "person_name"}:
        return "mask_identifier"
    if entity_type in {"address", "location"}:
        return "generalize_location"
    return "review"
