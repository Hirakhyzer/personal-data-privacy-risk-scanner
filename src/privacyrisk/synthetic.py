"""Deterministic synthetic documents and access logs.

All documents, people, identifiers, and access events are fictional. The module is
for privacy-risk pipeline validation without exposing real private data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

DOCUMENT_TYPES = ["support_ticket", "hr_note", "medical_intake", "finance_form", "student_record", "legal_memo", "product_feedback"]
OWNER_ROLES = ["support", "human_resources", "clinical_review", "finance", "student_services", "legal", "product"]
NAMES = ["Maya Chen", "Omar Khalid", "Lina Roberts", "Diego Silva", "Aisha Khan", "Noah Patel", "Sara Williams", "Hana Lee"]
CITIES = ["Lakeside", "Riverton", "Northbridge", "Hillford", "Oak Harbor", "Meadow City"]
MEDICAL_TERMS = ["asthma", "diabetes", "migraine", "hypertension", "allergy", "anxiety"]
SENSITIVE_PHRASES = ["immigration status", "disciplinary action", "salary dispute", "mental health concern", "financial hardship"]


@dataclass(frozen=True)
class SyntheticPrivacyConfig:
    documents: int = 70
    seed: int = 42

    def __post_init__(self) -> None:
        if self.documents < 20:
            raise ValueError("Use at least 20 documents for privacy-risk analysis.")


def generate_synthetic_privacy_data(config: SyntheticPrivacyConfig | None = None) -> dict[str, pd.DataFrame]:
    """Generate fictional documents and access logs."""
    cfg = config or SyntheticPrivacyConfig()
    rng = np.random.default_rng(cfg.seed)
    documents = _documents(cfg, rng)
    access_log = _access_log(documents, cfg, rng)
    return {"documents": documents, "access_log": access_log}


def _documents(cfg: SyntheticPrivacyConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.documents):
        doc_type = DOCUMENT_TYPES[idx % len(DOCUMENT_TYPES)]
        role = OWNER_ROLES[idx % len(OWNER_ROLES)]
        name = NAMES[idx % len(NAMES)]
        city = CITIES[(idx * 2) % len(CITIES)]
        email = f"synthetic.person{idx+1:03d}@example.org"
        phone = f"+1-555-{1000 + idx:04d}"
        national_id = f"SYN-{idx+10:03d}-{rng.integers(1000, 9999)}"
        account = f"ACCT-{rng.integers(10000000, 99999999)}"
        dob = f"19{70 + idx % 25:02d}-{(idx % 12) + 1:02d}-{(idx % 27) + 1:02d}"
        medical = MEDICAL_TERMS[idx % len(MEDICAL_TERMS)]
        sensitive = SENSITIVE_PHRASES[idx % len(SENSITIVE_PHRASES)]
        street = f"{100 + idx} Privacy Lane, {city}"
        base = f"Document for {name}. Contact email: {email}. Phone: {phone}. City: {city}."
        if doc_type == "support_ticket":
            text = base + f" Customer says account {account} is locked after address update at {street}."
        elif doc_type == "hr_note":
            text = base + f" HR note mentions {sensitive} and national identifier {national_id}."
        elif doc_type == "medical_intake":
            text = base + f" Intake lists date of birth {dob}, condition {medical}, and address {street}."
        elif doc_type == "finance_form":
            text = base + f" Finance review includes account number {account} and payment dispute notes."
        elif doc_type == "student_record":
            text = base + f" Student record includes DOB {dob}, guardian phone {phone}, and {sensitive}."
        elif doc_type == "legal_memo":
            text = base + f" Legal memo references ID {national_id}, home address {street}, and confidential settlement notes."
        else:
            text = base + f" Product feedback includes location {city} and request to remove personal profile data."
        # Add controlled low-risk docs so the scanner has contrast.
        if idx % 11 == 0:
            text = f"Synthetic policy summary DOC-{idx+1:04d}: aggregated usage trends for {city} without direct identifiers."
        access_level = "restricted" if doc_type in {"medical_intake", "finance_form", "hr_note", "legal_memo"} else "internal"
        rows.append({
            "document_id": f"DOC-{idx+1:04d}",
            "document_type": doc_type,
            "owner_role": role,
            "access_level": access_level,
            "text": text,
            "ground_truth_risk_hint": "critical" if doc_type in {"medical_intake", "finance_form"} else "high" if doc_type in {"hr_note", "legal_memo"} else "medium",
        })
    return pd.DataFrame(rows)


def _access_log(documents: pd.DataFrame, cfg: SyntheticPrivacyConfig, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    start = datetime(2026, 1, 5, 8, 0, 0)
    roles = OWNER_ROLES + ["contractor", "analytics", "external_auditor"]
    for idx in range(max(cfg.documents * 2, 40)):
        doc = documents.iloc[idx % len(documents)]
        actor_role = str(doc.owner_role) if rng.random() > 0.28 else roles[int(rng.integers(0, len(roles)))]
        hour_offset = int(rng.integers(0, 24 * 14))
        timestamp = start + timedelta(hours=hour_offset)
        # Inject some after-hours and role-mismatch cases.
        if idx % 17 == 0:
            timestamp = timestamp.replace(hour=2)
            actor_role = "contractor"
        rows.append({
            "access_event_id": f"ACC-{idx+1:05d}",
            "timestamp": timestamp.isoformat(),
            "document_id": doc.document_id,
            "actor_id": f"USER-{(idx % 18) + 1:03d}",
            "actor_role": actor_role,
            "action": "view" if rng.random() > 0.20 else "download",
            "access_channel": "internal_portal" if rng.random() > 0.15 else "bulk_export",
        })
    return pd.DataFrame(rows)
