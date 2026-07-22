# Synthetic lab

The synthetic lab creates fictional documents such as support tickets, HR notes, medical-intake examples, finance forms, student records, legal memos, and product feedback.

The generated data intentionally includes controlled sensitive patterns so the scanner can demonstrate detection, scoring, redaction, and access-review behavior without using real private data.

Run:

```bash
python scripts/run_synthetic_privacy_lab.py --documents 70 --seed 42
```

Outputs are written under `outputs/` and are ignored by Git except for `.gitkeep`.
