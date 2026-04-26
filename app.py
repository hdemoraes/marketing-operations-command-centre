"""
Marketing Operations Command Centre
Lead management, campaign analytics, A/B testing, and follow-up recommendations.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd

from src.crm import load_crm_leads_with_stats, get_data_source
from src.lead_scoring import enrich_leads
from src.analytics import (
    total_pipeline_value,
    conversion_rate,
    hot_lead_count,
    qualified_lead_count,
    leads_by_source,
    pipeline_by_status,
    score_distribution,
    leads_by_industry,
    priority_breakdown,
    monthly_lead_volume,
    ab_variant_comparison,
)
from src.utils import format_currency
from src.ai_copy_generator import generate_all, generate_followup_batch

st.set_page_config(
    page_title="Marketing Operations Command Centre",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def get_data() -> tuple[pd.DataFrame, dict]:
    df, stats = load_crm_leads_with_stats()
    return enrich_leads(df), stats


df, _crm_stats = get_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Data Source")
    _ds = get_data_source()
    if _ds == "Google Sheets CRM":
        st.success(f"🟢 {_ds}")
        if _crm_stats.get("removed", 0) > 0:
            st.caption(
                f"{_crm_stats['valid']} valid leads loaded "
                f"({_crm_stats['removed']} invalid rows removed)."
            )
        else:
            st.caption(f"{_crm_stats['valid']} leads loaded.")
    else:
        st.info(f"📁 {_ds}")
        st.caption("No live CRM connected. Using local sample data.")

    st.markdown("---")
    if st.button("Refresh CRM Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Click after submitting a new landing page lead.")

# ── Session state ─────────────────────────────────────────────────────────────

if "ai_output" not in st.session_state:
    st.session_state.ai_output = None
if "ai_last_id" not in st.session_state:
    st.session_state.ai_last_id = None
if "batch_output" not in st.session_state:
    st.session_state.batch_output = None

# ── Header ────────────────────────────────────────────────────────────────────

st.title("🎯 Marketing Operations Command Centre")
st.caption("Lead capture, campaign performance, pipeline visibility, and follow-up recommendations.")
st.info(
    "Live marketing operations dashboard. "
    "Review lead quality, campaign performance, and recommended next actions."
)
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_overview, tab_crm, tab_analytics, tab_ab, tab_ai = st.tabs([
    "📊 Overview",
    "👥 CRM",
    "📈 Analytics",
    "🧪 A/B Testing",
    "✉️ Follow-Up Recommendations",
])

PRIORITY_LABELS = {
    "Hot": "🔥 Hot",
    "Warm": "🟡 Warm",
    "Cold": "🔵 Cold",
    "Needs Review": "⚠️ Needs Review",
}


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

with tab_overview:
    st.subheader("Pipeline Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Leads", len(df))
    c2.metric("Qualified", qualified_lead_count(df))
    c3.metric("Hot Leads 🔥", hot_lead_count(df))
    c4.metric("Conversion Rate", f"{conversion_rate(df)}%")
    c5.metric("Pipeline Value", format_currency(total_pipeline_value(df)))

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Leads by Source**")
        src_data = leads_by_source(df)
        if src_data.empty:
            st.caption("No source data available.")
        else:
            st.bar_chart(src_data)

    with col_right:
        st.markdown("**Pipeline Value by Status**")
        pipe_data = pipeline_by_status(df)
        if pipe_data.empty:
            st.caption("No pipeline data available.")
        else:
            st.bar_chart(pipe_data)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — CRM
# ─────────────────────────────────────────────────────────────────────────────

with tab_crm:
    st.subheader("Lead Management")

    _crm_cols = [
        "lead_id", "company", "source", "status", "lead_score",
        "priority", "recommended_action", "estimated_value", "landing_page_variant",
    ]
    _missing_crm = [c for c in _crm_cols if c not in df.columns]

    if _missing_crm:
        st.warning(
            f"CRM data is missing expected columns: {', '.join(_missing_crm)}. "
            "Check the connected data source."
        )
    else:
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            status_opts = ["All"] + sorted(df["status"].unique().tolist())
            sel_status = st.selectbox("Status", status_opts)

        with f2:
            source_opts = ["All"] + sorted(df["source"].unique().tolist())
            sel_source = st.selectbox("Source", source_opts)

        with f3:
            sel_variant = st.selectbox("Landing Page Variant", ["All", "A", "B"])

        with f4:
            sort_options = {
                "Estimated Value ↓": ("estimated_value", False),
                "Date Created ↓": ("date_created", False),
                "Lead Score ↓": ("lead_score", False),
            }
            sort_label = st.selectbox("Sort by", list(sort_options.keys()))

        view = df.copy()
        if sel_status != "All":
            view = view[view["status"] == sel_status]
        if sel_source != "All":
            view = view[view["source"] == sel_source]
        if sel_variant != "All":
            view = view[view["landing_page_variant"] == sel_variant]

        sort_col, sort_asc = sort_options[sort_label]
        if sort_col in view.columns:
            view = view.sort_values(sort_col, ascending=sort_asc)

        st.caption(f"Showing **{len(view)}** of {len(df)} leads")

        if view.empty:
            st.info("No leads match the selected filters.")
        else:
            display = view[_crm_cols].copy()
            display = display.rename(columns={"company": "business_name"})
            display["priority"] = display["priority"].map(PRIORITY_LABELS)
            display["estimated_value"] = display["estimated_value"].apply(format_currency)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "lead_id": st.column_config.TextColumn("ID", width="small"),
                    "business_name": st.column_config.TextColumn("Business Name", width="medium"),
                    "source": st.column_config.TextColumn("Source", width="small"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "lead_score": st.column_config.ProgressColumn(
                        "Score", min_value=0, max_value=100, format="%d"
                    ),
                    "priority": st.column_config.TextColumn("Priority", width="small"),
                    "recommended_action": st.column_config.TextColumn(
                        "Next Best Action", width="large"
                    ),
                    "estimated_value": st.column_config.TextColumn("Est. Value", width="small"),
                    "landing_page_variant": st.column_config.TextColumn("Variant", width="small"),
                },
            )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

with tab_analytics:
    st.subheader("Campaign Analytics")

    if df.empty:
        st.info("No data available yet. Connect a CRM source to see analytics.")
    else:
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown("**Lead Score Distribution**")
            dist_data = score_distribution(df)
            if dist_data.sum() == 0:
                st.caption("No score data available.")
            else:
                st.bar_chart(dist_data)

        with col_a2:
            st.markdown("**Monthly Lead Volume**")
            if "date_created" not in df.columns or df["date_created"].isna().all():
                st.caption("No date data available.")
            else:
                st.line_chart(monthly_lead_volume(df))

        st.markdown("---")

        col_a3, col_a4 = st.columns(2)

        with col_a3:
            st.markdown("**Leads by Industry**")
            ind_data = leads_by_industry(df)
            if ind_data.empty:
                st.caption("No industry data available.")
            else:
                st.bar_chart(ind_data)

        with col_a4:
            st.markdown("**Priority Breakdown**")
            pri_data = priority_breakdown(df)
            if pri_data.empty:
                st.caption("No priority data available.")
            else:
                st.bar_chart(pri_data)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — A/B TESTING
# ─────────────────────────────────────────────────────────────────────────────

with tab_ab:
    st.subheader("Landing Page A/B Test Comparison")

    if "landing_page_variant" not in df.columns:
        st.warning("Landing page variant data is not available in the current dataset.")
    else:
        available_variants = sorted(df["landing_page_variant"].dropna().unique().tolist())

        if len(available_variants) < 2:
            variant_label = f"Variant {available_variants[0]}" if available_variants else "no variant"
            st.info(
                f"A/B comparison requires data from both Variant A and Variant B. "
                f"Currently only {variant_label} has data."
            )
        else:
            ab = ab_variant_comparison(df)

            variant_meta = {
                "A": ("Stop Losing Leads to Manual Follow-Up", "Dark hero · Fear-based CTA"),
                "B": ("Your Leads Deserve Better Than a Spreadsheet", "Split layout · Aspirational CTA"),
            }

            col_a, col_b = st.columns(2)
            for col, variant in zip([col_a, col_b], ["A", "B"]):
                variant_rows = ab[ab["landing_page_variant"] == variant]
                with col:
                    st.markdown(f"### Variant {variant}")
                    if variant_rows.empty:
                        st.info("No data for this variant yet.")
                        continue
                    row = variant_rows.iloc[0]
                    headline, style = variant_meta.get(variant, ("", ""))
                    if headline:
                        st.caption(f'"{headline}"')
                        st.caption(style)
                    st.markdown("---")
                    m1, m2 = st.columns(2)
                    m1.metric("Total Leads", int(row["Leads"]))
                    m2.metric("Avg Lead Score", row["Avg Score"])
                    m1.metric("Hot Leads", int(row["Hot Leads"]))
                    m2.metric("Conversion Rate", f"{row['Conversion Rate (%)']}%")
                    st.metric("Est. Pipeline Value", format_currency(row["Pipeline Value (AU$)"]))

            st.markdown("---")

            cc1, cc2, cc3 = st.columns(3)

            with cc1:
                st.markdown("**Conversion Rate (%)**")
                st.bar_chart(ab.set_index("landing_page_variant")["Conversion Rate (%)"])

            with cc2:
                st.markdown("**Average Lead Score**")
                st.bar_chart(ab.set_index("landing_page_variant")["Avg Score"])

            with cc3:
                st.markdown("**Hot Leads**")
                st.bar_chart(ab.set_index("landing_page_variant")["Hot Leads"])

            st.markdown("---")

            with st.expander("Full comparison data"):
                display_ab = ab.set_index("landing_page_variant").rename(
                    columns={"Pipeline Value (AU$)": "Pipeline Value"}
                )
                display_ab["Pipeline Value"] = display_ab["Pipeline Value"].apply(format_currency)
                st.dataframe(display_ab, use_container_width=True)

            ab_a = ab[ab["landing_page_variant"] == "A"]
            ab_b = ab[ab["landing_page_variant"] == "B"]

            if not ab_a.empty and not ab_b.empty:
                a = ab_a.iloc[0]
                b = ab_b.iloc[0]

                if a["Conversion Rate (%)"] > b["Conversion Rate (%)"]:
                    winner, reason = "A", "higher conversion rate"
                elif b["Conversion Rate (%)"] > a["Conversion Rate (%)"]:
                    winner, reason = "B", "higher conversion rate"
                elif a["Avg Score"] >= b["Avg Score"]:
                    winner, reason = "A", "higher average lead score (conversion rates tied)"
                else:
                    winner, reason = "B", "higher average lead score (conversion rates tied)"

                icon = "🔥" if winner == "A" else "✨"
                st.success(
                    f"{icon} **Winning Variant: {winner}** — Selected based on {reason}. "
                    f"Recommend scaling ad spend to this variant."
                )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — FOLLOW-UP RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

with tab_ai:
    st.subheader("Follow-Up Recommendation Engine")
    st.caption(
        "Select a lead to generate a personalised message draft, suggested subject line, "
        "next best action, and outreach angle based on their industry, pain point, and priority tier."
    )

    if df.empty:
        st.info("No leads available. Add leads via the CRM or landing page forms.")
    else:
        st.markdown("---")
        st.markdown("### Single Lead")

        lead_options = [
            f"{row['company']}  ({row['lead_id']})"
            for _, row in df.sort_values("lead_score", ascending=False).iterrows()
        ]

        selected_label = st.selectbox(
            "Select a lead",
            lead_options,
            key="ai_lead_selector",
            help="Leads are sorted by score — highest first",
        )

        selected_id = selected_label.split("(")[1].rstrip(")")
        selected_lead = df[df["lead_id"] == selected_id].iloc[0]

        if st.session_state.ai_last_id != selected_id:
            st.session_state.ai_output = None
            st.session_state.ai_last_id = selected_id

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Lead Score", int(selected_lead["lead_score"]))
        d2.metric("Priority", PRIORITY_LABELS.get(selected_lead["priority"], selected_lead["priority"]))
        d3.metric("Source", selected_lead["source"])
        d4.metric("Status", selected_lead["status"])

        st.markdown(f"**Pain Point:** _{selected_lead['pain_point']}_")
        st.markdown(
            f"**Industry:** {selected_lead['industry']}  ·  "
            f"**Est. Value:** {format_currency(selected_lead['estimated_value'])}"
        )

        st.markdown("")

        if st.button("✉️ Generate Recommendation", type="primary", key="gen_single"):
            st.session_state.ai_output = generate_all(selected_lead)

        if st.session_state.ai_output:
            out = st.session_state.ai_output

            if selected_lead["priority"] == "Needs Review":
                st.warning(
                    "⚠️ This lead is flagged for manual review. "
                    "Outreach is not recommended until the lead status is confirmed."
                )
            else:
                st.markdown("#### Recommendation Output")

                col_meta, col_body = st.columns([1, 2])

                with col_meta:
                    st.markdown("**📧 Suggested Subject Line**")
                    st.info(out["email_subject"])

                    st.markdown("**▶ Next Best Action**")
                    st.success(out["next_best_action"])

                    st.markdown("**📐 Outreach Angle**")
                    st.caption(out["followup_angle"])

                with col_body:
                    st.markdown("**✉️ Recommended Message**")
                    st.text_area(
                        label="",
                        value=out["personalised_followup"],
                        height=230,
                        key="ai_email_body",
                        help="Click inside, Ctrl+A to select all, then copy",
                    )

        st.markdown("---")

        # ── Batch recommendations ─────────────────────────────────────────────

        st.markdown("### Batch Recommendations")
        st.caption("Generates recommendations for all leads currently classified as Hot.")

        hot_count = int((df["priority"] == "Hot").sum())

        if hot_count == 0:
            st.warning(
                "No Hot leads found. Once high-priority leads arrive, "
                "batch recommendations will be available here."
            )
        else:
            st.caption(
                f"**{hot_count} Hot leads** in the current dataset. "
                f"Results are saved to `output/generated_followups.csv`."
            )

            if st.button(
                f"🚀 Generate Follow-Ups for Hot Leads ({hot_count})",
                key="gen_batch",
            ):
                with st.spinner(f"Generating {hot_count} recommendations..."):
                    st.session_state.batch_output = generate_followup_batch(df)

        if st.session_state.batch_output is not None:
            batch_df = st.session_state.batch_output

            if batch_df.empty:
                st.warning("Batch output is empty — no Hot leads were found during generation.")
            else:
                st.success(f"✅ {len(batch_df)} recommendations generated and saved.")

                preview_cols = [
                    "lead_id", "business_name", "status", "email_subject", "followup_angle"
                ]
                missing_cols = [c for c in preview_cols if c not in batch_df.columns]

                if missing_cols:
                    st.warning("Preview columns are missing from the batch output.")
                    st.dataframe(batch_df, use_container_width=True, hide_index=True)
                else:
                    st.dataframe(
                        batch_df[preview_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "lead_id": st.column_config.TextColumn("ID", width="small"),
                            "business_name": st.column_config.TextColumn("Business", width="medium"),
                            "status": st.column_config.TextColumn("Status", width="small"),
                            "email_subject": st.column_config.TextColumn(
                                "Suggested Subject Line", width="large"
                            ),
                            "followup_angle": st.column_config.TextColumn("Angle", width="medium"),
                        },
                    )

                    with st.expander("View all recommendations"):
                        st.dataframe(batch_df, use_container_width=True, hide_index=True)
