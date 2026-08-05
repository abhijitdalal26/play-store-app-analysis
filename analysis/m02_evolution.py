"""Section 2 — Evolution: what changed structurally between the 2022 catalogue and the 2026 scrape."""
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from analysis import data_prep as dp
from analysis.charts import save_static, save_interactive, PRIMARY, OLD, CATEGORICAL


def build():
    old = dp.old_headline_stats().iloc[0]
    new = dp.new_apps()

    metrics = {
        "% Free apps": (old["pct_free"] * 100, new["free"].mean() * 100),
        "% Ad-supported": (old["pct_ads"] * 100, new["contains_ads"].mean() * 100),
        "% Offer in-app purchases": (old["pct_iap"] * 100, new["in_app_purchases"].mean() * 100),
    }

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = list(metrics.keys())
    x = np.arange(len(labels))
    w = 0.35
    old_vals = [v[0] for v in metrics.values()]
    new_vals = [v[1] for v in metrics.values()]
    b1 = ax.bar(x - w / 2, old_vals, w, label="2022 catalogue", color=OLD)
    b2 = ax.bar(x + w / 2, new_vals, w, label="2026 scrape", color=PRIMARY)
    ax.set_xticks(x, labels)
    ax.set_ylabel("% of apps")
    ax.set_title("Business Model Shift: 2022 vs. 2026")
    ax.legend()
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    p1 = save_static(fig, "m02_business_model_shift")

    # score comparison — overlaid density via histogram bars (both datasets aggregated)
    old_hist = dp.old_score_histogram()
    old_hist = old_hist[old_hist["score_bin"] >= 1]
    new_scores = new["score"].dropna()
    new_hist = new_scores.round(1).value_counts(normalize=False).sort_index()
    old_norm = old_hist.set_index("score_bin")["n"] / old_hist["n"].sum()
    new_norm = new_hist / new_hist.sum()

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=old_norm.index, y=old_norm.values, name="2022 catalogue",
                           marker_color=OLD, opacity=0.75))
    fig2.add_trace(go.Bar(x=new_norm.index, y=new_norm.values, name="2026 scrape",
                           marker_color=PRIMARY, opacity=0.75))
    fig2.update_layout(barmode="overlay", title="Rating Distribution: 2022 vs. 2026 (normalized)",
                        xaxis_title="Star rating", yaxis_title="Share of apps", height=480)
    p2 = save_interactive(fig2, "m02_rating_shift")

    avg_old = old["avg_score"]
    avg_new = new_scores.mean()
    direction = "risen" if avg_new > avg_old else "fallen"

    return [{
        "id": "evolution",
        "kicker": "Part 2 · Four Years Later",
        "title": "The store didn't just grow — the business model changed underneath it",
        "narrative": [
            f"Average star rating has {direction} from <strong>{avg_old:.2f}</strong> in the 2022 "
            f"catalogue to <strong>{avg_new:.2f}</strong> in the 2026 scrape. That's not necessarily a "
            "quality story on its own — a fresh scrape of currently-live, currently-ranking apps is "
            "biased toward survivors, while the 2022 archive still carries every app that was ever "
            "listed, including the abandoned and the mediocre. Read it as 'what's actually competitive "
            "on the store today' rather than 'apps got better.'",
            "The monetization mix tells a cleaner story: advertising and in-app purchases are more "
            "prevalent in the current live catalogue than they were across the full 2022 archive, "
            "consistent with a broader industry shift away from pure paid-app models over the last "
            "several years.",
        ],
        "figures": [
            {"type": "static", "path": p1, "caption": "Share of apps that are free, ad-supported, or offer in-app purchases."},
            {"type": "interactive", "path": p2, "caption": "Normalized rating distributions — hover to compare bin heights directly."},
        ],
    }]
