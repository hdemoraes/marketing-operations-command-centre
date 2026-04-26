"""
Lead scoring: derives priority tier, recommended action, and estimated pipeline
value from each lead's score, status, and industry.

Two scoring paths:

  CSV sample data — lead_score is read directly from the file. Priority is
  assigned using the original thresholds (Hot >= 70).

  Google Sheets live leads — identified by the presence of an interest_level
  column. lead_score is recomputed from multiple form fields using the
  multi-factor model below. Priority uses stricter thresholds (Hot >= 80)
  calibrated to the new score scale.
"""

import pandas as pd

# Annual contract value baseline per industry (AU$)
INDUSTRY_BASE_VALUE = {
    "SaaS": 2800,
    "Financial Services": 4500,
    "Healthcare": 3200,
    "E-commerce": 2200,
    "Consulting": 3500,
    "Real Estate": 3800,
    "Education": 1800,
    "Retail": 1600,
    "Manufacturing": 2900,
    "Legal Tech": 4100,
}

# ── Priority thresholds ───────────────────────────────────────────────────────

# CSV sample data: scores are pre-set in the file (typical range 20–95)
_CSV_HOT  = 70
_CSV_WARM = 45
_CSV_COLD = 25

# Live form leads: multi-factor scores use a tighter 0–100 scale
_LIVE_HOT  = 80
_LIVE_WARM = 55
_LIVE_COLD = 25


# ── Priority functions ────────────────────────────────────────────────────────

def get_priority(score: int) -> str:
    """Priority tier for CSV sample leads (original thresholds)."""
    if score >= _CSV_HOT:
        return "Hot"
    if score >= _CSV_WARM:
        return "Warm"
    if score >= _CSV_COLD:
        return "Cold"
    return "Needs Review"


def _get_live_priority(score: int) -> str:
    """Priority tier for Google Sheets live leads (stricter thresholds)."""
    if score >= _LIVE_HOT:
        return "Hot"
    if score >= _LIVE_WARM:
        return "Warm"
    if score >= _LIVE_COLD:
        return "Cold"
    return "Needs Review"


# ── Multi-factor scoring for live form leads ──────────────────────────────────

def _score_from_fields(row: pd.Series) -> int:
    """
    Compute a lead score from Google Sheets form submission fields.

    Breakdown:
      Interest level (readiness to act)    +5 to +45
      Company size                         +0 to +25
      Pain point detail (length proxy)     +0 to +20
      Valid email present                  +5
      Business name present                +5
      Maximum (capped)                     100
    """
    score = 0

    # --- Interest level / readiness ---
    # Form sends "High" / "Medium" / "Low"; "Ready to move now" covers manual entry
    interest = str(row.get("interest_level", "") or "").strip().lower()
    if interest == "ready to move now":
        score += 45
    elif interest == "high":
        score += 40
    elif interest == "medium":
        score += 25
    elif interest == "low":
        score += 10
    else:
        score += 5  # unknown / blank = minimal credit

    # --- Company size ---
    # Normalisation stores company_size as "Company size: X" inside notes
    notes = str(row.get("notes", "") or "")
    if "200+" in notes:
        score += 25
    elif "51" in notes:   # covers "51–200"
        score += 20
    elif "11" in notes:   # covers "11–50"
        score += 12
    elif "1–10" in notes or "1-10" in notes:
        score += 5
    # else: unknown / not provided = +0

    # --- Pain point detail ---
    # Longer, specific pain points signal higher engagement
    pain = str(row.get("pain_point", "") or "").strip()
    if len(pain) >= 20:
        score += 20
    elif len(pain) >= 8:
        score += 10

    # --- Data completeness ---
    email = str(row.get("email", "") or "").strip()
    if "@" in email and "." in email.split("@")[-1]:
        score += 5

    if str(row.get("company", "") or "").strip():
        score += 5

    return min(score, 100)


# ── Recommended action ────────────────────────────────────────────────────────

def get_recommended_action(row: pd.Series) -> str:
    """
    Return a specific next step based on lead status and priority tier.
    Uses priority (not raw score) so it works correctly for both CSV and
    live leads, which use different scoring thresholds.
    """
    status   = row["status"]
    priority = row.get("priority", "")

    if priority == "Needs Review":
        return "Review and complete lead details"
    if status == "Closed Won":
        return "Explore upsell or referral opportunity"
    if status == "Closed Lost":
        return "Add to 90-day re-engagement sequence"
    if status == "Proposal Sent":
        return "Chase for decision — follow up within 3 days"
    if status == "Qualified" and priority == "Hot":
        return "Fast-track to proposal this week"
    if status == "Qualified":
        return "Book discovery call to progress"
    if status == "Contacted" and priority == "Hot":
        return "Send proposal — high engagement signal"
    if status == "Contacted":
        return "Follow up within 48 hours"
    if status == "Nurturing":
        return "Enrol in automated email sequence"
    if status == "New" and priority == "Hot":
        return "Fast-track to proposal or discovery call"
    if status == "New" and priority == "Warm":
        return "Send intro email within 24 hours"
    if status == "New" and priority == "Cold":
        return "Add to nurture sequence"
    if status == "New":
        return "Send intro email within 24 hours"
    return "Review and update lead status"


# ── Estimated pipeline value ──────────────────────────────────────────────────

def _calc_estimated_value(row: pd.Series) -> int:
    """
    Derive a deterministic pipeline value from industry + lead_id.
    Varies ±20% around the industry baseline so values look realistic.
    Handles any lead_id format by extracting digits only.
    """
    base   = INDUSTRY_BASE_VALUE.get(row["industry"], 2500)
    digits = "".join(filter(str.isdigit, str(row["lead_id"])))
    variance = (int(digits) % 5) * 0.08 if digits else 0
    return int(base * (0.84 + variance))


# ── Enrichment entry point ────────────────────────────────────────────────────

def enrich_leads(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add estimated_value, lead_score (live leads only), priority, and
    recommended_action. Returns an enriched copy — does not modify the source.

    Source detection: presence of interest_level column indicates Google Sheets
    live data; its absence means CSV sample data.
    """
    df = df.copy()

    is_live = "interest_level" in df.columns

    if is_live:
        # Recompute score from multiple form fields
        df["lead_score"] = df.apply(_score_from_fields, axis=1)
        df["priority"]   = df["lead_score"].apply(_get_live_priority)

        # Override to Needs Review if core contact data is missing
        incomplete = (
            df["email"].fillna("").str.strip().eq("") |
            df["company"].fillna("").str.strip().eq("")
        )
        df.loc[incomplete, "priority"] = "Needs Review"
    else:
        # CSV leads: score is already in the file — assign priority only
        df["priority"] = df["lead_score"].apply(get_priority)

    df["estimated_value"]    = df.apply(_calc_estimated_value, axis=1)
    df["recommended_action"] = df.apply(get_recommended_action, axis=1)
    return df


# ── Event-based score recalculation (optional utility) ───────────────────────

def compute_scores(leads: pd.DataFrame) -> pd.DataFrame:
    """Recalculate lead_score for CSV leads from campaign_events.csv."""
    from src.config import EVENTS_FILE, SCORE_WEIGHTS

    events = pd.read_csv(EVENTS_FILE, parse_dates=["event_date"])
    event_counts = (
        events.groupby(["lead_id", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    leads = leads.copy()
    for _, row in leads.iterrows():
        lead_id = row["lead_id"]
        score   = 0
        match   = event_counts[event_counts["lead_id"] == lead_id]
        if not match.empty:
            r      = match.iloc[0]
            score += r.get("email_open",   0) * SCORE_WEIGHTS["email_open"]
            score += r.get("email_click",  0) * SCORE_WEIGHTS["email_click"]
            score += r.get("form_submit",  0) * SCORE_WEIGHTS["form_submit"]
            score += r.get("page_view",    0) * SCORE_WEIGHTS["page_view"]
        if row["source"] == "Referral":
            score += SCORE_WEIGHTS["referral_source_bonus"]
        elif row["source"] == "LinkedIn":
            score += SCORE_WEIGHTS["linkedin_source_bonus"]
        leads.loc[leads["lead_id"] == lead_id, "lead_score"] = min(score, 100)

    return leads
