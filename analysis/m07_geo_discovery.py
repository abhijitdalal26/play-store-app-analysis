"""Section 7 — Geography & Discoverability: where apps get found, and by whom (2026 dataset only)."""
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from analysis import data_prep as dp
from analysis.charts import save_static, save_interactive, PRIMARY, OLD, CATEGORICAL

COUNTRY_NAMES = {
    "us": "United States", "in": "India", "br": "Brazil", "mx": "Mexico",
    "id": "Indonesia", "gb": "United Kingdom", "de": "Germany", "kr": "South Korea",
    "jp": "Japan", "ph": "Philippines",
}


def build():
    cs = dp.new_country_stats()
    sig = dp.new_discovery_signals()

    # ── Chart A: average score by country storefront ──
    by_country = cs.groupby("country")["score"].mean().sort_values(ascending=False)
    by_country.index = [COUNTRY_NAMES.get(c, c) for c in by_country.index]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.barh(by_country.index[::-1], by_country.values[::-1], color=PRIMARY)
    ax.set_xlim(2.8, 4.2)
    ax.set_xlabel("Average app score, same catalogue, localized storefront")
    ax.set_title("Same Apps, Different Verdicts: Average Rating by Country Storefront")
    fig.tight_layout()
    p1 = save_static(fig, "m07_score_by_country")

    # ── Chart B: chart-page visibility by category ──
    chart_rows = sig[sig["source"] == "chart_page"]
    cat_counts = chart_rows["category"].value_counts()
    fig2, ax2 = plt.subplots(figsize=(9, 6.5))
    ax2.barh(cat_counts.index[::-1], cat_counts.values[::-1], color=OLD)
    ax2.set_xlabel("Chart appearances across tracked countries & chart types")
    ax2.set_title("Which Categories Dominate the Curated Charts?")
    fig2.tight_layout()
    p2 = save_static(fig2, "m07_chart_visibility")

    # ── Chart C: keyword competitiveness — apps surfaced per search keyword ──
    search_rows = sig[sig["source"] == "search"].dropna(subset=["keyword"])
    kw = search_rows.groupby("keyword").agg(
        app_count=("app_id", "nunique"),
        avg_rank=("chart_rank", "mean"),
    ).reset_index()
    kw = kw.sort_values("app_count", ascending=False).head(25)
    fig3 = px.scatter(
        kw, x="app_count", y="avg_rank", text="keyword", size="app_count",
        color="avg_rank", color_continuous_scale="RdYlGn_r", size_max=40,
        labels={"app_count": "Distinct apps surfaced for this keyword",
                "avg_rank": "Average search-result rank (lower = more prominent)"},
    )
    fig3.update_traces(textposition="top center", textfont_size=9)
    fig3.update_yaxes(autorange="reversed")
    fig3.update_layout(title="Keyword Competitiveness: Search Volume vs. Result Crowding",
                        height=560, coloraxis_showscale=False)
    p3 = save_interactive(fig3, "m07_keyword_competition", hover_only_labels=True)

    top_country = by_country.index[0]
    bottom_country = by_country.index[-1]
    top_cat = cat_counts.index[0]
    quiet_keywords = kw.nsmallest(5, "app_count")["keyword"].tolist()

    return [{
        "id": "geo-discovery",
        "kicker": "Part 8 · Geography & Discoverability",
        "title": f"{top_country} rates apps kindest, {bottom_country} rates them harshest — and the charts have favorites",
        "narrative": [
            "The 2026 scrape tracked the same set of apps across ten country storefronts, which "
            "makes it possible to isolate a pure localization effect: identical apps, identical "
            f"functionality, different regional audiences. <strong>{top_country}</strong> users rate "
            f"apps most generously on average, while <strong>{bottom_country}</strong> users are the "
            "toughest graders — a gap worth remembering before treating any single-region rating as "
            "a universal quality signal.",
            f"<strong>{top_cat.replace('_', ' ').title()}</strong> shows up most often across the "
            "curated top-grossing and top-selling charts we tracked, meaning it gets outsized editorial "
            "placement independent of the raw app count in the category — real estate that's worth "
            "more than category size alone suggests.",
            "Keyword search results tell a discoverability story of their own: broad terms return "
            "hundreds of competing apps and bury any one result deep in the list, while narrow, "
            f"intent-specific terms — things like {', '.join(quiet_keywords[:3])} — surface a much "
            "smaller, less contested set of results. That gap between broad and narrow keywords is "
            "exactly where an app store optimization strategy earns its keep.",
        ],
        "figures": [
            {"type": "static", "path": p1, "caption": "Average rating for the identical app catalogue, split by localized storefront."},
            {"type": "static", "path": p2, "caption": "Category frequency across every tracked top-grossing / top-selling chart position."},
            {"type": "interactive", "path": p3, "caption": "Bubble size = number of distinct apps competing for that keyword; lower on the y-axis = buried deeper in results. Labels hide on hover-capable devices — use the tooltip instead."},
        ],
    }]
