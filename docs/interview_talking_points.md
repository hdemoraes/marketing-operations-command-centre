# Interview Talking Points

Use this document to prepare for conversations about this project in a Marketing AI & Automations Specialist interview.

---

## "Walk me through the project"

> "I built a portfolio project called the Marketing AI Automation Centre — an internal web tool that combines lightweight CRM management, campaign analytics, AI-generated follow-up copy, and A/B test comparison in a single Streamlit app. The goal was to build something that solves real problems I've seen marketing teams face: leads falling through the cracks, reporting taking too long, and AI sitting unused because there's no internal tooling to make it practical. I used Claude Code to assist with development — which is itself relevant to the role — and kept the architecture deliberately simple: Python, Streamlit, CSV storage, and the Anthropic API."

---

## On Claude Code-assisted development

- "I used Claude Code as my development partner — not just for boilerplate, but for discussing architecture trade-offs, reviewing logic, and generating realistic sample data."
- "This mirrors how I'd want to work in this role: using AI to accelerate the right parts of the work while applying my own judgement on product and marketing decisions."
- "I documented the prompts and decisions as I went, so the codebase tells a story of how the tool was built."

---

## On the lead scoring model

- "The scoring model is rule-based and intentionally transparent. Each lead gets points for form submissions, email opens, clicks, and a source channel bonus (Referral outperforms Google Ads, for example). The weights are in `config.py` so a non-developer can adjust them."
- "In a real scenario I'd validate the weights against historical conversion data — but for an MVP, transparent and adjustable beats a black-box ML model."

---

## On the AI copy generation feature

- "The follow-up generator sends each lead's pain point, job title, and industry to Claude. The prompt is constrained to return JSON with a subject line and email body — this makes it parseable and testable."
- "I deliberately avoided generic openers like 'I hope this email finds you well' in the prompt constraints. The output is personalised to the specific pain point the lead indicated when they filled in the form."
- "Graceful degradation: if the API key isn't set, the feature shows a warning rather than crashing."

---

## On the A/B testing comparison

- "Variant A uses a fear-based headline ('Stop Losing Leads') and a dark hero section. Variant B uses an aspirational frame ('Your leads deserve better') with a split hero showing a mock dashboard."
- "The analytics view lets you compare form submission rates, average lead scores, and Closed Won counts per variant — so you can make a data-driven decision about which to scale."

---

## On the tech choices

| Question | Answer |
|---------|--------|
| "Why Streamlit?" | Internal tools don't need React. Streamlit gets you to a working UI in hours, not days. |
| "Why CSV and not a database?" | MVP scope. CSV is inspectable, portable, and doesn't require server setup. Migrating to SQLite is a two-line change in `config.py`. |
| "Why not LangChain?" | Direct SDK calls are simpler, easier to debug, and more explainable. LangChain adds value at agent complexity I don't need here. |
| "Why Claude?" | Strong instruction-following for structured JSON output. Also directly relevant to Anthropic tooling. |

---

## On what you'd do next

1. Replace CSV with SQLite for concurrent access and easier querying
2. Add Streamlit authentication (st.experimental_user or Streamlit Cloud secrets)
3. Connect a real form provider (Typeform, Webflow) via webhook → CSV append
4. Add email sending via Resend or SendGrid so AI drafts can be dispatched from the UI
5. Build a Zapier/Make.com equivalent trigger system for automated nurture sequences

---

## Common objections

**"This is quite simple for a portfolio project"**  
> "Deliberate simplicity is a feature, not a limitation. The goal was a working MVP that demonstrates end-to-end thinking — data model, scoring logic, AI integration, analytics, A/B testing — not over-engineered architecture. Every module is independently testable and the whole thing runs from one command."

**"How would this scale?"**  
> "CSV and Streamlit stop being appropriate around 50k rows and 5+ concurrent users. At that point I'd move storage to SQLite or Postgres, add a proper job queue for AI generation, and potentially split the dashboard into separate Streamlit pages or move to FastAPI + React. But for an internal team tool, this architecture handles the load."
