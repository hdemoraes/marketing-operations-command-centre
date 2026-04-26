# Demo Walkthrough

This guide covers how to walk through the full Marketing Operations Command Centre workflow end to end — from landing page submission to dashboard insight.

---

## Prerequisites

- App running: `streamlit run app.py`
- Google Sheets CRM connected (or local CSV fallback active)
- Both landing pages accessible in a browser

---

## 1. Landing Page Submission

**Purpose:** Show how leads enter the system.

1. Open `landing_pages/variant_a.html` in a browser
2. Fill in the form:
   - Name: any test name
   - Work email: any email
   - Company: any company name
   - Industry: select one (e.g. SaaS)
   - Company size: select one
   - Interest level: **Ready to move now** (this maps to High → score 65 → Hot)
   - Pain point: optional free text
3. Click **Book Demo**
4. The browser redirects to the Google Apps Script confirmation page

**What happens in the background:**
- Apps Script `doPost()` appends a new row to the Google Sheet
- Row gets a generated lead ID (`F` + timestamp), status = "New", created_at = now

Repeat with `landing_pages/variant_b.html` to generate a Variant B lead.

---

## 2. Google Sheets CRM

**Purpose:** Show where the raw lead data lives.

1. Open the Google Sheet
2. Confirm the new rows from the form submissions appear
3. Note the columns: `lead_id`, `business_name`, `contact_name`, `email`, `industry`, `interest_level`, `source`, `landing_page_variant`, `status`, `created_at`

The sheet is the source of truth. The dashboard reads from it on every load (with a short Streamlit cache window).

---

## 3. Streamlit Dashboard

### Overview tab

1. Open the dashboard at `http://localhost:8501`
2. Click the refresh icon or press R to clear the cache and load new data
3. Point out the five top-line metrics: Total Leads, Qualified, Hot Leads, Conversion Rate, Pipeline Value
4. Show the **Leads by Source** chart — demonstrates multi-channel attribution
5. Show the **Pipeline Value by Status** chart — demonstrates value-based prioritisation

### CRM tab

1. Click the **CRM** tab
2. Use the Status filter to show only "New" leads — the submissions from step 1 should appear
3. Point out the Score column (progress bar) and Priority column
4. Point out the **Next Best Action** column — each lead has a specific recommended step based on its status and score
5. Sort by Estimated Value to show high-value leads at the top

### Analytics tab

1. Click the **Analytics** tab
2. Show the **Lead Score Distribution** — demonstrates the scoring spread across the database
3. Show the **Monthly Lead Volume** — shows pipeline growth over time
4. Show **Leads by Industry** and **Priority Breakdown**

### A/B Testing tab

1. Click the **A/B Testing** tab
2. Walk through the side-by-side variant comparison:
   - Variant A: dark hero, fear-based CTA ("Stop Losing Leads to Manual Follow-Up")
   - Variant B: light two-column, aspirational CTA ("Your Leads Deserve Better Than a Spreadsheet")
3. Point to Conversion Rate, Avg Lead Score, and Pipeline Value per variant
4. The system automatically identifies the winning variant based on conversion rate (with avg score as a tiebreaker)

### Follow-Up Recommendations tab

1. Click the **Follow-Up Recommendations** tab
2. Select a Hot lead from the dropdown (sorted by score, highest first)
3. Review the lead summary: score, priority, source, status, pain point, industry
4. Click **Generate Recommendation**
5. Walk through the four outputs:
   - **Suggested Subject Line** — personalised to the lead's company and pain category
   - **Next Best Action** — specific step for the sales or marketing team
   - **Outreach Angle** — strategic framing of the approach
   - **Recommended Message** — 4–6 line email body, copy-paste ready
6. Point out that the message references the lead's specific pain point and industry — not a generic template
7. Scroll to **Batch Recommendations** and click the generate button to produce recommendations for all Hot leads

---

## 4. Key Points to Highlight

| What to show | What it demonstrates |
|---|---|
| Form → Sheet → Dashboard in real time | End-to-end lead capture without a CRM subscription |
| Score and priority assigned automatically | No manual triage — the tool decides who to contact first |
| Next Best Action per lead | Consistent follow-up process across the team |
| A/B variant winner identified automatically | Data-driven creative decisions without a separate analytics tool |
| Batch recommendations with one click | Follow-up at scale without writing individual emails |
| CSV export of all recommendations | Output integrates with any email tool or CRM |

---

## 5. Sidebar — Data Source

The sidebar always shows whether the dashboard is reading from the live Google Sheet or the local CSV fallback:

- **🟢 Google Sheets CRM** — live data; form submissions appear after a cache refresh
- **📁 Sample CSV fallback** — offline mode; useful for demos without a live connection
