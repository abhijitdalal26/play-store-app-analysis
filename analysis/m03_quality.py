"""Section 3 — Ratings & Quality: does anyone actually love these apps."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from analysis import data_prep as dp
from analysis.charts import save_static, save_interactive, PRIMARY, OLD, CATEGORICAL


def build():
    new = dp.new_apps()
    new_g = dp.new_genre_stats()

    # Ratings volume vs score — is there a "more reviews = better rated" effect?
    sub = new.dropna(subset=["score", "ratings"])
    sub = sub[sub["ratings"] > 0]
    fig = px.scatter(
        sub, x="ratings", y="score", color="genre", opacity=0.55,
        hover_data={"title": True, "genre": True, "ratings": ":,", "score": ":.2f"},
        labels={"ratings": "Number of ratings (log scale)", "score": "Star rating"},
        color_discrete_sequence=CATEGORICAL * 6,
    )
    fig.update_xaxes(type="log")
    fig.update_layout(title="Popularity Doesn't Buy Love: Ratings Volume vs. Star Rating (2026)",
                       height=560, showlegend=False)
    p1 = save_interactive(fig, "m03_ratings_vs_score")

    # Content rating breakdown
    cr = new["content_rating"].value_counts(normalize=True).mul(100).round(1)
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.bar(cr.index, cr.values, color=PRIMARY)
    ax2.set_ylabel("% of apps")
    ax2.set_title("Content Rating Mix, 2026 Catalogue")
    for i, v in enumerate(cr.values):
        ax2.annotate(f"{v:.0f}%", (i, v), ha="center", va="bottom")
    fig2.tight_layout()
    p2 = save_static(fig2, "m03_content_rating")

    # Best and worst rated categories (min 15 apps, by avg score) — 2026
    qualified = new_g[new_g["app_count"] >= 15].sort_values("avg_score", ascending=False)
    best = qualified.head(8)
    worst = qualified.tail(8)
    combo = pd.concat([best, worst]).sort_values("avg_score")
    fig3, ax3 = plt.subplots(figsize=(9, 7))
    colors = [PRIMARY if v >= combo["avg_score"].median() else OLD for v in combo["avg_score"]]
    ax3.barh(combo["genre"], combo["avg_score"], color=colors)
    ax3.set_xlim(3.5, 5.0)
    ax3.set_xlabel("Average star rating")
    ax3.set_title("Best & Worst Rated Categories (≥15 apps), 2026")
    fig3.tight_layout()
    p3 = save_static(fig3, "m03_best_worst_categories")

    top_cat = qualified.iloc[0]
    bottom_cat = qualified.iloc[-1]

    return [{
        "id": "ratings-quality",
        "kicker": "Part 4 · Ratings & Quality",
        "title": "Reach and quality are two different games",
        "narrative": [
            "Plotting every app's rating count against its star score shows almost no correlation — "
            "apps with a handful of reviews are just as likely to sit at 4.5 stars as apps with "
            "millions of them. Star rating is not a proxy for scale; it's closer to a proxy for "
            "how well an app satisfies the narrow audience that bothered to review it.",
            f"At the category level the spread is real: <strong>{top_cat['genre']}</strong> "
            f"averages {top_cat['avg_score']:.2f}★ across {int(top_cat['app_count'])} apps, while "
            f"<strong>{bottom_cat['genre']}</strong> trails at {bottom_cat['avg_score']:.2f}★. "
            "Categories that skew utility-first and low-friction (reference tools, simple productivity) "
            "tend to out-rate categories where user expectations are harder to meet consistently "
            "(entertainment, social, anything ad-heavy).",
        ],
        "figures": [
            {"type": "interactive", "path": p1, "caption": "Each dot is one app. No visible upward trend means high ratings volume does not predict a high score."},
            {"type": "static", "path": p2, "caption": "Content rating distribution across the live catalogue."},
            {"type": "static", "path": p3, "caption": "Categories with the strongest and weakest average ratings (minimum 15 apps)."},
        ],
    }]
