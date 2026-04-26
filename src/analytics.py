"""
Analytics helpers: aggregation functions for the dashboard.
All inputs should be enriched DataFrames (post enrich_leads()).
All functions return a Series or DataFrame ready for st.bar_chart / st.line_chart.
"""

import pandas as pd
from src.config import CAMPAIGNS_FILE, EVENTS_FILE


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_campaigns() -> pd.DataFrame:
    return pd.read_csv(CAMPAIGNS_FILE, parse_dates=["start_date", "end_date"])


def load_events() -> pd.DataFrame:
    return pd.read_csv(EVENTS_FILE, parse_dates=["event_date"])


# ── Top-line metrics ──────────────────────────────────────────────────────────

def total_pipeline_value(df: pd.DataFrame) -> int:
    """Sum estimated_value for all leads that are not Closed Lost."""
    if "estimated_value" not in df.columns or df.empty:
        return 0
    return int(df[df["status"] != "Closed Lost"]["estimated_value"].fillna(0).sum())


def conversion_rate(df: pd.DataFrame) -> float:
    """Percentage of total leads that reached Closed Won."""
    if len(df) == 0:
        return 0.0
    return round(len(df[df["status"] == "Closed Won"]) / len(df) * 100, 1)


def hot_lead_count(df: pd.DataFrame) -> int:
    if "priority" not in df.columns or df.empty:
        return 0
    return int((df["priority"] == "Hot").sum())


def qualified_lead_count(df: pd.DataFrame) -> int:
    """Leads qualified by status (Qualified / Closed Won) or by lead score >= 70."""
    if df.empty:
        return 0
    by_status = df["status"].isin(["Qualified", "Closed Won"])
    by_score  = df["lead_score"] >= 70
    return int((by_status | by_score).sum())


# ── Chart data ────────────────────────────────────────────────────────────────

def leads_by_source(df: pd.DataFrame) -> pd.Series:
    """Lead count per source channel, sorted descending."""
    return (
        df.groupby("source")["lead_id"]
        .count()
        .sort_values(ascending=False)
        .rename("Leads")
    )


def pipeline_by_status(df: pd.DataFrame) -> pd.Series:
    """Total estimated pipeline value per status (excludes Closed Lost)."""
    return (
        df[df["status"] != "Closed Lost"]
        .groupby("status")["estimated_value"]
        .sum()
        .sort_values(ascending=False)
        .rename("Pipeline (AU$)")
    )


def score_distribution(df: pd.DataFrame) -> pd.Series:
    """Bucket lead_score into five ranges — used as a histogram."""
    bins = [0, 20, 40, 60, 80, 101]
    labels = ["0–20", "21–40", "41–60", "61–80", "81–100"]
    tmp = df.copy()
    tmp["band"] = pd.cut(tmp["lead_score"], bins=bins, labels=labels, right=False)
    return tmp.groupby("band", observed=True)["lead_id"].count().rename("Leads")


def leads_by_industry(df: pd.DataFrame) -> pd.Series:
    return (
        df.groupby("industry")["lead_id"]
        .count()
        .sort_values(ascending=False)
        .rename("Leads")
    )


def priority_breakdown(df: pd.DataFrame) -> pd.Series:
    order = ["Hot", "Warm", "Cold", "Needs Review"]
    counts = df.groupby("priority")["lead_id"].count().rename("Leads")
    return counts.reindex([p for p in order if p in counts.index])


def monthly_lead_volume(df: pd.DataFrame) -> pd.Series:
    """Lead count per calendar month, sorted chronologically."""
    tmp = df.copy()
    tmp["month"] = pd.to_datetime(tmp["date_created"]).dt.to_period("M").astype(str)
    return tmp.groupby("month")["lead_id"].count().rename("Leads").sort_index()


# ── A/B comparison ────────────────────────────────────────────────────────────

def ab_variant_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per landing page variant (A, B) with:
    Leads, Avg Score, Hot Leads, Closed Won, Pipeline Value, Conversion Rate.
    """
    g = df.groupby("landing_page_variant")

    leads_count = g["lead_id"].count()
    avg_score = g["lead_score"].mean().round(1)
    hot = g["priority"].apply(lambda x: (x == "Hot").sum())
    won = g["status"].apply(lambda x: (x == "Closed Won").sum())

    active = df[df["status"] != "Closed Lost"]
    pipeline = active.groupby("landing_page_variant")["estimated_value"].sum()

    result = pd.DataFrame({
        "Leads": leads_count,
        "Avg Score": avg_score,
        "Hot Leads": hot,
        "Closed Won": won,
        "Pipeline Value (AU$)": pipeline,
    }).reset_index()

    result["Conversion Rate (%)"] = (
        result["Closed Won"] / result["Leads"] * 100
    ).round(1)

    return result


# ── Campaign-level (used in Phase 3+) ────────────────────────────────────────

def campaign_performance(campaigns: pd.DataFrame) -> pd.DataFrame:
    df = campaigns.copy()
    df["cost_per_lead_gbp"] = df["cost_per_lead_gbp"].fillna(0)
    return df.sort_values("cost_per_lead_gbp")
