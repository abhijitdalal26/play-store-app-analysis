"""Section 6 — Developer Landscape: who actually owns the installs, and how much of that is big tech."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis import data_prep as dp
from analysis.charts import save_interactive, PRIMARY, OLD, CORAL, GREY


def gini(values):
    v = np.sort(np.asarray(values, dtype=float))
    v = v[v >= 0]
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    cum = np.cumsum(v)
    return (n + 1 - 2 * (cum.sum() / cum[-1])) / n


def lorenz_xy(values):
    v = np.sort(np.asarray(values, dtype=float))
    v = v[v >= 0]
    n = len(v)
    cum_pct = np.cumsum(v) / v.sum()
    x = np.linspace(0, 1, n)
    return x, cum_pct


def build():
    old_dev_all = dp.old_developer_portfolio()
    old_dev = dp.old_developer_portfolio_indie()
    new_dev_all = dp.new_developer_portfolio()
    new_dev = dp.new_developer_portfolio_indie()

    bt_installs_old = old_dev_all["total_installs"].sum() - old_dev["total_installs"].sum()
    bt_share_old = bt_installs_old / old_dev_all["total_installs"].sum() * 100
    bt_installs_new = new_dev_all["total_installs"].sum() - new_dev["total_installs"].sum()
    bt_share_new = bt_installs_new / new_dev_all["total_installs"].sum() * 100

    g_old_all, g_old_indie = gini(old_dev_all["total_installs"]), gini(old_dev["total_installs"])
    g_new_all, g_new_indie = gini(new_dev_all["total_installs"]), gini(new_dev["total_installs"])

    def lorenz_pair(values, col, color, name, legendgroup, showlegend, visible):
        x, y = lorenz_xy(values)
        idx = np.linspace(0, len(x) - 1, 2000).astype(int)
        rgb = {"grey": "154,154,154", "green": "47,111,79"}[color]
        return go.Scatter(
            x=x[idx], y=y[idx], mode="lines",
            line=dict(color=GREY if color == "grey" else PRIMARY, width=2),
            fill="tonexty", fillcolor=f"rgba({rgb},0.15)",
            name=name, legendgroup=legendgroup, showlegend=showlegend, visible=visible,
        )

    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        f"2022 (Gini: all {g_old_all:.2f} · indie {g_old_indie:.2f})",
        f"2026 (Gini: all {g_new_all:.2f} · indie {g_new_indie:.2f})"])
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash", color="gray"),
                              showlegend=False, hoverinfo="skip"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash", color="gray"),
                              showlegend=False, hoverinfo="skip"), row=1, col=2)
    fig.add_trace(lorenz_pair(old_dev_all["total_installs"], 1, "grey", "All developers",
                               "all", True, True), row=1, col=1)
    fig.add_trace(lorenz_pair(old_dev["total_installs"], 1, "green", "Indie developers only",
                               "indie", True, "legendonly"), row=1, col=1)
    fig.add_trace(lorenz_pair(new_dev_all["total_installs"], 2, "grey", "All developers",
                               "all", False, True), row=1, col=2)
    fig.add_trace(lorenz_pair(new_dev["total_installs"], 2, "green", "Indie developers only",
                               "indie", False, "legendonly"), row=1, col=2)
    fig.update_xaxes(title_text="Cumulative share of developers")
    fig.update_yaxes(title_text="Cumulative share of installs", row=1, col=1)
    fig.update_layout(
        title="Install Inequality Among Developers — Click the Legend to Isolate Indie",
        height=480, legend=dict(groupclick="togglegroup"),
    )
    p1 = save_interactive(fig, "m05_lorenz")

    # top developers by portfolio size — buttons swap between all-publisher and indie-only lists
    top_all = new_dev_all.sort_values("total_installs", ascending=False).head(15)
    top_indie = new_dev.sort_values("total_installs", ascending=False).head(15)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=top_all["total_installs"], y=top_all["developer"], orientation="h",
                           marker_color=GREY, text=[f"{v:,.0f}" for v in top_all["total_installs"]],
                           textposition="outside", visible=True))
    fig2.add_trace(go.Bar(x=top_indie["total_installs"], y=top_indie["developer"], orientation="h",
                           marker_color=PRIMARY, text=[f"{v:,.0f}" for v in top_indie["total_installs"]],
                           textposition="outside", visible=False))
    fig2.update_layout(
        title="Top 15 Developers by Total Installs (2026 catalogue)",
        xaxis_title="Total installs across portfolio", height=520,
        yaxis=dict(autorange="reversed"), margin=dict(l=210, t=90),
        updatemenus=[dict(
            type="buttons", direction="right", x=1, y=1.14, xanchor="right",
            buttons=[
                dict(label="All publishers", method="update",
                     args=[{"visible": [True, False]}, {"title": "Top 15 Developers by Total Installs — All Publishers (2026)"}]),
                dict(label="Indie only", method="update",
                     args=[{"visible": [False, True]}, {"title": "Top 15 Developers by Total Installs — Indie Only (2026)"}]),
            ],
        )],
    )
    p2 = save_interactive(fig2, "m05_top_developers")

    top1pct_old = old_dev.nlargest(max(1, len(old_dev) // 100), "total_installs")["total_installs"].sum() / old_dev["total_installs"].sum() * 100
    top1pct_new = new_dev.nlargest(max(1, len(new_dev) // 100), "total_installs")["total_installs"].sum() / new_dev["total_installs"].sum() * 100
    single_app_share_old = (old_dev["app_count"] == 1).mean() * 100
    single_app_share_new = (new_dev["app_count"] == 1).mean() * 100

    return [{
        "id": "developers",
        "kicker": "Part 6 · Developer Landscape",
        "title": f"Big tech holds {bt_share_new:.0f}% of 2026 installs — and even without them, it's still winner-take-most",
        "narrative": [
            f"Big tech and pre-installed publishers hold <strong>{bt_share_new:.0f}%</strong> of all "
            f"2026 installs ({bt_share_old:.0f}% in the 2022 archive) despite being a sliver of the "
            "developer count. Both charts below default to the full, unfiltered picture — everyone "
            "included — with an indie-only view one click away, so you can see exactly how much of "
            "that inequality is 'Google exists' versus a genuine indie winner-take-most dynamic.",
            f"Strip big tech out and the inequality barely moves: a Gini coefficient of "
            f"{g_old_indie:.2f} in 2022 and {g_new_indie:.2f} in 2026 among indie developers alone "
            f"(versus {g_old_all:.2f} / {g_new_all:.2f} with everyone included; 1.0 would mean one "
            f"developer owns every install). The top 1% of indie developers by portfolio account for "
            f"roughly {top1pct_old:.0f}% of indie installs in the archive and {top1pct_new:.0f}% in "
            "the fresh scrape — this is a real indie phenomenon, not just a big-tech artifact.",
            f"Most developers aren't trying to be the top 1%, either way: "
            f"{single_app_share_old:.0f}% of indie developers in the 2022 archive (and "
            f"{single_app_share_new:.0f}% in 2026) have shipped exactly one app. The realistic "
            "comparison for a new developer isn't 'the market average' — it's the long tail of other "
            "single-app indie publishers, most of whom never break out of low install counts "
            "regardless of category.",
        ],
        "figures": [
            {"type": "interactive", "path": p1, "caption": "Grey = every developer. Green = indie only (click the legend to toggle). The further the curve bows below the diagonal, the more installs are concentrated in fewer hands."},
            {"type": "interactive", "path": p2, "caption": "Buttons at top-right switch between the full publisher list and indie-only."},
        ],
    }]
