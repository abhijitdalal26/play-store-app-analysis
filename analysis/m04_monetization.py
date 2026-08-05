"""Section 4 — Monetization: how apps actually make money, and what it costs users."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from analysis import data_prep as dp
from analysis.charts import save_static, PRIMARY, OLD, CATEGORICAL, PURPLE, GOLD, CORAL


def build():
    new = dp.new_apps()
    new_g = dp.new_genre_stats()

    def model_label(row):
        if not row["free"]:
            return "Paid Premium"
        if row["contains_ads"] and row["in_app_purchases"]:
            return "Hybrid (Ads + IAP)"
        if row["contains_ads"]:
            return "Ad-Supported Only"
        if row["in_app_purchases"]:
            return "IAP Only"
        return "Purely Free"

    new = new.copy()
    new["model"] = new.apply(model_label, axis=1)
    top10 = new_g.nlargest(10, "app_count")["genre"]
    subset = new[new["genre"].isin(top10)]
    ct = pd.crosstab(subset["genre"], subset["model"], normalize="index") * 100
    order = ["Purely Free", "Ad-Supported Only", "IAP Only", "Hybrid (Ads + IAP)", "Paid Premium"]
    ct = ct.reindex(columns=order).fillna(0)
    ct = ct.loc[top10[top10.isin(ct.index)]]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    ct.plot(kind="barh", stacked=True, color=[PRIMARY, GOLD, "#3B6FA0", PURPLE, CORAL], ax=ax, width=0.7)
    for p in ax.patches:
        w = p.get_width()
        if w > 6:
            ax.annotate(f"{w:.0f}%", (p.get_x() + w / 2, p.get_y() + p.get_height() / 2),
                        ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    ax.set_title("Revenue Architecture Across the 10 Largest Categories (2026)")
    ax.set_xlabel("Share of apps in category (%)")
    ax.set_ylabel("")
    ax.legend(title="Monetization model", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    p1 = save_static(fig, "m04_monetization_mix")

    # price distribution, old vs new (paid apps)
    old_price = dp.old_price_distribution()["price"]
    new_price = new.loc[(~new["free"]) & (new["price"] > 0) & (new["price"] < 100), "price"]

    fig2, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=False)
    axes[0].hist(old_price, bins=40, color=OLD)
    axes[0].set_title(f"2022 Paid-App Prices (median ${old_price.median():.2f})")
    axes[0].set_xlabel("Price (USD)")
    axes[1].hist(new_price, bins=40, color=PRIMARY)
    axes[1].set_title(f"2026 Paid-App Prices (median ${new_price.median():.2f})")
    axes[1].set_xlabel("Price (USD)")
    fig2.tight_layout()
    p2 = save_static(fig2, "m04_price_distribution")

    pct_paid_old = 100 - dp.old_headline_stats().iloc[0]["pct_free"] * 100
    pct_paid_new = 100 - new["free"].mean() * 100
    hybrid_share = (new["model"] == "Hybrid (Ads + IAP)").mean() * 100

    return [{
        "id": "monetization",
        "kicker": "Part 5 · Monetization",
        "title": "Paid apps are a rounding error; hybrid ads-plus-IAP is the default",
        "narrative": [
            f"Only <strong>{pct_paid_new:.1f}%</strong> of apps in the 2026 catalogue charge an "
            f"upfront price, down from {pct_paid_old:.1f}% in 2022. The dominant model today is "
            f"a hybrid of advertising and in-app purchases — <strong>{hybrid_share:.0f}%</strong> of apps "
            "in the current scrape run both simultaneously, monetizing free users through ads while "
            "reserving IAP for the smaller cohort willing to pay for removal of friction or unlocks.",
            "The mix isn't uniform across categories, though. Utility categories skew toward ad-only "
            "or IAP-only, while games and entertainment lean hard into the hybrid model — makes sense, "
            "since games have both the engagement to sustain ad breaks and content worth selling.",
            "Of the shrinking pool of apps that still charge upfront, the median price has held "
            "roughly steady, suggesting the paid-app segment that remains is a stable, deliberate niche "
            "(professional tools, specialist utilities) rather than a dying model still finding its floor.",
        ],
        "figures": [
            {"type": "static", "path": p1, "caption": "Monetization model share within each of the 10 largest 2026 categories."},
            {"type": "static", "path": p2, "caption": "Distribution of paid-app prices, 2022 archive vs. 2026 live scrape."},
        ],
    }]
