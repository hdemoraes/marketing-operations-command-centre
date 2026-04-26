"""
CRM helpers: load, filter, update, and save lead records.
Supports Google Sheets as a live data source; falls back to local CSV when not configured.
"""

import os
import pandas as pd
from src.config import LEADS_FILE

_INTEREST_SCORE_MAP = {"High": 65, "Medium": 45, "Low": 25}


def _get_sheet_url() -> str | None:
    return os.getenv("STREAMLIT_GOOGLE_SHEET_CSV_URL") or None


def _normalize_sheet_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map Google Sheets form submission columns to the app's expected schema."""
    df = df.copy()

    # 1. Strip whitespace and lowercase all column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 2. Fix known truncations produced by some Google Sheets CSV exports
    _col_fixes = {
        "landing_page_va":  "landing_page_variant",
        "landing_page_var": "landing_page_variant",
        "business_nam":     "business_name",
        "contact_nam":      "contact_name",
        "interest_leve":    "interest_level",
        "company_siz":      "company_size",
        "pain_poin":        "pain_point",
    }
    df = df.rename(columns={k: v for k, v in _col_fixes.items() if k in df.columns})

    # 3. Keep both business_name and company for compatibility
    if "business_name" in df.columns and "company" not in df.columns:
        df["company"] = df["business_name"]
    elif "company" in df.columns and "business_name" not in df.columns:
        df["business_name"] = df["company"]

    # 4. Rename created_at → date_created
    if "created_at" in df.columns and "date_created" not in df.columns:
        df = df.rename(columns={"created_at": "date_created"})

    # 5. Split contact_name into first/last but keep the original column
    if "contact_name" in df.columns:
        names = df["contact_name"].fillna("").str.split(" ", n=1, expand=True)
        df["first_name"] = names[0]
        df["last_name"]  = names[1] if 1 in names.columns else ""

    # 6. Map interest_level → lead_score; keep interest_level for scoring detection
    if "interest_level" in df.columns:
        df["lead_score"] = (
            df["interest_level"].map(_INTEREST_SCORE_MAP).fillna(30).astype(int)
        )

    # 7. Populate notes from company_size but keep company_size column
    if "company_size" in df.columns:
        df["notes"] = df["company_size"].apply(
            lambda v: f"Company size: {v}" if pd.notna(v) and v else ""
        )

    # 8. Add any still-missing columns with safe defaults
    _defaults: dict = {
        "contact_name":        "",
        "company_size":        "",
        "pain_point":          "",
        "interest_level":      "",
        "industry":            "",
        "source":              "",
        "status":              "New",
        "landing_page_variant": "",
        "email":               "",
        "notes":               "",
        "job_title":           "",
        "last_contacted":      pd.NaT,
        "date_created":        pd.NaT,
    }
    for col, default in _defaults.items():
        if col not in df.columns:
            df[col] = default

    df["date_created"]   = pd.to_datetime(df["date_created"],   errors="coerce")
    df["last_contacted"] = pd.to_datetime(df["last_contacted"],  errors="coerce")
    return df


def _clean_sheet_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Remove invalid or test rows from a normalised Google Sheets DataFrame.
    Returns (cleaned_df, n_removed). Does not modify the source sheet.

    Removes rows where:
    - date_created is not a valid date (NaT after parsing)
    - source is a bare variant letter "A" or "B" (value entered in wrong field)
    - landing_page_variant contains a status value such as "New"
    - status looks like a date (date entered in wrong field)
    - company (business_name) is missing or blank
    """
    # Trim whitespace from all string columns first
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    mask = pd.Series(True, index=df.index)

    if "date_created" in df.columns:
        mask &= df["date_created"].notna()

    if "source" in df.columns:
        mask &= ~df["source"].fillna("").str.upper().isin(["A", "B"])

    if "landing_page_variant" in df.columns:
        mask &= ~df["landing_page_variant"].fillna("").str.lower().eq("new")

    if "status" in df.columns:
        mask &= pd.to_datetime(df["status"], errors="coerce").isna()

    if "company" in df.columns:
        mask &= df["company"].fillna("").str.strip().ne("")

    cleaned = df[mask].copy()
    return cleaned, int(len(df) - len(cleaned))


def _load_crm_leads_internal() -> tuple[pd.DataFrame, dict]:
    url = _get_sheet_url()
    if url:
        try:
            raw = pd.read_csv(url)
            normalised = _normalize_sheet_columns(raw)
            cleaned, removed = _clean_sheet_rows(normalised)
            stats = {"total_raw": len(raw), "valid": len(cleaned), "removed": removed}
            return cleaned, stats
        except Exception:
            pass
    df = pd.read_csv(LEADS_FILE, parse_dates=["date_created", "last_contacted"])
    return df, {"total_raw": len(df), "valid": len(df), "removed": 0}


def load_crm_leads() -> pd.DataFrame:
    """Load from Google Sheets if configured, otherwise fall back to local CSV."""
    df, _ = _load_crm_leads_internal()
    return df


def load_crm_leads_with_stats() -> tuple[pd.DataFrame, dict]:
    """Load, clean, and return the DataFrame with a stats dict (total_raw, valid, removed)."""
    return _load_crm_leads_internal()


def get_data_source() -> str:
    """Return a label for the active data source."""
    return "Google Sheets CRM" if _get_sheet_url() else "Sample CSV fallback"


def load_leads() -> pd.DataFrame:
    """Return all leads from the local CSV as a DataFrame."""
    return pd.read_csv(LEADS_FILE, parse_dates=["date_created", "last_contacted"])


def save_leads(df: pd.DataFrame) -> None:
    """Overwrite the leads CSV with the given DataFrame."""
    df.to_csv(LEADS_FILE, index=False)


def filter_leads(
    df: pd.DataFrame,
    status: str | None = None,
    source: str | None = None,
    industry: str | None = None,
    min_score: int = 0,
) -> pd.DataFrame:
    """Return a filtered view of leads. None values skip that filter."""
    mask = df["lead_score"] >= min_score
    if status:
        mask &= df["status"] == status
    if source:
        mask &= df["source"] == source
    if industry:
        mask &= df["industry"] == industry
    return df[mask].copy()


def update_lead_status(df: pd.DataFrame, lead_id: str, new_status: str) -> pd.DataFrame:
    """Update the status of a single lead by ID and return the modified DataFrame."""
    df.loc[df["lead_id"] == lead_id, "status"] = new_status
    return df


def get_lead_by_id(df: pd.DataFrame, lead_id: str) -> pd.Series | None:
    """Return a single lead row, or None if not found."""
    result = df[df["lead_id"] == lead_id]
    return result.iloc[0] if not result.empty else None
