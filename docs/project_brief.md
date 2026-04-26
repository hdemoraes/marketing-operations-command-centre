# Project Brief: Marketing AI Automation Centre

## Overview

An internal marketing automation tool built as a portfolio project to demonstrate practical skills in AI-assisted development, marketing technology, and lightweight web tooling.

**Target role:** Marketing AI & Automations Specialist  
**Build approach:** Claude Code-assisted development, documented iteratively  
**Deployment target:** Local / Streamlit Cloud  

---

## Problem Statement

Marketing teams at SMBs and growing businesses commonly face:

1. **Lead leakage** — Leads captured through campaigns are not followed up promptly or consistently.
2. **Manual reporting** — Campaign performance data lives in separate platforms; weekly/monthly reports take hours to compile.
3. **No lead scoring** — Sales receives unqualified leads; there is no mechanism to prioritise outreach.
4. **Expensive CRMs** — HubSpot, Salesforce etc. are overkill and cost-prohibitive for small teams.
5. **No A/B testing process** — Landing page copy and CTAs are never systematically tested.
6. **AI underutilisation** — Teams know AI can help with copy and analysis but have no tooling in place.

---

## Solution

A Streamlit-based internal tool that gives a single marketing manager or small team:

- A lightweight CRM view of all leads with filtering and scoring
- AI-generated follow-up email drafts (via Claude API)
- Campaign performance analytics with channel attribution
- A/B test comparison for landing page variants
- Automated score recalculation based on engagement events
- CSV-based storage (no database server required)

---

## Success Criteria

| Criteria | Target |
|---------|--------|
| Works on first run with sample data | Yes |
| AI follow-up generation functional | Yes, with valid API key |
| All charts render correctly | Yes |
| A/B comparison visible | Yes |
| No external database required | Yes |
| Readable by a junior developer | Yes |

---

## Out of Scope (MVP)

- User authentication / multi-user support
- Real-time form integrations (Typeform, HubSpot)
- Email sending (SMTP / Mailchimp)
- Mobile app
- Paid ad platform integrations (Google Ads API, Meta API)

---

## Timeline

| Phase | Deliverable | Status |
|-------|------------|--------|
| 1 | Folder structure, sample data, module skeletons | Complete |
| 2 | Streamlit dashboard with CRM + analytics views | Planned |
| 3 | AI follow-up generator integration | Planned |
| 4 | A/B testing comparison view | Planned |
| 5 | Polish, docs, interview prep | Planned |
