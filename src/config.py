"""
Configuration: loads environment variables and defines shared path constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / os.getenv("DATA_DIR", "data")
OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")

# Files
LEADS_FILE = DATA_DIR / "crm_leads.csv"
EVENTS_FILE = DATA_DIR / "campaign_events.csv"
CAMPAIGNS_FILE = DATA_DIR / "sample_campaigns.csv"
FOLLOWUPS_FILE = OUTPUT_DIR / "generated_followups.csv"
SUMMARY_FILE = OUTPUT_DIR / "campaign_summary.csv"

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Lead scoring weights (used in lead_scoring.py)
SCORE_WEIGHTS = {
    "email_open": 5,
    "email_click": 10,
    "form_submit": 20,
    "page_view": 2,
    "referral_source_bonus": 15,
    "linkedin_source_bonus": 10,
}

# Statuses considered active (not lost/closed)
ACTIVE_STATUSES = ["New", "Contacted", "Qualified", "Proposal Sent", "Nurturing"]
