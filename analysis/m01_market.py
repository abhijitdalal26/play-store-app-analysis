"""Section 1 — Market Landscape: how big is the store and where do the apps live."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from analysis import data_prep as dp
from analysis.charts import save_static, save_interactive, thousands, PRIMARY, OLD, GREY


def _opportunity_trace(df, name, color, visible, min_apps):
    df = df[df["app_count"] >= min_apps].copy()
    df["cr3_pct"] = (df["cr3_share"] * 100).round(1)
    sizes = np.clip(df["cr3_pct"], 4, None).to_numpy(dtype=float)
    hover = [
        f"<b>{g}</b><br>Competing apps: {a:,.0f}<br>Median installs: {m:,.0f}<br>Top-3 install share: {c:.1f}%"
        for g, a, m, c in zip(df["genre"], df["app_count"], df["median_installs"], df["cr3_pct"])
    ]
    return go.Scatter(
        x=df["app_count"], y=df["median_installs"],
        mode="markers+text", text=df["genre"], textposition="top center", textfont=dict(size=10),
        marker=dict(size=sizes, sizemode="area", sizeref=2. * sizes.max() / (44. ** 2), sizemin=4,
                    color=color, opacity=0.75, line=dict(width=1, color="white")),
        name=name, visible=visible,
        hovertext=hover, hoverinfo="text",
    )


def build():
    sections = []
    old_g = dp.old_genre_stats()
    old_g_indie = dp.old_genre_stats_indie()
    new_g_indie = dp.new_genre_stats_indie()
    old_head = dp.old_headline_stats().iloc[0]
    bt_share = dp.old_bigtech_share_by_genre()

    # ── Chart 1: category volume, old dataset (static horizontal bars, everyone included) ──
    top20 = old_g.nlargest(20, "app_count")
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(top20["genre"][::-1], top20["app_count"][::-1], color=OLD)
    ax.set_title("Where the Apps Live — Category Volume (2022 catalogue, 3.45M apps)")
    ax.set_xlabel("Number of apps")
    thousands(ax, "x")
    fig.tight_layout()
    p1 = save_static(fig, "m01_category_volume_2022")

    # ── Chart 1b: big-tech install share by category — sets up why the toggle below matters ──
    bt_top = bt_share.nlargest(15, "pct_big_tech_installs")
    fig1b, ax1b = plt.subplots(figsize=(9, 7))
    ax1b.barh(bt_top["genre"][::-1], bt_top["pct_big_tech_installs"][::-1], color="#8A8A8A")
    ax1b.set_xlim(0, 100)
    ax1b.set_xlabel("Share of category installs held by big tech / pre-installed publishers (%)")
    ax1b.set_title("Where Big Tech Already Owns the Category (2022 catalogue)")
    fig1b.tight_layout()
    p1b = save_static(fig1b, "m01_bigtech_share")

    # ── Chart 2: opportunity matrix — both views live in the chart, toggled via the legend ──
    fig2 = go.Figure()
    fig2.add_trace(_opportunity_trace(old_g, "All apps (incl. big tech)", GREY, True, 3000))
    fig2.add_trace(_opportunity_trace(old_g_indie, "Indie developers only", PRIMARY, "legendonly", 3000))
    fig2.update_xaxes(type="log", title_text="Number of competing apps")
    fig2.update_yaxes(type="log", title_text="Median installs (demand)")
    fig2.update_layout(
        title="The Opportunity Matrix — Competition vs. Demand vs. Monopoly (2022)"
              "<br><sup>Bubble size = top-3 install share (CR3). Click a legend entry to toggle it, double-click to isolate.</sup>",
        height=580,
        legend=dict(title=dict(text="Click to show/hide")),
    )
    p2 = save_interactive(fig2, "m01_opportunity_matrix", hover_only_labels=True)

    # ── Chart 3: 2026 category volume vs 2022, indie-only share comparison ──
    old_share = (old_g_indie.set_index("genre")["app_count"] / old_g_indie["app_count"].sum() * 100)
    new_share = (new_g_indie.set_index("genre")["app_count"] / new_g_indie["app_count"].sum() * 100)
    shift = pd.DataFrame({"2022 share %": old_share, "2026 share %": new_share}).dropna()
    shift["delta"] = shift["2026 share %"] - shift["2022 share %"]
    movers = pd.concat([shift.nlargest(6, "delta"), shift.nsmallest(6, "delta")]).sort_values("delta")

    fig3, ax3 = plt.subplots(figsize=(9, 7))
    colors = [PRIMARY if v > 0 else OLD for v in movers["delta"]]
    ax3.barh(movers.index, movers["delta"], color=colors)
    ax3.axvline(0, color="#444", lw=0.8)
    ax3.set_title("Category Share Shift Among Indie Developers: 2022 → 2026")
    ax3.set_xlabel("Change in share of indie-listed apps (percentage points)")
    fig3.tight_layout()
    p3 = save_static(fig3, "m01_category_shift")

    n_apps = int(old_head["n_apps"])
    n_genres = int(old_head["n_genres"])
    top_genre = old_g.iloc[0]
    biggest_mover_up = shift["delta"].idxmax()
    biggest_mover_down = shift["delta"].idxmin()
    most_owned = bt_top.iloc[0]

    sections.append({
        "id": "market-landscape",
        "kicker": "Part 1 · Market Landscape",
        "title": "A store of 3.45 million apps, and a handful of categories that run it",
        "narrative": [
            f"The 2022 catalogue counts <strong>{n_apps:,} apps</strong> spread across "
            f"<strong>{n_genres} categories</strong> — but the distribution is nowhere close to even. "
            f"<strong>{top_genre['genre']}</strong> alone carries {int(top_genre['app_count']):,} apps, "
            "and the top handful of categories (Education, Entertainment, Music & Audio, Business, "
            "Tools) absorb a disproportionate share of everything ever published.",
            "Raw app counts include everyone, including publishers that were never real competition "
            f"to begin with. In <strong>{most_owned['genre']}</strong>, big tech and pre-installed "
            f"publishers alone account for {most_owned['pct_big_tech_installs']:.0f}% of all installs "
            "— one or two players with an unfair structural head start, not a crowded market.",
            "The chart below shows the full, unfiltered store by default — every publisher, nothing "
            "held back — plotted on three axes at once: how many apps are fighting for attention "
            "(x-axis), how much demand exists per app (y-axis, log scale), and how concentrated that "
            "demand is in the hands of the top 3 apps (bubble size). Click <strong>\"Indie developers "
            "only\"</strong> in the legend to swap in the big-tech-excluded view — the same chart, "
            "the same axes, filtered to the competition an independent developer can actually contest. "
            "Every chart later in this report that talks about 'competition' or 'opportunity' offers "
            "the same toggle.",
        ],
        "figures": [
            {"type": "static", "path": p1, "caption": "Top 20 categories by app count, 2022 catalogue (all publishers)."},
            {"type": "static", "path": p1b,
             "caption": "Categories where big tech / pre-installed publishers already hold most of the installs — the reason the toggle below matters."},
            {"type": "interactive", "path": p2,
             "caption": "Defaults to all publishers. Click the legend to switch to indie-only, or to compare both at once."},
        ],
    })

    sections.append({
        "id": "category-shift",
        "kicker": "Part 1 · Market Landscape",
        "title": f"Four years on: {biggest_mover_up} is eating share, {biggest_mover_down} is shrinking",
        "narrative": [
            "Comparing each category's share of indie listings in 2022 against its share of the fresh "
            "2026 scrape isolates where independent publishing activity is actually moving, "
            "independent of the size difference between the two datasets. This one is indie-only by "
            "design rather than by default — a pre-installed giant relisting an app doesn't reflect "
            "'momentum' in any meaningful sense, so including it would just be noise.",
            f"<strong>{biggest_mover_up}</strong> gained the most relative share among indie "
            f"developers, while <strong>{biggest_mover_down}</strong> lost the most — a signal worth "
            "cross-checking against the monetization and freshness sections later in this report "
            "before drawing conclusions.",
        ],
        "figures": [
            {"type": "static", "path": p3, "caption": "Biggest gainers and losers in indie category share, 2022 → 2026."},
        ],
    })
    return sections
