# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   app.py (Streamlit)                │
│  ┌──────────┐ ┌───────────┐ ┌─────────────────────┐ │
│  │ CRM View │ │ Analytics │ │  AI Follow-Up Gen   │ │
│  └────┬─────┘ └─────┬─────┘ └──────────┬──────────┘ │
└───────┼─────────────┼──────────────────┼────────────┘
        │             │                  │
┌───────▼─────────────▼──────────────────▼────────────┐
│                    src/ modules                      │
│  crm.py │ analytics.py │ lead_scoring.py │ utils.py  │
│                ai_copy_generator.py                  │
└───────────────────────┬──────────────────────────────┘
                        │
        ┌───────────────┼───────────────────┐
        │               │                   │
   data/            output/          Claude API
   crm_leads.csv    generated_        (Anthropic)
   campaign_        followups.csv
   events.csv       campaign_
   sample_           summary.csv
   campaigns.csv
```

## Data Flow

### Lead Ingestion
1. `crm_leads.csv` is the source of truth for all leads.
2. `crm.load_leads()` returns a DataFrame every time the CRM view renders.
3. Status updates write back to the CSV via `crm.save_leads()`.

### Lead Scoring
1. `lead_scoring.compute_scores()` joins leads with `campaign_events.csv`.
2. Score = weighted sum of event interactions + source channel bonus, capped at 100.
3. Scores are stored in `crm_leads.csv`; they can be recalculated on demand.

### AI Follow-Up Generation
1. User selects a lead in the CRM view.
2. `ai_copy_generator.generate_followup()` constructs a prompt with the lead's pain point, industry, and status.
3. The Claude API returns a JSON object with `subject` and `body`.
4. Result is displayed in the UI and optionally appended to `output/generated_followups.csv`.

### Campaign Analytics
1. `analytics.py` aggregates `sample_campaigns.csv` and `campaign_events.csv`.
2. Functions return DataFrames that are passed directly to Plotly charts.
3. A/B comparison joins leads on `landing_page_variant` and events on `event_type`.

## File Responsibilities

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit routing, page layout, state management |
| `src/config.py` | All paths, env vars, shared constants |
| `src/crm.py` | Lead CRUD operations |
| `src/lead_scoring.py` | Score calculation logic |
| `src/ai_copy_generator.py` | Claude API calls and prompt construction |
| `src/analytics.py` | Aggregation queries (pandas only) |
| `src/utils.py` | Formatting, validation, display helpers |

## Design Decisions

**Why CSV, not SQLite?**  
CSV requires no database driver, is inspectable in Excel, and is portable. For an MVP with <10k rows, performance is fine.

**Why Streamlit?**  
Zero frontend code required. Suitable for internal tools. Rapid iteration. Deployable to Streamlit Cloud in minutes.

**Why Claude for copy generation?**  
Claude's instruction-following and JSON output are reliable for structured copy tasks. The prompt is designed to return consistent JSON so the UI can parse it without fragile string splitting.

**Why not LangChain or an agent framework?**  
Unnecessary complexity for a single-turn, single-purpose API call. Direct SDK calls are easier to debug, test, and explain in an interview.
