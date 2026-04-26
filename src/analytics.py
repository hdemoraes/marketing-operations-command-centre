"""
Analytics helpers: aggregation functions for the dashboard.
All inputs should be enriched DataFrames (post enrich_leads()).
All functions return a Series or DataFrame ready for st.bar_chart / st.line_chart.
All functions are defensively guarded — they never raise on missing columns or empty data.
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
    if df.empty or "estimated_value" not in df.columns or "status" not in df.columns:
        return 0
    return int(df[df["status"] != "Closed Lost"]["estimated_value"].fillna(0).sum())


def conversion_rate(df: pd.DataFrame) -> float:
    """Percentage of total leads that reached Closed Won."""
    if df.empty or "status" not in df.columns:
        return 0.0
    return round(len(df[df["status"] == "Closed Won"]) / len(df) * 100, 1)


def hot_lead_count(df: pd.DataFrame) -> int:
    if df.empty or "priority" not in df.columns:
        return 0
    return int((df["priority"] == "Hot").sum())


def qualified_lead_count(df: pd.DataFrame) -> int:
    """Leads qualified by status (Qualified / Closed Won) or by lead score >= 70."""
    if df.empty:
        return 0
    result = pd.Series(False, index=df.index)
    if "status" in df.columns:
        result |= df["status"].isin(["Qualified", "Closed Won"])
    if "lead_score" in df.columns:
        result |= df["lead_score"] >= 70
    return int(result.sum())


# ── Chart data ────────────────────────────────────────────────────────────────

def leads_by_source(df: pd.DataFrame) -> pd.Series:
    """Lead count per source channel, sorted descending."""
    if df.empty or "source" not in df.columns:
        return pd.Series([], name="Leads", dtype=int)
    count_col = "lead_id" if "lead_id" in df.columns else df.columns[0]
    try:
        return (
            df.groupby("source")[count_col]
            .count()
            .sort_values(ascending=False)
            .rename("Leads")
        )
    except Exception:
        return pd.Series([], name="Leads", dtype=int)


def pipeline_by_status(df: pd.DataFrame) -> pd.Series:
    """Total estimated pipeline value per status (excludes Closed Lost)."""
    if df.empty or "status" not in df.columns or "estimated_value" not in df.columns:
        return pd.Series([], name="Pipeline (AU$)", dtype=float)
    try:
        return (
            df[df["status"] != "Closed Lost"]
            .groupby("status")["estimated_value"]
            .sum()
            .sort_values(ascending=False)
            .rename("Pipeline (AU$)")
        )
    except Exception:
        return pd.Series([], name="Pipeline (AU$)", dtype=float)


def score_distribution(df: pd.DataFrame) -> pd.Series:
    """Bucket lead_score into five ranges — used as a histogram."""
    labels = ["0–20", "21–40", "41–60", "61–80", "81–100"]
    empty = pd.Series(0, index=labels, name="Leads")
    if df.empty or "lead_score" not in df.columns:
        return empty
    try:
        bins = [0, 20, 40, 60, 80, 101]
        tmp = df.copy()
        tmp["band"] = pd.cut(tmp["lead_score"], bins=bins, labels=labels, right=False)
        count_col = "lead_id" if "lead_id" in df.columns else tmp.columns[0]
        return tmp.groupby("band", observed=True)[count_col].count().rename("Leads")
    except Exception:
        return empty


def leads_by_industry(df: pd.DataFrame) -> pd.Series:
    """Lead count per industry, sorted descending."""
    if df.empty or "industry" not in df.columns:
        return pd.Series([], name="Leads", dtype=int)
    count_col = "lead_id" if "lead_id" in df.columns else df.columns[0]
    try:
        return (
            df.groupby("industry")[count_col]
            .count()
            .sort_values(ascending=False)
            .rename("Leads")
        )
    except Exception:
        return pd.Series([], name="Leads", dtype=int)


def priority_breakdown(df: pd.DataFrame) -> pd.Series:
    """Lead count per priority tier in display order."""
    order = ["Hot", "Warm", "Cold", "Needs Review"]
    if df.empty or "priority" not in df.columns:
        return pd.Series([], name="Leads", dtype=int)
    count_col = "lead_id" if "lead_id" in df.columns else df.columns[0]
    try:
        counts = df.groupby("priority")[count_col].count().rename("Leads")
        return counts.reindex([p for p in order if p in counts.index])
    except Exception:
        return pd.Series([], name="Leads", dtype=int)


def monthly_lead_volume(df: pd.DataFrame) -> pd.Series:
    """Lead count per calendar month, sorted chronologically."""
    if df.empty or "date_created" not in df.columns:
        return pd.Series([], name="Leads", dtype=int)
    count_col = "lead_id" if "lead_id" in df.columns else df.columns[0]
    try:
        tmp = df.copy()
        tmp["month"] = pd.to_datetime(tmp["date_created"], errors="coerce").dt.to_period("M").astype(str)
        tmp = tmp[tmp["month"].notna() & (tmp["month"] != "NaT")]
        if tmp.empty:
            return pd.Series([], name="Leads", dtype=int)
        return tmp.groupby("month")[count_col].count().rename("Leads").sort_index()
    except Exception:
        return pd.Series([], name="Leads", dtype=int)


# ── A/B comparison ────────────────────────────────────────────────────────────

_AB_COLUMNS = [
    "landing_page_variant", "Leads", "Avg Score",
    "Hot Leads", "Closed Won", "Pipeline Value (AU$)", "Conversion Rate (%)",
]

def ab_variant_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per landing page variant (A, B) with:
    Leads, Avg Score, Hot Leads, Closed Won, Pipeline Value, Conversion Rate.
    Returns an empty DataFrame with the expected columns on any failure.
    """
    required = {"landing_page_variant", "lead_id", "lead_score", "priority", "status", "estimated_value"}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame(columns=_AB_COLUMNS)
    try:
        g = df.groupby("landing_page_variant")

        leads_count = g["lead_id"].count()
        avg_score   = g["lead_score"].mean().round(1)
        hot         = g["priority"].apply(lambda x: (x == "Hot").sum())
        won         = g["status"].apply(lambda x: (x == "Closed Won").sum())

        active   = df[df["status"] != "Closed Lost"]
        pipeline = active.groupby("landing_page_variant")["estimated_value"].sum()

        result = pd.DataFrame({
            "Leads":               leads_count,
            "Avg Score":           avg_score,
            "Hot Leads":           hot,
            "Closed Won":          won,
            "Pipeline Value (AU$)": pipeline,
        }).reset_index()

        result["Conversion Rate (%)"] = (
            result["Closed Won"] / result["Leads"] * 100
        ).round(1)

        return result
    except Exception:
        return pd.DataFrame(columns=_AB_COLUMNS)


# ── Campaign-level (used in Phase 3+) ────────────────────────────────────────

def campaign_performance(campaigns: pd.DataFrame) -> pd.DataFrame:
    df = campaigns.copy()
    df["cost_per_lead_gbp"] = df["cost_per_lead_gbp"].fillna(0)
    return df.sort_values("cost_per_lead_gbp")
