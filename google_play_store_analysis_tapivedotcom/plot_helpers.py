"""
plot_helpers.py — Google Play Store Analysis | Visualization Module
====================================================================
All chart functions for the Kaggle dataset analysis notebook.

Usage in notebook:
    import plot_helpers as ph
    ph.plot_score_distribution(score_data)

Chart library guide
-------------------
  Seaborn / Matplotlib  →  statistical distributions, heatmaps, bar charts
  Plotly                →  interactive scatter / bubble charts where hovering
                           over individual data points (app names, categories)
                           adds meaningful context
"""

from __future__ import annotations
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Shared constants ──────────────────────────────────────────────────────────
SAVE_DIR = "images"
BG       = "#0d1117"
SAVE_KW  = dict(dpi=150, bbox_inches="tight", facecolor=BG)
os.makedirs(SAVE_DIR, exist_ok=True)


# =============================================================================
# SECTION 1 — DATA OVERVIEW
# =============================================================================

def plot_missing_values(null_df):
    """
    Horizontal bar chart of missing-value % per column.

    Parameters
    ----------
    null_df : pd.DataFrame  columns = ["Column", "Missing_Pct"]
    """
    null_df = null_df.sort_values("Missing_Pct", ascending=True).reset_index(drop=True)
    palette = [
        "#238636" if v == 0 else
        "#1f6feb" if v < 10 else
        "#d29922" if v < 50 else "#da3633"
        for v in null_df["Missing_Pct"]
    ]

    fig, ax = plt.subplots(figsize=(10, 9))
    bars = ax.barh(null_df["Column"], null_df["Missing_Pct"],
                   color=palette, edgecolor="#30363d", linewidth=0.5)

    ax.set_xlabel("Missing %", labelpad=8)
    ax.set_title("Missing Values Per Column", fontweight="bold", pad=12)
    ax.axvline(50, color="#da3633", ls="--", lw=1.2, alpha=0.7, label="50% threshold")
    ax.axvline(10, color="#d29922", ls="--", lw=1.2, alpha=0.7, label="10% threshold")
    ax.set_xlim(0, 110)

    for bar, val in zip(bars, null_df["Missing_Pct"]):
        if val > 0.5:
            ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", ha="left", fontsize=8.5, color="#c9d1d9")

    patches = [
        mpatches.Patch(color="#238636", label="0% missing"),
        mpatches.Patch(color="#1f6feb", label="< 10%"),
        mpatches.Patch(color="#d29922", label="10 – 50%"),
        mpatches.Patch(color="#da3633", label="> 50%"),
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/01_missing_values.png", **SAVE_KW)
    plt.show()


# =============================================================================
# SECTION 2 — DESCRIPTIVE DISTRIBUTIONS
# =============================================================================

def plot_score_distribution(score_data):
    """
    Histogram + KDE and box plot of app ratings.

    Parameters
    ----------
    score_data : pd.DataFrame  column = "score"
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(score_data["score"], bins=50, kde=True, color="#6c63ff",
                 edgecolor="#30363d", linewidth=0.3, ax=axes[0],
                 line_kws={"lw": 2.5, "color": "#ff6584"})
    axes[0].set_title("Rating Score Distribution", fontweight="bold")
    axes[0].set_xlabel("Score (1 – 5)")
    axes[0].set_ylabel("App Count")
    med = score_data["score"].median()
    avg = score_data["score"].mean()
    axes[0].axvline(med, color="#ffd700", ls="--", lw=1.8, label=f"Median: {med:.2f}")
    axes[0].axvline(avg, color="#ff6584", ls="--", lw=1.8, label=f"Mean:   {avg:.2f}")
    axes[0].legend()

    sns.boxplot(x=score_data["score"], color="#6c63ff", ax=axes[1],
                flierprops={"marker": ".", "markersize": 2, "alpha": 0.3})
    axes[1].set_title("Score Box Plot", fontweight="bold")
    axes[1].set_xlabel("Score (1 – 5)")

    plt.suptitle("2.1 — App Rating Distribution", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/02_score_distribution.png", **SAVE_KW)
    plt.show()

    print(f"Mean: {avg:.3f}  |  Median: {med:.3f}")
    print(f"Apps rated ≥ 4.0 : {(score_data['score'] >= 4.0).mean()*100:.1f}%")
    print(f"Apps rated  < 3.0 : {(score_data['score'] < 3.0).mean()*100:.1f}%")


def plot_install_distribution(install_dist):
    """
    Plotly interactive log-scale bar chart of install bucket distribution.

    Parameters
    ----------
    install_dist : pd.DataFrame  columns = ["minInstalls", "app_count", "pct", "label"]
    """
    fig = px.bar(
        install_dist,
        x="minInstalls", y="app_count",
        hover_data={"app_count": True, "pct": ":.2f", "label": True, "minInstalls": False},
        labels={"minInstalls": "Install Bucket (floor)", "app_count": "Number of Apps", "pct": "% of Apps"},
        title="2.2 — Install Count Distribution (Power-Law Curve)",
        color="app_count",
        color_continuous_scale="Viridis",
        log_x=True,
    )
    fig.update_layout(
        xaxis_title="Minimum Installs (log scale)",
        yaxis_title="Number of Apps",
        coloraxis_showscale=False,
        title_font_size=16,
        height=450,
    )
    fig.show()

    top = install_dist.nlargest(1, "app_count").iloc[0]
    long_tail = install_dist[install_dist["minInstalls"] >= 1_000_000]["pct"].sum()
    print(f"\n💡 Most common bucket  : {top['label']} installs ({top['pct']:.1f}% of apps)")
    print(f"💡 Apps with 1M+ installs : {long_tail:.1f}%")


def plot_free_vs_paid(fp_data):
    """
    Pie chart + avg-installs bar + avg-score bar for free vs paid.

    Parameters
    ----------
    fp_data : pd.DataFrame  columns = ["app_type", "count", "avg_installs", "avg_score"]
    """
    COLORS = ["#6c63ff", "#ff6584"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].pie(fp_data["count"], labels=fp_data["app_type"], autopct="%1.1f%%",
                colors=COLORS, startangle=90,
                textprops={"color": "#c9d1d9", "fontsize": 12},
                wedgeprops={"edgecolor": BG, "linewidth": 2})
    axes[0].set_title("2.3a — Free vs Paid\n(by app count)", fontweight="bold")

    bars = axes[1].bar(fp_data["app_type"], fp_data["avg_installs"] / 1e6,
                       color=COLORS, edgecolor="#30363d")
    axes[1].set_title("2.3b — Avg Min Installs\n(Free vs Paid)", fontweight="bold")
    axes[1].set_ylabel("Avg Min Installs (Millions)")
    for bar, val in zip(bars, fp_data["avg_installs"] / 1e6):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                     f"{val:.1f}M", ha="center", fontweight="bold", color="#c9d1d9")

    bars2 = axes[2].bar(fp_data["app_type"], fp_data["avg_score"],
                        color=COLORS, edgecolor="#30363d")
    axes[2].set_title("2.3c — Avg Rating\n(Free vs Paid)", fontweight="bold")
    axes[2].set_ylabel("Average Score")
    axes[2].set_ylim(0, 5)
    for bar, val in zip(bars2, fp_data["avg_score"]):
        axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                     f"{val:.2f}★", ha="center", fontweight="bold", color="#c9d1d9")

    plt.suptitle("2.3 — Free vs Paid App Comparison", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/03_free_vs_paid.png", **SAVE_KW)
    plt.show()


def plot_category_supply_demand(cat_supply, cat_demand):
    """
    Side-by-side horizontal bars: app count (supply) and total installs (demand).

    Parameters
    ----------
    cat_supply : pd.DataFrame  columns = ["genre", "app_count"]   (top 20)
    cat_demand : pd.DataFrame  columns = ["genre", "total_installs_M"]  (top 20)
    """
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))

    s_pal = sns.color_palette("Blues_r", n_colors=len(cat_supply))
    bars = axes[0].barh(cat_supply["genre"][::-1], cat_supply["app_count"][::-1],
                        color=s_pal, edgecolor="#30363d", linewidth=0.4)
    axes[0].set_title("2.4 — Most Apps by Category (Supply)", fontweight="bold")
    axes[0].set_xlabel("Number of Apps")
    axes[0].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K" if x >= 1000 else f"{x:.0f}"))
    for bar, val in zip(bars, cat_supply["app_count"][::-1]):
        axes[0].text(val + 50, bar.get_y() + bar.get_height() / 2,
                     f"{val:,}", va="center", ha="left", fontsize=8.5, color="#c9d1d9")

    d_pal = sns.color_palette("Purples_r", n_colors=len(cat_demand))
    bars2 = axes[1].barh(cat_demand["genre"][::-1], cat_demand["total_installs_M"][::-1],
                         color=d_pal, edgecolor="#30363d", linewidth=0.4)
    axes[1].set_title("2.5 — Most Installs by Category (Demand)", fontweight="bold")
    axes[1].set_xlabel("Total Min Installs (Millions)")
    for bar, val in zip(bars2, cat_demand["total_installs_M"][::-1]):
        axes[1].text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                     f"{val:,.0f}M", va="center", ha="left", fontsize=8.5, color="#c9d1d9")

    plt.suptitle("Category Supply vs Demand — Top 20", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/04_category_supply_demand.png", **SAVE_KW)
    plt.show()


def plot_review_distribution(review_data):
    """
    Log-scale histogram + KDE of review counts with percentile markers.

    Parameters
    ----------
    review_data : pd.DataFrame  columns = ["reviews", "log_reviews"]
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(review_data["log_reviews"], bins=60, kde=True, color="#f0883e",
                 edgecolor="#30363d", linewidth=0.3, ax=ax,
                 line_kws={"lw": 2, "color": "#ffd700"})
    ax.set_title("2.6 — Review Count Distribution (log₁₀ scale)", fontweight="bold", pad=12)
    ax.set_xlabel("Number of Reviews")
    ax.set_ylabel("App Count")
    ax.set_xticks([0, 1, 2, 3, 4, 5, 6, 7])
    ax.set_xticklabels(["1", "10", "100", "1K", "10K", "100K", "1M", "10M"])

    for p, ls in zip([50, 75, 90, 99], ["--", "-.", ":", "--"]):
        val = np.percentile(review_data["log_reviews"], p)
        ax.axvline(val, ls=ls, lw=1.2, alpha=0.8, label=f"P{p}: {10**val:,.0f}")
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/05_review_distribution.png", **SAVE_KW)
    plt.show()

    print(f"Median reviews   : {int(10**review_data['log_reviews'].median()):,}")
    print(f"P75 reviews      : {int(np.percentile(review_data['reviews'], 75)):,}")
    print(f"P99 reviews      : {int(np.percentile(review_data['reviews'], 99)):,}")


def plot_release_year(year_data):
    """
    Bar chart of app count by release year, peak year highlighted in gold.

    Parameters
    ----------
    year_data : pd.DataFrame  columns = ["releasedYear", "app_count"]
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    palette = sns.color_palette("rocket", n_colors=len(year_data))
    bars = ax.bar(year_data["releasedYear"], year_data["app_count"],
                  color=palette, edgecolor="#30363d", linewidth=0.5)

    peak = year_data.loc[year_data["app_count"].idxmax()]
    ax.bar(peak["releasedYear"], peak["app_count"],
           color="#ffd700", edgecolor="#30363d", label=f"Peak year: {int(peak['releasedYear'])}")

    ax.set_title("2.7 — App Release Timeline by Year", fontweight="bold", pad=12)
    ax.set_xlabel("Release Year")
    ax.set_ylabel("Number of Apps Released")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))
    ax.legend()

    for bar, (_, row) in zip(bars, year_data.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
                f"{row['app_count']/1000:.0f}K",
                ha="center", fontsize=7.5, color="#8b949e", rotation=45)

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/06_release_year.png", **SAVE_KW)
    plt.show()


def plot_iap_price(iap_data):
    """
    Violin + box plot of IAP min/max price ranges (IAP apps only).

    Parameters
    ----------
    iap_data : pd.DataFrame  columns = ["minprice", "maxprice"]
    """
    import pandas as pd

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.violinplot(y=iap_data["maxprice"], color="#6c63ff",
                   ax=axes[0], cut=0, inner="quartile")
    axes[0].set_title("2.8a — IAP Max Price (violin)", fontweight="bold")
    axes[0].set_ylabel("Max IAP Price (USD)")
    axes[0].set_ylim(0, 150)

    melted = iap_data.melt(var_name="Type", value_name="Price")
    melted = melted[melted["Price"] > 0]
    sns.boxplot(data=melted, x="Type", y="Price",
                palette=["#6c63ff", "#ff6584"], ax=axes[1])
    axes[1].set_title("2.8b — IAP Min vs Max Price (box)", fontweight="bold")
    axes[1].set_ylabel("IAP Price (USD)")
    axes[1].set_ylim(0, 100)
    axes[1].set_xticklabels(["Min IAP Price", "Max IAP Price"])

    plt.suptitle("2.8 — In-App Purchase Price Distribution (IAP Apps Only)",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/07_iap_price.png", **SAVE_KW)
    plt.show()

    print(f"Median max IAP price      : ${iap_data['maxprice'].median():.2f}")
    print(f"P75 max IAP price         : ${iap_data['maxprice'].quantile(0.75):.2f}")
    print(f"IAP with max price > $99  : {(iap_data['maxprice'] > 99.99).mean()*100:.1f}%")


# =============================================================================
# SECTION 3 — COMPARATIVE
# =============================================================================

def plot_free_vs_paid_installs(fp_installs):
    """
    Violin of log installs split by free vs paid.

    Parameters
    ----------
    fp_installs : pd.DataFrame  columns = ["app_type", "log_installs"]
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=fp_installs, x="app_type", y="log_installs",
                   palette=["#6c63ff", "#ff6584"], inner="quartile", cut=0, ax=ax)

    for i, app_type in enumerate(["Free", "Paid"]):
        subset = fp_installs[fp_installs["app_type"] == app_type]
        med = subset["log_installs"].median()
        ax.text(i, med + 0.05, f"Median: {int(10**med):,}",
                ha="center", fontsize=10, color="#ffd700", fontweight="bold")

    ax.set_title("3.1 — Install Distribution: Free vs Paid Apps", fontweight="bold", pad=12)
    ax.set_xlabel("App Type")
    ax.set_ylabel("Min Installs (log₁₀ scale)")
    ticks  = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    labels = ["1", "10", "100", "1K", "10K", "100K", "1M", "10M", "100M"]
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/08_free_vs_paid_installs.png", **SAVE_KW)
    plt.show()


def plot_category_avg_rating(cat_rating):
    """
    Horizontal bar of avg score per category, sorted descending.

    Parameters
    ----------
    cat_rating : pd.DataFrame  columns = ["genre", "avg_score", "app_count"]
    """
    fig, ax = plt.subplots(figsize=(10, 9))
    palette = sns.color_palette("RdYlGn", n_colors=len(cat_rating))
    bars = ax.barh(cat_rating["genre"][::-1], cat_rating["avg_score"][::-1],
                   color=palette, edgecolor="#30363d", linewidth=0.4)

    ax.set_title("3.2 — Average Rating by Category (min 100 apps)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Average Score")
    ax.set_xlim(3.0, 5.1)
    overall = cat_rating["avg_score"].mean()
    ax.axvline(overall, color="#ffd700", ls="--", lw=1.5,
               label=f"Overall avg: {overall:.2f}")
    ax.legend()

    for bar, val in zip(bars, cat_rating["avg_score"][::-1]):
        ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", fontsize=9, color="#c9d1d9")

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/09_category_avg_rating.png", **SAVE_KW)
    plt.show()


def plot_category_efficiency(cat_efficiency):
    """
    Horizontal bar of avg installs per app by category.

    Parameters
    ----------
    cat_efficiency : pd.DataFrame  columns = ["genre", "avg_installs", "app_count"]
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    palette = sns.color_palette("magma_r", n_colors=len(cat_efficiency))
    bars = ax.barh(cat_efficiency["genre"][::-1],
                   cat_efficiency["avg_installs"][::-1] / 1e6,
                   color=palette, edgecolor="#30363d", linewidth=0.4)

    ax.set_title("3.3 — Install Efficiency by Category\n(Avg Min Installs Per App)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Average Min Installs (Millions)")

    for bar, (_, row) in zip(bars, cat_efficiency[::-1].iterrows()):
        avg = row["avg_installs"] / 1e6
        ax.text(avg + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{avg:.1f}M  (n={row['app_count']:,})",
                va="center", ha="left", fontsize=8.5, color="#c9d1d9")

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/10_category_efficiency.png", **SAVE_KW)
    plt.show()


def plot_iap_ads_effect(iap_score, ads_installs):
    """
    3.4 Violin: IAP vs no-IAP rating.
    3.5 Violin: ad-supported vs no-ads installs.

    Parameters
    ----------
    iap_score    : pd.DataFrame  columns = ["iap_label", "score"]
    ads_installs : pd.DataFrame  columns = ["ads_label", "log_installs"]
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sns.violinplot(data=iap_score, x="iap_label", y="score",
                   palette=["#6c63ff", "#ff6584"], inner="quartile", cut=0, ax=axes[0])
    axes[0].set_title("3.4 — Rating: IAP vs No-IAP Apps", fontweight="bold")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Score (1 – 5)")
    for i, label in enumerate(["Has IAP", "No IAP"]):
        med = iap_score[iap_score["iap_label"] == label]["score"].median()
        axes[0].text(i, med + 0.05, f"Median: {med:.2f}★",
                     ha="center", fontsize=9, color="#ffd700", fontweight="bold")

    sns.violinplot(data=ads_installs, x="ads_label", y="log_installs",
                   palette=["#f0883e", "#3fb950"], inner="quartile", cut=0, ax=axes[1])
    axes[1].set_title("3.5 — Installs: Ad-Supported vs No Ads", fontweight="bold")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Min Installs (log₁₀ scale)")

    plt.suptitle("Effect of IAP & Ads on App Performance",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/11_iap_ads_effect.png", **SAVE_KW)
    plt.show()


def plot_monetization_model(mono_data):
    """
    Plotly 3-panel bar: app count, avg installs, avg score by monetization model.

    Parameters
    ----------
    mono_data : pd.DataFrame
        columns = ["model", "app_count", "avg_installs_M", "avg_score"]
    """
    from IPython.display import display as ipy_display

    colors = px.colors.qualitative.Vivid[:len(mono_data)]
    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=["App Count", "Avg Installs (M)", "Avg Rating"])

    fig.add_trace(go.Bar(x=mono_data["model"], y=mono_data["app_count"],
                         marker_color=colors, showlegend=False,
                         hovertemplate="<b>%{x}</b><br>Apps: %{y:,}<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=mono_data["model"], y=mono_data["avg_installs_M"],
                         marker_color=colors, showlegend=False,
                         hovertemplate="<b>%{x}</b><br>Avg Installs: %{y:.2f}M<extra></extra>"),
                  row=1, col=2)
    fig.add_trace(go.Bar(x=mono_data["model"], y=mono_data["avg_score"],
                         marker_color=colors, showlegend=False,
                         hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.3f}<extra></extra>"),
                  row=1, col=3)

    fig.update_layout(title_text="3.6 — Monetization Model Performance Comparison",
                      title_font_size=16, height=450)
    fig.show()
    ipy_display(mono_data.sort_values("avg_installs_M", ascending=False).reset_index(drop=True))


# =============================================================================
# SECTION 4 — CORRELATIONAL
# =============================================================================

def plot_reviews_ratings_vs_installs(scatter_data):
    """
    Plotly side-by-side scatter: reviews vs installs, ratings vs installs.
    Hover shows app name + genre — great for identifying outlier apps.

    Parameters
    ----------
    scatter_data : pd.DataFrame
        columns = ["title", "genre", "reviews", "ratings", "minInstalls", "score",
                   "log_installs", "log_reviews", "log_ratings"]
    """
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["4.1 — Reviews vs Installs",
                                        "4.2 — Ratings vs Installs"])

    hover_genre = scatter_data["genre"].fillna("Unknown").astype(str)

    fig.add_trace(go.Scattergl(
        x=scatter_data["log_reviews"], y=scatter_data["log_installs"],
        mode="markers",
        marker=dict(size=3, color=scatter_data["score"],
                    colorscale="RdYlGn", showscale=True,
                    colorbar=dict(title="Score", x=0.44), opacity=0.5),
        text=scatter_data["title"],
        customdata=hover_genre,
        hovertemplate="<b>%{text}</b><br>Genre: %{customdata}<br>"
                      "Reviews: 10^%{x:.1f}<br>Installs: 10^%{y:.1f}<extra></extra>",
        name="Reviews",
    ), row=1, col=1)

    fig.add_trace(go.Scattergl(
        x=scatter_data["log_ratings"], y=scatter_data["log_installs"],
        mode="markers",
        marker=dict(size=3, color=scatter_data["score"],
                    colorscale="RdYlGn", showscale=False, opacity=0.5),
        text=scatter_data["title"],
        hovertemplate="<b>%{text}</b><br>"
                      "Ratings: 10^%{x:.1f}<br>Installs: 10^%{y:.1f}<extra></extra>",
        name="Ratings",
    ), row=1, col=2)

    fig.update_layout(
        title_text="4.1 & 4.2 — Reviews & Ratings vs Installs (log-log) | Hover for app name",
        title_font_size=15, height=500,
    )
    fig.update_xaxes(title_text="log₁₀(Reviews)", row=1, col=1)
    fig.update_xaxes(title_text="log₁₀(Ratings)", row=1, col=2)
    fig.update_yaxes(title_text="log₁₀(Min Installs)", row=1, col=1)
    fig.show()

    r1 = scatter_data[["log_reviews", "log_installs"]].corr().iloc[0, 1]
    r2 = scatter_data[["log_ratings", "log_installs"]].corr().iloc[0, 1]
    print(f"Pearson r  (log reviews vs log installs) : {r1:.4f}")
    print(f"Pearson r  (log ratings vs log installs) : {r2:.4f}")


def plot_app_age_installs(age_data):
    """
    Bar chart of avg installs by app age (years) with app-count twin axis.

    Parameters
    ----------
    age_data : pd.DataFrame  columns = ["app_age_yrs", "avg_installs_M", "app_count"]
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    palette = sns.color_palette("crest", n_colors=len(age_data))
    bars = ax.bar(age_data["app_age_yrs"], age_data["avg_installs_M"],
                  color=palette, edgecolor="#30363d", linewidth=0.4)

    ax.set_title("4.3 — App Age vs Average Installs", fontweight="bold", pad=12)
    ax.set_xlabel("App Age (Years since release, as of 2024)")
    ax.set_ylabel("Avg Min Installs (Millions)")

    for bar, (_, row) in zip(bars, age_data.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{row['avg_installs_M']:.1f}M",
                ha="center", fontsize=8, color="#8b949e")

    ax2 = ax.twinx()
    ax2.plot(age_data["app_age_yrs"], age_data["app_count"],
             "o--", color="#ffd700", lw=1.5, markersize=4, label="# Apps")
    ax2.set_ylabel("Number of Apps", color="#ffd700")
    ax2.tick_params(axis="y", labelcolor="#ffd700")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/12_app_age_installs.png", **SAVE_KW)
    plt.show()


def plot_screenshots_installs(ss_data):
    """
    Bubble scatter: num screenshots vs avg installs. Bubble size = app count.

    Parameters
    ----------
    ss_data : pd.DataFrame  columns = ["num_screenshots", "avg_installs_M", "app_count"]
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    sc = ax.scatter(
        ss_data["num_screenshots"], ss_data["avg_installs_M"],
        s=ss_data["app_count"] / ss_data["app_count"].max() * 300 + 20,
        c=ss_data["avg_installs_M"], cmap="plasma",
        edgecolors="#30363d", linewidths=0.5, alpha=0.85,
    )
    z  = np.polyfit(ss_data["num_screenshots"], ss_data["avg_installs_M"], 1)
    xs = np.linspace(ss_data["num_screenshots"].min(), ss_data["num_screenshots"].max(), 100)
    ax.plot(xs, np.poly1d(z)(xs), "--", color="#ff6584", lw=1.8, alpha=0.8,
            label=f"Trend (slope={z[0]:.2f})")

    plt.colorbar(sc, ax=ax, label="Avg Installs (M)")
    ax.set_title("4.4 — Screenshots vs Avg Installs\n(bubble size = number of apps)",
                 fontweight="bold")
    ax.set_xlabel("Number of Screenshots")
    ax.set_ylabel("Avg Min Installs (Millions)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/13_screenshots_installs.png", **SAVE_KW)
    plt.show()

    r = ss_data[["num_screenshots", "avg_installs_M"]].corr().iloc[0, 1]
    print(f"Correlation (screenshots vs avg installs): r = {r:.4f}")


def plot_paid_price_sweet_spot(paid_data, bin_agg):
    """
    Plotly: individual paid-app scatter (hover = name) + binned median installs bar.

    Parameters
    ----------
    paid_data : pd.DataFrame  columns = ["price", "minInstalls", "score", "title"]
    bin_agg   : pd.DataFrame  columns = ["price_bin", "median_installs", "app_count"]
    """
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["Individual Paid Apps (hover for name)",
                                        "Median Installs by Price Bracket"])

    fig.add_trace(go.Scattergl(
        x=paid_data["price"],
        y=_np.log10(paid_data["minInstalls"] + 1),
        mode="markers",
        marker=dict(size=4, color=paid_data["score"], colorscale="RdYlGn",
                    showscale=True, colorbar=dict(title="Score", x=0.44), opacity=0.5),
        text=paid_data["title"],
        hovertemplate="<b>%{text}</b><br>Price: $%{x:.2f}<br>"
                      "Installs: 10^%{y:.1f}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=[str(b) for b in bin_agg["price_bin"]],
        y=bin_agg["median_installs"],
        marker_color=px.colors.sequential.Viridis[:len(bin_agg)],
        text=bin_agg["app_count"].apply(lambda x: f"n={x:,}"),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Median Installs: %{y:,}<br>%{text}<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(title_text="4.5 — Paid App Price vs Installs | Sweet Spot Analysis",
                      title_font_size=15, height=500, showlegend=False)
    fig.update_xaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="log₁₀(Min Installs)", row=1, col=1)
    fig.update_xaxes(title_text="Price Bracket", row=1, col=2)
    fig.update_yaxes(title_text="Median Min Installs", row=1, col=2)
    fig.show()


def plot_correlation_heatmap(corr_matrix):
    """
    Seaborn lower-triangle correlation heatmap of all numeric signals.

    Parameters
    ----------
    corr_matrix : pd.DataFrame  (square numeric correlation matrix)
    """
    from IPython.display import display as ipy_display

    fig, ax = plt.subplots(figsize=(14, 12))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f",
                cmap="RdBu_r", center=0, vmin=-1, vmax=1, ax=ax,
                linewidths=0.5, linecolor="#30363d",
                annot_kws={"size": 9},
                cbar_kws={"shrink": 0.8})
    ax.set_title("4.6 — Numeric Signal Correlation Matrix",
                 fontweight="bold", pad=15, fontsize=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/14_correlation_heatmap.png", **SAVE_KW)
    plt.show()

    print("Top correlations with minInstalls:")
    top_corr = (corr_matrix["minInstalls"]
                .drop("minInstalls")
                .sort_values(key=abs, ascending=False)
                .head(8))
    ipy_display(
        top_corr.reset_index()
                .rename(columns={"index": "Feature", "minInstalls": "Correlation"})
    )


def plot_star_tier_breakdown(star_tier_pct):
    """
    Stacked bar of normalised star-vote % by install tier.

    Parameters
    ----------
    star_tier_pct : pd.DataFrame
        columns = ["install_tier", "star1" ... "star5"]  (values already normalised to %)
    """
    STAR_COLORS = ["#da3633", "#d29922", "#e3b341", "#3fb950", "#6c63ff"]
    tier_labels  = star_tier_pct["install_tier"].str.replace(r"^\d+\. ", "", regex=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(star_tier_pct))
    for col, color, star in zip(
        ["star1", "star2", "star3", "star4", "star5"],
        STAR_COLORS, ["1★", "2★", "3★", "4★", "5★"],
    ):
        bars = ax.bar(tier_labels, star_tier_pct[col], bottom=bottom,
                      color=color, label=star, edgecolor=BG, linewidth=0.4)
        for bar, val in zip(bars, star_tier_pct[col]):
            if val > 5:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:.0f}%", ha="center", va="center",
                        fontsize=8, color=BG, fontweight="bold")
        bottom += star_tier_pct[col]

    ax.set_title("4.7 — Star Rating Breakdown by Install Tier\n(% of total votes)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Install Tier")
    ax.set_ylabel("% of Rating Votes")
    ax.legend(title="Star Rating", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    ax.set_ylim(0, 100)
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/15_star_tier_breakdown.png", **SAVE_KW)
    plt.show()


# =============================================================================
# SECTION 5 — OUTLIERS & ANOMALIES
# =============================================================================

def plot_viral_bad_table(viral_bad):
    """
    Plotly interactive table: high-install + low-score apps.
    appId column is clickable-style so user can look up directly.

    Parameters
    ----------
    viral_bad : pd.DataFrame
        columns = ["title", "appId", "genre", "minInstalls", "score", "reviews", "developer"]
    """
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["App Name", "Package (appId)", "Category",
                    "Min Installs", "Score ★", "Reviews", "Developer"],
            fill_color="#1f2937",
            align="left",
            font=dict(color="#c9d1d9", size=11),
            line_color="#374151",
        ),
        cells=dict(
            values=[
                viral_bad["title"],
                viral_bad["appId"],
                viral_bad["genre"],
                viral_bad["minInstalls"].apply(lambda x: f"{x:,}"),
                viral_bad["score"].apply(lambda x: f"{x:.2f}★"),
                viral_bad["reviews"].apply(lambda x: f"{x:,}"),
                viral_bad["developer"],
            ],
            fill_color=[["#161b22" if i % 2 == 0 else BG for i in range(len(viral_bad))]],
            align="left",
            font=dict(
                color=["#c9d1d9", "#58a6ff", "#c9d1d9",
                       "#3fb950", "#da3633", "#c9d1d9", "#c9d1d9"],
                size=10,
            ),
            line_color="#30363d",
        ),
    )])
    fig.update_layout(
        title="5.1 — Viral but Poor Quality: 1M+ Installs & Score < 3.5",
        title_font_size=15,
        height=600,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    fig.show()
    print(f"Found {len(viral_bad)} apps with 1M+ installs and score < 3.5")


def plot_inflated_ratings(inflated):
    """
    Plotly scatter of apps with suspiciously perfect scores and very few ratings.
    Hover for app name, developer, appId — look it up in the CSV!

    Parameters
    ----------
    inflated : pd.DataFrame
        columns = ["title", "appId", "genre", "score", "ratings", "reviews",
                   "developer", "minInstalls"]
    """
    fig = px.scatter(
        inflated, x="ratings", y="score",
        size="minInstalls", size_max=30,
        color="genre",
        hover_name="title",
        hover_data={"appId": True, "developer": True, "reviews": True},
        title=f"5.2 — Suspiciously Perfect Scores (≥ 4.9★) with ≤ 50 Ratings | n={len(inflated)}",
        labels={"ratings": "Number of Ratings", "score": "Score"},
        height=500,
    )
    fig.update_layout(title_font_size=14)
    fig.show()


def plot_oversaturation(cat_sat):
    """
    Plotly quadrant scatter: competition (x) vs demand (y) per category.

    Parameters
    ----------
    cat_sat : pd.DataFrame
        columns = ["genre", "app_count", "avg_installs_M", "total_installs_B"]
    """
    med_count    = cat_sat["app_count"].median()
    med_installs = cat_sat["avg_installs_M"].median()

    cat_sat = cat_sat.copy()
    cat_sat["quadrant"] = cat_sat.apply(lambda r: (
        "🟢 Opportunity"    if r["app_count"] < med_count and r["avg_installs_M"] >= med_installs
        else "🔴 Saturated" if r["app_count"] >= med_count and r["avg_installs_M"] >= med_installs
        else "🟡 Niche"     if r["app_count"] < med_count and r["avg_installs_M"] < med_installs
        else "⚪ Crowded & Weak"
    ), axis=1)

    fig = px.scatter(
        cat_sat, x="app_count", y="avg_installs_M",
        size="total_installs_B", size_max=60,
        color="quadrant",
        color_discrete_map={
            "🟢 Opportunity":    "#3fb950",
            "🔴 Saturated":      "#da3633",
            "🟡 Niche":          "#d29922",
            "⚪ Crowded & Weak": "#8b949e",
        },
        hover_name="genre",
        hover_data={"app_count": True, "avg_installs_M": ":.2f", "total_installs_B": ":.2f"},
        title="5.3 — Category Oversaturation Map | Bubble = Total Installs",
        labels={"app_count": "Number of Apps (Competition)",
                "avg_installs_M": "Avg Installs Per App (M)"},
        log_x=True, height=550,
    )
    fig.add_hline(y=med_installs, line_dash="dash", line_color="#ffd700", opacity=0.6,
                  annotation_text="Median Avg Installs", annotation_position="right")
    fig.add_vline(x=med_count, line_dash="dash", line_color="#ff6584", opacity=0.6,
                  annotation_text="Median App Count", annotation_position="top right")
    fig.update_layout(title_font_size=14)
    fig.show()


def plot_prolific_devs_quality(prolific_devs):
    """
    Plotly scatter: # apps vs avg score for developers with 50+ apps.
    Hover for developer name — cross-reference in CSV via developer / developerId.

    Parameters
    ----------
    prolific_devs : pd.DataFrame
        columns = ["developer", "app_count", "avg_score", "avg_installs", "total_reviews"]
    """
    from IPython.display import display as ipy_display

    fig = px.scatter(
        prolific_devs, x="app_count", y="avg_score",
        size="total_reviews", size_max=50,
        color="avg_score", color_continuous_scale="RdYlGn",
        hover_name="developer",
        hover_data={"app_count": True, "avg_score": ":.3f",
                    "avg_installs": ":,.0f", "total_reviews": ":,"},
        title=f"5.4 — Prolific Devs (50+ Apps): Portfolio Size vs Avg Rating | n={len(prolific_devs)}",
        labels={"app_count": "Number of Apps", "avg_score": "Average Score"},
        height=550,
    )
    fig.add_hline(y=3.0, line_dash="dash", line_color="#da3633", opacity=0.7,
                  annotation_text="Quality floor (3.0★)", annotation_position="right")
    fig.update_layout(title_font_size=14, coloraxis_colorbar_title="Avg Score")
    fig.show()

    low_q = prolific_devs[prolific_devs["avg_score"] < 3.0]
    print(f"Prolific devs (50+ apps) with avg score < 3.0 : {len(low_q)}")
    print("\nTop 5 by app count:")
    ipy_display(
        prolific_devs.head(5)[["developer", "app_count", "avg_score", "avg_installs"]].round(2)
    )


# =============================================================================
# SECTION 6 — DEVELOPER PATTERNS
# =============================================================================

def plot_developer_distribution(dev_counts):
    """
    Histogram of log(app count per developer) + cumulative threshold chart.

    Parameters
    ----------
    dev_counts : pd.DataFrame  columns = ["developer", "app_count", "log_count"]
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(dev_counts["log_count"], bins=50, color="#6c63ff",
                 edgecolor="#30363d", kde=True, ax=axes[0],
                 line_kws={"lw": 2, "color": "#ff6584"})
    axes[0].set_title("6.1 — Developer App Count Distribution",
                      fontweight="bold")
    axes[0].set_xlabel("Number of Apps Published (log₁₀ scale)")
    axes[0].set_ylabel("Number of Developers")
    axes[0].set_xticks([0, 1, 2, 3])
    axes[0].set_xticklabels(["1", "10", "100", "1K"])

    thresholds = [1, 2, 5, 10, 20, 50, 100]
    pcts = [(dev_counts["app_count"] > t).mean() * 100 for t in thresholds]
    axes[1].plot(thresholds, pcts, "o-", color="#6c63ff", lw=2, markersize=8)
    axes[1].fill_between(thresholds, pcts, alpha=0.2, color="#6c63ff")
    for t, p in zip(thresholds, pcts):
        axes[1].annotate(f"{p:.1f}%", (t, p),
                         textcoords="offset points", xytext=(5, 5),
                         fontsize=9, color="#c9d1d9")
    axes[1].set_title("6.1b — % of Developers with > N Apps", fontweight="bold")
    axes[1].set_xlabel("App Count Threshold")
    axes[1].set_ylabel("% of Developers")
    axes[1].set_xscale("log")
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("Developer App Portfolio Distribution",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/16_developer_distribution.png", **SAVE_KW)
    plt.show()

    print(f"Total unique developers  : {len(dev_counts):,}")
    print(f"Single-app developers    : {(dev_counts['app_count'] == 1).mean()*100:.1f}%")
    print(f"Developers with 10+ apps : {(dev_counts['app_count'] >= 10).mean()*100:.2f}%")


def plot_top_developers(top_devs):
    """
    Horizontal bar: top 20 most prolific developers with avg score annotation.

    Parameters
    ----------
    top_devs : pd.DataFrame  columns = ["developer", "app_count", "avg_score"]
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    palette = sns.color_palette("rocket_r", n_colors=len(top_devs))
    bars = ax.barh(top_devs["developer"][::-1], top_devs["app_count"][::-1],
                   color=palette, edgecolor="#30363d", linewidth=0.4)

    ax.set_title("6.2 — Top 20 Most Prolific Developers", fontweight="bold", pad=12)
    ax.set_xlabel("Number of Apps Published")

    for bar, (_, row) in zip(bars, top_devs[::-1].iterrows()):
        ax.text(row["app_count"] + 2,
                bar.get_y() + bar.get_height() / 2,
                f"{row['app_count']} apps  ⭐ {row['avg_score']:.2f}",
                va="center", ha="left", fontsize=9, color="#c9d1d9")

    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/17_top_developers.png", **SAVE_KW)
    plt.show()


def plot_developer_type_comparison(dev_type_data):
    """
    6.3 Violin: rating and installs split by developer type.

    Parameters
    ----------
    dev_type_data : pd.DataFrame  columns = ["dev_type", "score", "log_installs"]
    """
    ORDER   = ["Single-App (1)", "Boutique (2-5)", "Studio (6-20)", "Factory (20+)"]
    palette = sns.color_palette("husl", n_colors=4)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sns.violinplot(data=dev_type_data, x="dev_type", y="score",
                   order=ORDER, palette=palette, inner="quartile", cut=0, ax=axes[0])
    axes[0].set_title("6.3a — Rating by Developer Type", fontweight="bold")
    axes[0].set_xlabel("Developer Type")
    axes[0].set_ylabel("Score (1 – 5)")

    sns.violinplot(data=dev_type_data, x="dev_type", y="log_installs",
                   order=ORDER, palette=palette, inner="quartile", cut=0, ax=axes[1])
    axes[1].set_title("6.3b — Installs by Developer Type", fontweight="bold")
    axes[1].set_xlabel("Developer Type")
    axes[1].set_ylabel("Min Installs (log₁₀ scale)")

    plt.suptitle("6.3 — Single-App vs Multi-App Developer Performance",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/18_developer_type_comparison.png", **SAVE_KW)
    plt.show()


def plot_dev_quality_scatter(dev_qual):
    """
    Plotly scatter: developer portfolio size vs avg rating.
    Hover for developer name — great for discovering hidden high-quality publishers.

    Parameters
    ----------
    dev_qual : pd.DataFrame
        columns = ["developer", "app_count", "avg_score", "total_installs_M"]
    """
    r = dev_qual[["app_count", "avg_score"]].corr().iloc[0, 1]

    fig = px.scatter(
        dev_qual, x="app_count", y="avg_score",
        size="total_installs_M", size_max=40,
        color="avg_score", color_continuous_scale="RdYlGn",
        hover_name="developer",
        hover_data={"app_count": True, "avg_score": ":.3f", "total_installs_M": ":.2f"},
        log_x=True,
        title=f"6.4 — Developer: # Apps vs Avg Rating | Bubble = Total Installs | r={r:.3f}",
        labels={"app_count": "Number of Apps (log scale)", "avg_score": "Average Rating"},
        height=550,
    )
    fig.add_hline(y=4.0, line_dash="dot", line_color="#ffd700", opacity=0.7,
                  annotation_text="4.0★ quality threshold", annotation_position="right")
    fig.update_layout(title_font_size=14, coloraxis_colorbar_title="Avg Score")
    fig.show()

    print(f"Correlation (# apps vs avg score): r = {r:.4f}")


# =============================================================================
# SECTION 7 — BUSINESS INSIGHTS
# =============================================================================

def plot_opportunity_gap(opp_data):
    """
    Plotly bubble chart: category competition (x) vs demand (y).
    Colour-coded quadrants reveal market opportunities.

    Parameters
    ----------
    opp_data : pd.DataFrame
        columns = ["genre", "app_count", "avg_installs_M", "total_installs_B",
                   "avg_score", "quadrant"]
    """
    from IPython.display import display as ipy_display

    COLOR_MAP = {
        "🟢 Opportunity (Low competition, High demand)":     "#3fb950",
        "🔴 Saturated (High competition, High demand)":      "#da3633",
        "🟡 Niche (Low competition, Low demand)":            "#d29922",
        "⚪ Crowded & Weak (High competition, Low demand)":  "#8b949e",
    }
    med_count    = opp_data["app_count"].median()
    med_installs = opp_data["avg_installs_M"].median()

    fig = px.scatter(
        opp_data, x="app_count", y="avg_installs_M",
        size="total_installs_B", size_max=80,
        color="quadrant", color_discrete_map=COLOR_MAP,
        hover_name="genre",
        hover_data={"app_count": True, "avg_installs_M": ":.2f", "avg_score": ":.2f"},
        title="7.2 — Market Opportunity Gap: Category Competition vs Install Demand",
        labels={"app_count": "Number of Apps (Competition)",
                "avg_installs_M": "Avg Installs Per App (Demand, M)"},
        log_x=True, text="genre", height=650,
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.add_hline(y=med_installs, line_dash="dash", line_color="#ffffff", opacity=0.35)
    fig.add_vline(x=med_count,    line_dash="dash", line_color="#ffffff", opacity=0.35)
    fig.update_layout(title_font_size=15, legend_title_text="Quadrant")
    fig.show()

    print("\n🟢 OPPORTUNITY categories (low competition, high avg installs):")
    opportunity = (opp_data[opp_data["quadrant"].str.startswith("🟢")]
                   .sort_values("avg_installs_M", ascending=False))
    ipy_display(
        opportunity[["genre", "app_count", "avg_installs_M", "avg_score"]]
        .rename(columns={"genre": "Category", "app_count": "# Apps",
                          "avg_installs_M": "Avg Installs (M)", "avg_score": "Avg Score"})
    )


def plot_monetization_tiers(pivot_pct):
    """
    Stacked bar of monetization-model % by install tier.

    Parameters
    ----------
    pivot_pct : pd.DataFrame
        Index = ordered tier labels, columns = model names, values = % of apps in tier
    """
    MONO_COLORS = {
        "Free + IAP + Ads": "#6c63ff",
        "Free + IAP":        "#f0883e",
        "Free + Ads":        "#3fb950",
        "Free Only":         "#58a6ff",
        "Paid":              "#da3633",
    }
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(pivot_pct))

    for model, color in MONO_COLORS.items():
        if model in pivot_pct.columns:
            values = pivot_pct[model].values
            bars = ax.bar(pivot_pct.index, values, bottom=bottom,
                          label=model, color=color, edgecolor=BG, linewidth=0.4)
            for bar, val in zip(bars, values):
                if val > 5:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_y() + bar.get_height() / 2,
                            f"{val:.0f}%", ha="center", va="center",
                            fontsize=8.5, color=BG, fontweight="bold")
            bottom += values

    ax.set_title("7.3 — Monetization Model Distribution by Install Tier",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Install Tier")
    ax.set_ylabel("% of Apps in Tier")
    ax.set_ylim(0, 100)
    ax.legend(title="Monetization Model", bbox_to_anchor=(1.01, 1),
              borderaxespad=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{SAVE_DIR}/19_monetization_tiers.png", **SAVE_KW)
    plt.show()


def plot_category_bubble(cat_overview):
    """
    Plotly mega bubble chart: every category plotted as a bubble.
    x=avg score, y=avg installs, size=total installs, colour=% free.
    Hover for full breakdown — the definitive category overview.

    Parameters
    ----------
    cat_overview : pd.DataFrame
        columns = ["genre", "app_count", "avg_installs_M", "avg_score",
                   "total_installs_B", "pct_free", "pct_iap"]
    """
    fig = px.scatter(
        cat_overview, x="avg_score", y="avg_installs_M",
        size="total_installs_B", size_max=90,
        color="pct_free", color_continuous_scale="RdYlGn",
        hover_name="genre",
        hover_data={"app_count": True, "avg_installs_M": ":.2f",
                    "avg_score": ":.3f", "pct_free": ":.1f",
                    "pct_iap": ":.1f", "total_installs_B": ":.2f"},
        text="genre",
        title="7.4 — Category Overview: Rating vs Avg Installs | Bubble=Total Installs | Color=% Free",
        labels={"avg_score": "Average Rating",
                "avg_installs_M": "Avg Installs Per App (Millions)",
                "pct_free": "% Free Apps"},
        height=700,
    )
    fig.update_traces(textposition="top center", textfont_size=8)
    fig.update_layout(title_font_size=14, coloraxis_colorbar_title="% Free")
    fig.show()
