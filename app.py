import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from data.data_generator import generate_marketing_data

DATA_PATH = Path(__file__).resolve().parent / "data" / "marketing_data.xlsx"


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load campaign data from the Excel sheet or generate it if missing."""
    if DATA_PATH.exists():
        df = pd.read_excel(DATA_PATH)
    else:
        df = generate_marketing_data(500, export_excel=True)

    df = df.copy()
    df["CTR"] = df["CTR"].astype(float)
    df["CPA"] = df["CPA"].astype(float)
    df["ROAS"] = df["ROAS"].astype(float)
    df["Impressions"] = df["Impressions"].astype(int)
    df["Clicks"] = df["Clicks"].astype(int)
    df["Conversions"] = df["Conversions"].astype(int)
    df["Spend ($)"] = df["Spend ($)"].astype(float)

    return df


def build_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate campaign performance to the audience segment level."""
    summary = (
        df.groupby("Audience Segment", as_index=False)
        .agg(
            Spend=("Spend ($)", "sum"),
            Impressions=("Impressions", "sum"),
            Clicks=("Clicks", "sum"),
            Conversions=("Conversions", "sum"),
            ROAS=("ROAS", "mean"),
        )
    )
    summary["CTR"] = summary["Clicks"] / summary["Impressions"]
    summary["CPA"] = summary["Spend"] / summary["Conversions"]
    summary["Conversion Efficiency"] = summary["Conversions"] / summary["Spend"]
    summary = summary.round({"CTR": 5, "CPA": 2, "ROAS": 2, "Conversion Efficiency": 5})
    return summary.sort_values("Spend", ascending=False)


def render_header() -> None:
    st.set_page_config(page_title="Agentic Campaign Optimization Engine", layout="wide")
    st.title("Agentic Campaign Optimization Engine")
    st.markdown(
        """
        **Agentic Campaign Optimization Engine** simulates how an AI agent can ingest marketing data, detect poor performance,
        rewrite ad creative, and reallocate budget for better results.

        Use the sidebar to explore: the campaign dashboard, anomaly detection, creative optimization, and budget reallocation.
        """
    )


def campaign_dashboard(df: pd.DataFrame) -> None:
    st.header("Campaign Dashboard")
    with st.expander("Workshop overview", expanded=True):
        st.write(
            "This dashboard ingests the actual marketing dataset from the Excel file and visualizes the performance "
            "funnel from spend to conversions. The agent monitors these charts to identify where campaign efficiency drops."
        )

    total_spend = df["Spend ($)"].sum()
    total_conversions = df["Conversions"].sum()
    average_cpa = (df["Spend ($)"].sum() / df["Conversions"].sum()) if total_conversions else 0
    average_roas = df["ROAS"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spend", f"${total_spend:,.0f}")
    col2.metric("Total Conversions", f"{total_conversions:,}")
    col3.metric("Average CPA", f"${average_cpa:,.2f}")
    col4.metric("Average ROAS", f"{average_roas:.2f}x")

    segment_summary = build_segment_summary(df)

    fig_spend_vs_conv = px.scatter(
        segment_summary,
        x="Spend",
        y="Conversions",
        size="Impressions",
        color="ROAS",
        hover_data=["Audience Segment", "CPA", "CTR"],
        title="Spend vs Conversions by Audience Segment",
        labels={"Spend": "Spend ($)", "Conversions": "Conversions", "ROAS": "ROAS"},
        template="plotly_white",
    )
    fig_spend_vs_conv.update_layout(height=520)

    fig_cpa_platform = px.bar(
        df.groupby("Platform", as_index=False)["CPA"].mean(),
        x="Platform",
        y="CPA",
        text="CPA",
        title="Average CPA by Platform",
        labels={"CPA": "Average CPA ($)"},
        template="plotly_white",
    )
    fig_cpa_platform.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig_cpa_platform.update_layout(yaxis_title="CPA ($)", height=520)

    fig_roas = px.bar(
        segment_summary.sort_values("ROAS", ascending=False).head(10),
        x="ROAS",
        y="Audience Segment",
        orientation="h",
        title="Top 10 Segments by ROAS",
        labels={"ROAS": "ROAS", "Audience Segment": "Segment"},
        template="plotly_white",
    )
    fig_roas.update_layout(height=520)

    st.plotly_chart(fig_spend_vs_conv, use_container_width=True)
    st.plotly_chart(fig_cpa_platform, use_container_width=True)
    st.plotly_chart(fig_roas, use_container_width=True)

    with st.expander("View segment-level performance details", expanded=False):
        st.dataframe(segment_summary.style.format({"Spend": "${:,.0f}", "CPA": "${:,.2f}", "ROAS": "{:.2f}x", "CTR": "{:.2%}"}))


def anomaly_detection(df: pd.DataFrame) -> None:
    st.header("Anomaly Detection")
    st.write(
        "The agent flags underperforming segments using clear thresholds: CPA above $50 and/or CTR below 0.5%. "
        "This helps the workshop team focus on the most obvious opportunities for creative and budget fixes."
    )

    segment_summary = build_segment_summary(df)
    underperformers = segment_summary.loc[(segment_summary["CPA"] > 50) | (segment_summary["CTR"] < 0.005)]
    worst_offenders = underperformers.sort_values(["CPA", "CTR"], ascending=[False, True]).head(5)

    col1, col2, col3 = st.columns(3)
    col1.metric("Underperforming Segments", f"{len(underperformers)}")
    col2.metric("Worst CPA", f"${worst_offenders['CPA'].max():,.2f}")
    col3.metric("Lowest CTR", f"{worst_offenders['CTR'].min():.2%}")

    st.markdown("### Underperforming Segments")
    if len(underperformers):
        styled = (
            underperformers.style
            .format({"Spend": "${:,.0f}", "CPA": "${:,.2f}", "ROAS": "{:.2f}x", "CTR": "{:.2%}"})
            .apply(
                lambda col: ["background-color: #ffcccc" if v > 50 else "" for v in col],
                subset=["CPA"],
            )
        )
        st.dataframe(styled)
    else:
        st.success("No underperforming segments detected. The agent is happy!")

    st.markdown("### Worst Offenders")
    st.table(
        worst_offenders.style.format(
            {"Spend": "${:,.0f}", "CPA": "${:,.2f}", "ROAS": "{:.2f}x", "CTR": "{:.2%}"}
        )
    )

    fig = px.scatter(
        underperformers,
        x="CTR",
        y="CPA",
        size="Spend",
        color="ROAS",
        hover_name="Audience Segment",
        title="Underperformers: CPA vs CTR",
        labels={"CTR": "CTR", "CPA": "CPA ($)"},
        template="plotly_white",
    )
    fig.update_layout(yaxis_title="CPA ($)", xaxis_tickformat=".1%", height=520)
    st.plotly_chart(fig, use_container_width=True)


def simulate_agent_recommendations(segment: str) -> tuple[str, list[dict[str, str]]]:
    base_reasons = {
        "Tech Bros 25-34": (
            "The current creative feels too generic for this tech-savvy audience. They respond best to performance, innovation, and social proof.",
            [
                {"Headline": "Ship Faster with the Tools Built for Modern Engineers", "Primary Text": "Boost your launch velocity with software designed for ambitious developers aged 25-34. Trusted by top startups."},
                {"Headline": "Scale Your Side Hustle with Smarter Marketing", "Primary Text": "Grow revenues with ads crafted for tech-focused founders who want data-driven results and fewer manual tasks."},
                {"Headline": "Stop Wasting Time on Slow Workflows", "Primary Text": "Discover a faster path to productivity with a platform made for tech pros who demand speed and reliability."},
            ],
        ),
        "Soccer Moms": (
            "This segment needs warm, family-first messaging that highlights convenience, trust, and value for busy parents.",
            [
                {"Headline": "Simplify Your Week with Family-Friendly Savings", "Primary Text": "Keep the kids happy and your schedule on track with products built for active families."},
                {"Headline": "Trusted by Parents Who Want More Free Time", "Primary Text": "Enjoy expert tips, reliable services, and easy solutions designed for busy soccer moms."},
                {"Headline": "Make Every Moment Count with Better Planning", "Primary Text": "From school runs to game days, our tool helps you stay organized without the stress."},
            ],
        ),
        "Home Decor Lovers": (
            "The audience is looking for immersive styling inspiration, aspirational visuals, and a strong sense of personal taste.",
            [
                {"Headline": "Curate Your Dream Home in Minutes", "Primary Text": "Explore beautifully designed pieces that bring warmth, style, and personality to every room."},
                {"Headline": "Fresh Decor Ideas for Your Unique Space", "Primary Text": "Discover the collection loved by design enthusiasts who want bold, affordable home updates."},
                {"Headline": "Turn Blank Walls into Stylish Statements", "Primary Text": "Elevate your home with curated decor that feels premium, effortless, and perfectly you."},
            ],
        ),
    }
    fallback = (
        "The selected audience segment needs a sharper, more targeted message that matches their motivations and stage in the buyer journey.",
        [
            {"Headline": "Unlock Better Results with Smarter Creative", "Primary Text": "Realign your messaging to match what your audience actually cares about and watch engagement improve."},
            {"Headline": "Move Fast with Ads Built for Your Best Customers", "Primary Text": "Use targeted headlines and copy that speak directly to audience needs and business outcomes."},
            {"Headline": "Stop Guessing and Start Converting", "Primary Text": "Switch to creative that identifies the problem, shows the benefit, and delivers a clear next step."},
        ],
    )

    return base_reasons.get(segment, fallback)


def creative_optimization(df: pd.DataFrame) -> None:
    st.header("Agentic Creative Optimization")
    st.write(
        "Select an underperforming audience segment and let the agent simulate a creative diagnosis plus fresh ad copy variants." 
        "This workflow highlights how an AI agent moves from data to a concrete creative recommendation."
    )

    segment_summary = build_segment_summary(df)
    underperformers = segment_summary.loc[(segment_summary["CPA"] > 50) | (segment_summary["CTR"] < 0.005)]
    selection = st.selectbox("Choose an underperforming segment", underperformers["Audience Segment"].tolist())

    if st.button("Run AI Agent"):
        with st.spinner("Analyzing creative performance and generating copy..."):
            analysis, variants = simulate_agent_recommendations(selection)
            st.success("AI Agent has completed the creative optimization analysis.")
            st.markdown(f"### Why this creative is failing for {selection}")
            st.write(analysis)

            cols = st.columns(3)
            for idx, variant in enumerate(variants):
                with cols[idx]:
                    st.markdown(f"**Variant {idx + 1}**")
                    st.markdown(f"**Headline:** {variant['Headline']}")
                    st.markdown(f"**Primary Text:** {variant['Primary Text']}")

            st.markdown(
                "---\n"
                "The agent suggests using more audience-specific triggers and simplifying the message so the creative converts better for the chosen segment."
            )
    else:
        st.info("Select a segment and click 'Run AI Agent' to generate tailored ad copy recommendations.")


def budget_reallocation(df: pd.DataFrame) -> None:
    st.header("Budget Reallocation Engine")
    st.write(
        "The agent recommends shifting budget away from underperforming segments and into the best performers. "
        "This page visualizes the current allocation and the projected impact on conversions."
    )

    segment_summary = build_segment_summary(df)
    segment_summary["Budget Share"] = segment_summary["Spend"] / segment_summary["Spend"].sum()
    underperformers = segment_summary.loc[(segment_summary["CPA"] > 50) | (segment_summary["CTR"] < 0.005)]
    top_performers = segment_summary.sort_values("ROAS", ascending=False).head(3)

    shifted_budget = (underperformers["Spend"] * 0.20).sum()
    recommendation = segment_summary.copy()
    recommendation.loc[underperformers.index, "Spend"] = recommendation.loc[underperformers.index, "Spend"] * 0.80

    top_share = top_performers["Spend"] / top_performers["Spend"].sum()
    recommendation.loc[top_performers.index, "Spend"] += shifted_budget * top_share.values

    recommendation["Projected Conversions"] = (recommendation["Spend"] * recommendation["Conversion Efficiency"]).round().astype(int)
    current_total = segment_summary["Conversions"].sum()
    projected_total = recommendation["Projected Conversions"].sum()
    delta_conversions = projected_total - current_total

    st.metric("Budget shift amount", f"${shifted_budget:,.0f}")
    st.metric("Current conversions", f"{current_total:,}")
    st.metric("Projected conversions", f"{projected_total:,}", delta=f"{delta_conversions:+,}")

    allocation = pd.DataFrame(
        {
            "Audience Segment": segment_summary["Audience Segment"],
            "Current Spend": segment_summary["Spend"],
            "Recommended Spend": recommendation["Spend"],
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=allocation["Audience Segment"],
            y=allocation["Current Spend"],
            name="Current Spend",
            marker_color="#636EFA",
        )
    )
    fig.add_trace(
        go.Bar(
            x=allocation["Audience Segment"],
            y=allocation["Recommended Spend"],
            name="Recommended Spend",
            marker_color="#EF553B",
        )
    )
    fig.update_layout(
        barmode="group",
        title="Current Budget vs Agent Recommended Allocation",
        xaxis_title="Audience Segment",
        yaxis_title="Spend ($)",
        template="plotly_white",
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Top 3 Recommended Budget Winners")
    st.table(
        recommendation.loc[top_performers.index]
        .sort_values("Projected Conversions", ascending=False)
        .rename(columns={"Spend": "Recommended Spend"})
        .style.format({"Recommended Spend": "${:,.0f}", "Projected Conversions": "{:,}", "CPA": "${:,.2f}", "ROAS": "{:.2f}x", "CTR": "{:.2%}"})
    )

    with st.expander("Key assumptions behind the projection", expanded=False):
        st.write(
            "The agent assumes each segment keeps its current conversion efficiency, so reallocating budget toward higher-efficiency segments increases total conversions. "
            "This is a simplified projection for workshop discussion rather than a precise financial model."
        )


def main() -> None:
    render_header()
    df = load_data()

    page = st.sidebar.radio(
        "Select a page",
        [
            "Campaign Dashboard",
            "Anomaly Detection",
            "Agentic Creative Optimization",
            "Budget Reallocation Engine",
        ],
    )

    if page == "Campaign Dashboard":
        campaign_dashboard(df)
    elif page == "Anomaly Detection":
        anomaly_detection(df)
    elif page == "Agentic Creative Optimization":
        creative_optimization(df)
    elif page == "Budget Reallocation Engine":
        budget_reallocation(df)


if __name__ == "__main__":
    main()
