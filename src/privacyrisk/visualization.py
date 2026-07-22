"""Local matplotlib figures for privacy-risk review."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _save(path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(p, dpi=160)
    plt.close()


def plot_entity_type_counts(entities: pd.DataFrame, path: str | Path) -> None:
    counts = entities["entity_type"].value_counts().head(10) if not entities.empty else pd.Series(dtype=int)
    plt.figure(figsize=(9, 5))
    counts.sort_values().plot(kind="barh")
    plt.title("Detected sensitive entity counts")
    plt.xlabel("Findings")
    _save(path)


def plot_document_risk_distribution(risk: pd.DataFrame, path: str | Path) -> None:
    plt.figure(figsize=(8, 5))
    if not risk.empty:
        risk["privacy_risk_score"].plot(kind="hist", bins=12)
    plt.title("Document privacy-risk score distribution")
    plt.xlabel("Privacy risk score")
    _save(path)


def plot_redaction_actions(plan: pd.DataFrame, path: str | Path) -> None:
    counts = plan["redaction_action"].value_counts().head(10) if not plan.empty else pd.Series(dtype=int)
    plt.figure(figsize=(9, 5))
    counts.sort_values().plot(kind="barh")
    plt.title("Recommended redaction actions")
    plt.xlabel("Action count")
    _save(path)


def plot_access_risk(access_audit: pd.DataFrame, path: str | Path) -> None:
    plt.figure(figsize=(9, 5))
    if not access_audit.empty:
        summary = access_audit.groupby("actor_role")["suspicious_access_flag"].sum().sort_values()
        summary.plot(kind="barh")
    plt.title("Suspicious access events by actor role")
    plt.xlabel("Flagged events")
    _save(path)


def plot_risk_by_document_type(type_summary: pd.DataFrame, path: str | Path) -> None:
    plt.figure(figsize=(9, 5))
    if not type_summary.empty:
        type_summary.sort_values("mean_privacy_risk_score").plot(x="document_type", y="mean_privacy_risk_score", kind="barh", legend=False)
    plt.title("Mean privacy risk by document type")
    plt.xlabel("Mean privacy risk score")
    _save(path)
