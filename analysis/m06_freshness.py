"""Section 6 — Freshness: release trends over time and how actively apps are maintained today."""
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timezone

from analysis import data_prep as dp
from analysis.charts import save_static, save_interactive, PRIMARY, OLD


def build():
    trend = dp.old_release_trend()
    trend = trend[(trend["year"] >= 2010) & (trend["year"] <= 2021)]

    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax1.bar(trend["year"], trend["app_count"], color=OLD, alpha=0.85, label="Apps released")
    ax1.set_ylabel("Apps released that year")
    ax1.set_xlabel("Year")
    ax2 = ax1.twinx()
    ax2.plot(trend["year"], trend["avg_score"], color=PRIMARY, marker="o", lw=2, label="Avg rating")
    ax2.set_ylabel("Average rating")
    ax2.set_ylim(3.5, 5)
    ax1.set_title("A Decade of Publishing: Release Volume & Average Rating by Cohort (2022 archive)")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    fig.tight_layout()
    p1 = save_static(fig, "m06_release_trend")

    # freshness of the current live catalogue — days since last update
    new = dp.new_apps().dropna(subset=["updated_dt"])
    now = new["updated_dt"].max()
    days_since = (now - new["updated_dt"]).dt.days
    bins = [0, 30, 90, 180, 365, 730, 100000]
    labels = ["<1 month", "1-3 months", "3-6 months", "6-12 months", "1-2 years", "2+ years"]
    bucket = pd.cut(days_since, bins=bins, labels=labels)
    dist = bucket.value_counts(normalize=True).reindex(labels).mul(100)

    fig2 = go.Figure(go.Bar(x=dist.index.astype(str), y=dist.values, marker_color=PRIMARY,
                             text=[f"{v:.0f}%" for v in dist.values], textposition="outside"))
    fig2.update_layout(title="How Recently Have Live Apps Been Updated? (2026 scrape)",
                        xaxis_title="Time since last update", yaxis_title="Share of apps", height=460)
    p2 = save_interactive(fig2, "m06_update_recency")

    stale_pct = dist[["1-2 years", "2+ years"]].sum()
    fresh_pct = dist[["<1 month", "1-3 months"]].sum()
    peak_year = int(trend.loc[trend["app_count"].idxmax(), "year"])

    return [{
        "id": "freshness",
        "kicker": "Part 7 · Freshness & Momentum",
        "title": "Publishing peaked years ago — but the survivors are actively maintained",
        "narrative": [
            f"App publishing volume in the archive peaked around <strong>{peak_year}</strong> before "
            "tapering off in the most recent cohorts — partly a real slowdown, partly an artifact of "
            "a dataset frozen at a point in time (very recent apps hadn't yet accumulated the ratings "
            "history that makes them show up cleanly in aggregate stats).",
            f"Among apps live on the store today, <strong>{fresh_pct:.0f}%</strong> were updated within "
            f"the last 90 days, while <strong>{stale_pct:.0f}%</strong> haven't been touched in over a "
            "year. Update recency is one of the more honest signals in this dataset: an app that's still "
            "shipping updates is, at minimum, still being actively operated by someone with a reason to "
            "keep it alive — a reasonable proxy for 'this niche still has commercial upside.'",
        ],
        "figures": [
            {"type": "static", "path": p1, "caption": "Release cohort size and average rating by year, 2010-2021."},
            {"type": "interactive", "path": p2, "caption": "Distribution of time since last update across the current live catalogue."},
        ],
    }]
