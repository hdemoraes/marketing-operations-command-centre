"""
Shared utility functions: formatting, validation, and display helpers.
"""

import pandas as pd
from datetime import datetime


def format_currency(value: float, symbol: str = "AU$") -> str:
    return f"{symbol}{value:,.2f}"


def format_pct(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}%"


def days_since(date_value) -> int | None:
    """Return days since a date. Returns None if date is NaT/None."""
    if pd.isna(date_value):
        return None
    delta = datetime.utcnow() - pd.to_datetime(date_value)
    return delta.days


def score_colour(score: int) -> str:
    """Return a hex colour for use in Streamlit metric displays."""
    if score >= 75:
        return "#e74c3c"   # red / hot
    if score >= 50:
        return "#e67e22"   # orange / warm
    if score >= 25:
        return "#3498db"   # blue / cool
    return "#95a5a6"       # grey / cold


def validate_leads_schema(df: pd.DataFrame) -> list[str]:
    """Return a list of missing required columns, empty if schema is valid."""
    required = [
        "lead_id", "first_name", "last_name", "email", "company",
        "industry", "job_title", "source", "landing_page_variant",
        "status", "lead_score", "date_created", "pain_point",
    ]
    return [col for col in required if col not in df.columns]


def truncate(text: str, max_len: int = 60) -> str:
    """Truncate a string for display in narrow table columns."""
    return text if len(text) <= max_len else text[:max_len - 1] + "…"
