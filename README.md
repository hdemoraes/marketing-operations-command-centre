# Marketing Operations Command Centre

An internal marketing operations dashboard for lead management, campaign analytics, A/B testing, and follow-up recommendations. Built with Python and Streamlit. Connects to a live Google Sheets CRM via landing page forms, with a local CSV fallback for offline use.

---

## Overview

The dashboard centralises the core marketing operations workflow in one place:

- Ingest leads from landing page forms via Google Sheets, or load from local CSV
- Score and segment leads into Hot / Warm / Cold priority tiers automatically
- View pipeline value, conversion rates, and lead volume across channels
- Compare landing page variant performance on lead quality, not just click volume
- Generate personalised follow-up recommendations and next best actions per lead

---

## Features

| Feature | Description |
|---------|-------------|
| **Lead scoring** | Rule-based scoring assigns a priority tier (Hot / Warm / Cold) based on score thresholds |
| **CRM view** | Filterable lead table with status, source, score, priority, and recommended next action |
| **Pipeline analytics** | Lead volume by source, pipeline value by status, score distribution, monthly trends |
| **A/B test comparison** | Side-by-side variant comparison on conversion rate, avg score, hot leads, and pipeline value |
| **Follow-up recommendations** | Per-lead message draft, subject line, next best action, and outreach angle |
| **Batch recommendations** | One-click generation for all Hot leads; output saved to CSV |
| **Google Sheets CRM** | Live lead ingestion from landing page form submissions via Google Apps Script |
| **CSV fallback** | Works offline with local sample data when no live CRM is configured |

---

## Architecture

```
landing_pages/
  variant_a.html          ─── HTML form → POST → Google Apps Script
  variant_b.html          ─── HTML form → POST → Google Apps Script
                                            │
                                   Google Sheet (CRM)
                                            │ CSV export URL
app.py                    ─── load_crm_leads() → enrich_leads() → dashboard
  │
  ├── src/crm.py          ─── load_crm_leads(), normalize columns, CSV fallback
  ├── src/lead_scoring.py ─── priority tiers, estimated value, recommended action
  ├── src/analytics.py    ─── aggregation functions for all chart data
  ├── src/ai_copy_generator.py ─── follow-up recommendation engine
  └── src/utils.py        ─── format_currency, shared helpers
```

**Data flow for live CRM:**
Form submission → Google Apps Script `doPost()` → appends row to Sheet → Streamlit reads CSV export URL → normalises columns → enriches with scoring → renders in dashboard.

**Data flow for CSV fallback:**
`data/crm_leads.csv` → enriches with scoring → renders in dashboard.

---

## Setup

### Prerequisites

- Python 3.11+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:

```
# Required only for follow-up recommendations via Claude API (optional)
ANTHROPIC_API_KEY=your_key_here

# Required for live Google Sheets CRM
STREAMLIT_GOOGLE_SHEET_CSV_URL=https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=0
```

Leave `STREAMLIT_GOOGLE_SHEET_CSV_URL` blank to use the local CSV fallback.

---

## Running Locally

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Works immediately with sample data — no database or live CRM required.

---

## Connecting Google Sheets CRM

Full setup instructions including the complete Google Apps Script code are in:

```
docs/google_sheets_crm_setup.md
```

Quick summary:
1. Create a Google Sheet with the required column headers
2. Add the `doPost()` Apps Script and deploy as a web app
3. The web app URL is already wired into both landing pages
4. Get the sheet's CSV export URL and add it to `.env` as `STREAMLIT_GOOGLE_SHEET_CSV_URL`
5. Restart the app — the sidebar will confirm the live data source

### Column schema

The Google Sheet must have these headers:

```
lead_id | business_name | contact_name | email | industry | company_size |
pain_point | interest_level | source | landing_page_variant | status | created_at
```

The app normalises these automatically on load:
- `business_name` → `company`
- `contact_name` → `first_name` + `last_name`
- `interest_level` → `lead_score` (High=65, Medium=45, Low=25)
- `created_at` → `date_created`

---

## Folder Structure

```
marketing-ai-automation-centre/
│
├── app.py                         # Streamlit entry point
├── requirements.txt
├── .env.example
│
├── data/
│   ├── crm_leads.csv              # Local CSV fallback (52 sample leads)
│   ├── campaign_events.csv        # Touchpoint events per lead
│   └── sample_campaigns.csv       # Campaign-level performance data
│
├── src/
│   ├── config.py                  # Env vars and path constants
│   ├── lead_scoring.py            # Scoring logic and lead enrichment
│   ├── ai_copy_generator.py       # Follow-up recommendation engine
│   ├── crm.py                     # CRM load, normalise, fallback, CRUD
│   ├── analytics.py               # Aggregation helpers for charts
│   └── utils.py                   # format_currency and shared utilities
│
├── landing_pages/
│   ├── variant_a.html             # Landing page — Variant A
│   └── variant_b.html             # Landing page — Variant B
│
├── output/
│   └── generated_followups.csv   # Batch recommendation output
│
└── docs/
    ├── google_sheets_crm_setup.md # Full CRM integration guide
    └── demo_script.md             # Walkthrough guide for demos
```

---

## Deployment Notes

The app is designed for internal use and can be deployed to Streamlit Community Cloud with minimal configuration.

1. Push the repository to GitHub
2. Connect the repo at [share.streamlit.io](https://share.streamlit.io)
3. Set `STREAMLIT_GOOGLE_SHEET_CSV_URL` (and optionally `ANTHROPIC_API_KEY`) as Streamlit secrets
4. The app will load live CRM data on every page refresh

For team access control, enable Streamlit's built-in viewer authentication in the deployment settings.

---

## Future Improvements

| Feature | Approach |
|---------|----------|
| Live CRM sync | HubSpot API or Pipedrive API integration |
| Automated follow-up sequences | Zapier / Make.com / n8n webhook triggers on status change |
| Real A/B conversion tracking | GA4 API or landing page pixel events |
| Lead status updates from dashboard | Write-back to Google Sheets via Apps Script |
| Multi-team authentication | Streamlit Cloud viewer auth or internal SSO |
# marketing-operations-command-centre
