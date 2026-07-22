"""Run the complete synthetic personal data privacy risk scanner lab.

The command uses only fictional documents, people, identifiers, and access logs.
It demonstrates sensitive data detection, privacy-risk scoring, redaction planning,
access audit checks, reporting, figures, and a hash-chained audit ledger without
real private data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from privacyrisk.access import access_summary, audit_access_events
from privacyrisk.audit import append_record, verify_log
from privacyrisk.config import ensure_output_dirs, set_seed
from privacyrisk.detector import detect_sensitive_entities, entity_type_summary
from privacyrisk.redaction import build_redaction_plan, redaction_action_summary
from privacyrisk.reporting import write_report
from privacyrisk.risk import risk_by_document_type, score_document_risk, summarize_privacy_risk
from privacyrisk.synthetic import SyntheticPrivacyConfig, generate_synthetic_privacy_data
from privacyrisk.visualization import (
    plot_access_risk,
    plot_document_risk_distribution,
    plot_entity_type_counts,
    plot_redaction_actions,
    plot_risk_by_document_type,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic personal data privacy risk scanner lab.")
    parser.add_argument("--documents", type=int, default=70)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    set_seed(args.seed)
    outputs = ensure_output_dirs(args.output_dir)
    data = generate_synthetic_privacy_data(SyntheticPrivacyConfig(documents=args.documents, seed=args.seed))
    documents = data["documents"]
    access_log = data["access_log"]

    entities = detect_sensitive_entities(documents)
    entity_summary = entity_type_summary(entities)
    risk = score_document_risk(documents, entities)
    redactions = build_redaction_plan(documents, entities, risk)
    redaction_summary = redaction_action_summary(redactions)
    access_audit = audit_access_events(access_log, documents, risk)
    access_stats = access_summary(access_audit)
    type_summary = risk_by_document_type(risk)

    summary = summarize_privacy_risk(risk, entities, access_audit)
    summary.update({
        "seed": args.seed,
        "redaction_action_count": int(len(redactions)),
        "access_event_count": int(len(access_log)),
        "entity_type_count": int(entities["entity_type"].nunique()) if not entities.empty else 0,
    })

    documents.to_csv(outputs["results"] / "synthetic_documents.csv", index=False)
    entities.to_csv(outputs["results"] / "synthetic_detected_entities.csv", index=False)
    entity_summary.to_csv(outputs["results"] / "synthetic_entity_type_summary.csv", index=False)
    risk.to_csv(outputs["results"] / "synthetic_document_risk.csv", index=False)
    redactions.to_csv(outputs["results"] / "synthetic_redaction_plan.csv", index=False)
    redaction_summary.to_csv(outputs["results"] / "synthetic_redaction_action_summary.csv", index=False)
    access_log.to_csv(outputs["results"] / "synthetic_access_log.csv", index=False)
    access_audit.to_csv(outputs["results"] / "synthetic_access_audit.csv", index=False)
    access_stats.to_csv(outputs["results"] / "synthetic_access_summary.csv", index=False)
    type_summary.to_csv(outputs["results"] / "synthetic_risk_by_document_type.csv", index=False)

    audit_path = outputs["audit"] / "privacy_risk_audit_log.jsonl"
    append_record(audit_path, {**summary, "boundary": "synthetic privacy review support only"})
    summary["audit_log"] = verify_log(audit_path)
    (outputs["results"] / "synthetic_privacy_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    write_report(outputs["reports"] / "synthetic_privacy_risk_report.md", summary, risk, entities, redactions, access_audit, type_summary)
    plot_entity_type_counts(entities, outputs["figures"] / "synthetic_entity_type_counts.png")
    plot_document_risk_distribution(risk, outputs["figures"] / "synthetic_document_risk_distribution.png")
    plot_redaction_actions(redactions, outputs["figures"] / "synthetic_redaction_actions.png")
    plot_access_risk(access_audit, outputs["figures"] / "synthetic_access_risk.png")
    plot_risk_by_document_type(type_summary, outputs["figures"] / "synthetic_risk_by_document_type.png")

    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
