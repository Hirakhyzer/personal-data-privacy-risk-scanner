# Methodology

The lab implements a transparent synthetic privacy-risk pipeline:

1. Generate fictional documents and access logs.
2. Detect sensitive entities with regex and dictionary rules.
3. Score document risk using weighted entity types and access-level context.
4. Recommend redaction actions by entity type and risk class.
5. Audit access events for role mismatch, after-hours access, bulk export, restricted documents, and high-risk documents.
6. Write local reports, figures, JSON summaries, and hash-chained audit records.

The detectors are deliberately interpretable baselines. They are designed for research validation and educational review, not legal certification.
