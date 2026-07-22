from privacyrisk.access import audit_access_events
from privacyrisk.detector import detect_sensitive_entities
from privacyrisk.redaction import build_redaction_plan
from privacyrisk.risk import score_document_risk
from privacyrisk.synthetic import SyntheticPrivacyConfig, generate_synthetic_privacy_data


def _sample():
    return generate_synthetic_privacy_data(SyntheticPrivacyConfig(documents=28, seed=8))


def test_detector_finds_expected_entity_types():
    data = _sample()
    entities = detect_sensitive_entities(data["documents"])
    assert not entities.empty
    found = set(entities["entity_type"].unique())
    assert {"email", "phone", "person_name"}.issubset(found)
    assert len(found & {"national_id_like", "financial_account_like", "medical_term", "date_of_birth"}) >= 2


def test_risk_redaction_and_access_audit_have_expected_flags():
    data = _sample()
    entities = detect_sensitive_entities(data["documents"])
    risk = score_document_risk(data["documents"], entities)
    plan = build_redaction_plan(data["documents"], entities, risk)
    access = audit_access_events(data["access_log"], data["documents"], risk)
    assert not risk.empty
    assert risk["privacy_risk_score"].between(0, 1).all()
    assert risk["requires_human_review"].sum() > 0
    assert not plan.empty
    assert {"mask_email", "mask_phone"}.intersection(set(plan["redaction_action"]))
    assert access["suspicious_access_flag"].sum() > 0
