"""
AI-style follow-up generator.
Produces personalised outreach copy using template-based logic — no external API required.
Templates vary by priority tier (Hot / Warm / Cold / Needs Review) and are selected
deterministically from the lead_id so results are consistent across runs.
"""

import pandas as pd
from datetime import datetime
from src.config import FOLLOWUPS_FILE


# ── Internal helpers ──────────────────────────────────────────────────────────

def _pick(options: list, lead_id: str) -> str:
    """Pick from a list deterministically using the lead number as index."""
    return options[int(lead_id[1:]) % len(options)]


def _pain_category(pain_point: str) -> str:
    """Map raw pain_point text to a short human-readable category."""
    p = pain_point.lower()
    if any(w in p for w in ["report", "visibility", "attribut", "dashboard"]):
        return "reporting and attribution"
    if any(w in p for w in ["manual", "spreadsheet", "admin", "hours per week"]):
        return "manual admin workload"
    if any(w in p for w in ["follow-up", "follow up", "goes cold", "inconsistent"]):
        return "lead follow-up"
    if any(w in p for w in ["crm", "out of date", "sales won't"]):
        return "CRM and data quality"
    if any(w in p for w in ["scor", "qualify", "priorit"]):
        return "lead qualification"
    if any(w in p for w in ["a/b", "landing page", "testing"]):
        return "conversion testing"
    if any(w in p for w in ["linkedin", "outreach", "scalab"]):
        return "outreach scalability"
    if any(w in p for w in ["handoff", "hand-off", "handover"]):
        return "marketing-to-sales handoff"
    if any(w in p for w in ["budget", "expensive", "roi", "cost"]):
        return "marketing ROI"
    return "marketing operations"


def _clean_pain(pain_point: str) -> str:
    """
    Prepare pain_point for mid-sentence use:
    - Strip trailing period
    - Cut at em-dash so the core issue is a clean phrase
    - Lowercase first char, but preserve acronyms (CRM, ROI) and proper nouns (LinkedIn)
    """
    p = pain_point.strip().rstrip(".")
    if " — " in p:
        p = p.split(" — ")[0]
    first_word = p.split()[0] if p.split() else ""
    known_proper = {"LinkedIn", "Google", "A/B"}
    if (len(first_word) >= 2 and first_word.isupper()) or first_word in known_proper:
        return p
    return p[0].lower() + p[1:]


# ── Four public functions ─────────────────────────────────────────────────────

def generate_email_subject(lead: pd.Series) -> str:
    """Return a personalised subject line for the lead's priority tier."""
    priority = lead["priority"]
    first = lead["first_name"]
    company = lead["company"]
    industry = lead["industry"]
    pain_cat = _pain_category(lead["pain_point"])
    lid = lead["lead_id"]

    if priority == "Needs Review":
        return "Manual review required before outreach."

    if priority == "Hot":
        return _pick([
            f"{first} — quick question about {company}'s {pain_cat}",
            f"Ready to fix {company}'s {pain_cat} challenges?",
            f"Worth 20 minutes, {first}? (re: {company})",
        ], lid)

    if priority == "Warm":
        return _pick([
            f"One idea for {company}'s {pain_cat} situation",
            f"{first} — following up on {pain_cat}",
            f"Re: {company} — a quick thought",
        ], lid)

    # Cold
    return _pick([
        f"Quick thought on {pain_cat} for {industry} teams",
        f"Something that might be relevant for {company}",
        f"{first} — relevant to {pain_cat}?",
    ], lid)


def generate_followup_email(lead: pd.Series) -> str:
    """Return a personalised follow-up email body (4–6 lines, human-written tone)."""
    priority = lead["priority"]
    first = lead["first_name"]
    company = lead["company"]
    industry = lead["industry"]
    job_title = lead["job_title"]
    pain = _clean_pain(lead["pain_point"])
    pain_cat = _pain_category(lead["pain_point"])
    lid = lead["lead_id"]

    if priority == "Needs Review":
        return "Manual review required before outreach."

    if priority == "Hot":
        return _pick([
            (
                f"{first},\n\n"
                f"I noticed {company} is working on {pain_cat} — specifically, {pain}. "
                f"It's exactly the kind of problem we help {industry} teams fix.\n\n"
                f"We've worked with several similar organisations recently — in most cases "
                f"they saw a meaningful difference within the first four weeks, "
                f"without a lengthy implementation project.\n\n"
                f"Given your role as {job_title}, I think a 20-minute call could be "
                f"genuinely useful. Would this week or next work for you?"
            ),
            (
                f"{first},\n\n"
                f"Working with {industry} teams, I keep hearing the same theme: {pain}. "
                f"It's a bottleneck that quietly costs more than most people realise.\n\n"
                f"We've built a straightforward approach to fixing this — most teams are "
                f"up and running within two weeks and the difference is immediate.\n\n"
                f"Would you be open to a 20-minute walkthrough tailored to {company}'s setup?"
            ),
            (
                f"{first},\n\n"
                f"I'll get straight to it — {pain_cat} is causing real friction for "
                f"{industry} teams right now, and there are a couple of quick wins that "
                f"could make an immediate difference at {company}.\n\n"
                f"Happy to walk you through them on a short call. "
                f"No lengthy demo — just a direct answer to your specific situation.\n\n"
                f"When works best for you this week?"
            ),
        ], lid)

    if priority == "Warm":
        return _pick([
            (
                f"{first},\n\n"
                f"I wanted to follow up after you showed interest in addressing "
                f"{pain_cat} challenges at {company}.\n\n"
                f"A few {industry} teams I've spoken with recently had a similar challenge "
                f"and found that a short discovery call helped them clarify the right "
                f"approach quickly — even when they weren't sure they were ready to move "
                f"forward yet.\n\n"
                f"Would that be a useful conversation for {company}? "
                f"I'm flexible on timing this week or next."
            ),
            (
                f"{first},\n\n"
                f"Following up on {company}'s interest in improving {pain_cat}.\n\n"
                f"One thing that tends to surprise people in {industry}: the fix is usually "
                f"less complex than it looks. The teams who resolve this fastest start by "
                f"getting a clear picture of where the biggest gap is.\n\n"
                f"Would a no-obligation 20-minute call make sense to map that out together?"
            ),
            (
                f"{first},\n\n"
                f"Just checking in — I know timing matters with decisions like this.\n\n"
                f"If {pain_cat} is still a priority at {company}, I'd be happy to share how "
                f"a couple of similar {industry} teams approached it. "
                f"No commitment needed — just a conversation.\n\n"
                f"Let me know if this week works or if there's a better time."
            ),
        ], lid)

    # Cold
    return _pick([
        (
            f"{first},\n\n"
            f"Cold email — I'll keep it brief.\n\n"
            f"I noticed {company} might be dealing with {pain_cat} — specifically, {pain}. "
            f"Rather than pitch you straight away, one insight worth sharing: the teams "
            f"who fix this fastest usually consolidate their data in one place before "
            f"adding new tools, not the other way around.\n\n"
            f"If that resonates and the timing is right, happy to have a short "
            f"conversation. No pressure at all."
        ),
        (
            f"{first},\n\n"
            f"Quick one — I came across {company} and thought your work on {pain_cat} "
            f"might overlap with what we help {industry} teams with.\n\n"
            f"Happy to send over a short guide on how similar teams have approached "
            f"this, if useful. No obligation — just thought it might be relevant."
        ),
        (
            f"{first},\n\n"
            f"I realise this is a cold email, so I'll be direct.\n\n"
            f"If {pain_cat} is something {company} is actively working on, I might be "
            f"able to help. I work with {industry} teams on exactly this and I've seen "
            f"what tends to work — and what doesn't.\n\n"
            f"Happy to share a couple of quick thoughts if the timing is right."
        ),
    ], lid)


def generate_next_best_action(lead: pd.Series) -> str:
    """Return a short, specific next action for the sales or marketing team."""
    if lead["priority"] == "Needs Review":
        return "Manual review required before outreach."

    status = lead["status"]
    priority = lead["priority"]

    if status == "Closed Won":
        return "Explore upsell opportunity or request a referral while the relationship is warm."
    if status == "Closed Lost":
        return "Add to 90-day re-engagement sequence. Do not contact before that window."
    if status == "Proposal Sent":
        return "Send a brief check-in and offer to address any questions. Don't wait more than 3 days."
    if status == "Qualified" and priority == "Hot":
        return "Send proposal within 24 hours — high intent, don't let momentum drop."
    if status == "Qualified":
        return "Book a discovery call to confirm timeline and budget before sending a proposal."
    if status == "Contacted" and priority == "Hot":
        return "Send personalised follow-up today referencing their pain point. Propose a specific meeting date."
    if status == "Contacted":
        return "Follow up within 48 hours. Reference their specific pain point to re-engage."
    if status == "Nurturing":
        return "Enrol in a 3-step email sequence spaced one week apart. Hold off on direct outreach."
    if status == "New" and priority == "Hot":
        return "Contact today — a high score on a new enquiry is a strong buying signal. Call preferred."
    if status == "New":
        return "Send personalised intro email within 24 hours referencing their pain point."
    return "Review lead status and update before taking further action."


def _followup_angle(lead: pd.Series) -> str:
    """Return a short strategic label for the outreach approach."""
    priority = lead["priority"]
    status = lead["status"]
    source = lead["source"]

    if priority == "Needs Review":
        return "Manual review required"
    if priority == "Hot":
        if source == "Referral":
            return "Referral warmth — leverage shared connection, move fast"
        if source == "LinkedIn":
            return "LinkedIn intent signal — respond to demonstrated interest"
        if status in ["Qualified", "Proposal Sent"]:
            return "Value-led close — urgency + social proof from their industry"
        return "Speed-to-first-contact — high score, act within 24 hours"
    if priority == "Warm":
        if status == "Nurturing":
            return "Nurture re-engagement — insight-led, no hard pitch"
        return "Consultative — help first, pitch second"
    if source in ["Organic", "LinkedIn"]:
        return "Content-driven awareness — education before pitch"
    return "Low-pressure seed — plant for a future cycle"


# ── Entry points ──────────────────────────────────────────────────────────────

def generate_all(lead: pd.Series) -> dict:
    """Generate all four output fields for a single lead."""
    return {
        "email_subject": generate_email_subject(lead),
        "personalised_followup": generate_followup_email(lead),
        "next_best_action": generate_next_best_action(lead),
        "followup_angle": _followup_angle(lead),
    }


def generate_followup_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate follow-ups for all Hot leads and write to output/generated_followups.csv.
    Returns the results as a DataFrame.
    """
    hot_leads = df[df["priority"] == "Hot"].copy()
    rows = []

    for _, lead in hot_leads.iterrows():
        output = generate_all(lead)
        rows.append({
            "lead_id": lead["lead_id"],
            "business_name": lead["company"],
            "priority": lead["priority"],
            "status": lead["status"],
            "lead_score": int(lead["lead_score"]),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            **output,
        })

    result_df = pd.DataFrame(rows)
    if not result_df.empty:
        result_df.to_csv(FOLLOWUPS_FILE, index=False)
    return result_df
