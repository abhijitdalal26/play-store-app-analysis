"""Section 3 — Meet the Market: every real app in the 2026 catalogue, not a category average."""
import numpy as np
import plotly.graph_objects as go

from analysis import data_prep as dp
from analysis.charts import save_interactive, PRIMARY, OLD


def build():
    apps = dp.new_apps().dropna(subset=["score", "min_installs"]).copy()
    apps["log_installs"] = np.log10(apps["min_installs"].clip(lower=1))

    indie = apps[~apps["is_big_tech"]]
    giants = apps[apps["is_big_tech"]]

    def hover_text(df):
        return [
            f"<b>{t}</b><br>{g} · {d}<br>Installs: {i:,.0f}<br>Rating: {s:.2f}★"
            for t, g, d, i, s in zip(df["title"], df["genre"], df["developer"],
                                      df["min_installs"], df["score"])
        ]

    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=indie["log_installs"], y=indie["score"], mode="markers",
        marker=dict(size=6, color=PRIMARY, opacity=0.5, line=dict(width=0)),
        name=f"Independent developers ({len(indie):,} apps)",
        text=hover_text(indie), hovertemplate="%{text}<extra></extra>",
    ))
    fig.add_trace(go.Scattergl(
        x=giants["log_installs"], y=giants["score"], mode="markers",
        marker=dict(size=10, color=OLD, symbol="diamond", opacity=0.9, line=dict(width=0.5, color="white")),
        name=f"Big tech / pre-installed ({len(giants):,} apps)",
        text=hover_text(giants), hovertemplate="%{text}<extra></extra>",
    ))
    tickvals = [3, 4, 5, 6, 7, 8, 9]
    fig.update_xaxes(title_text="Installs (log scale)", tickvals=tickvals,
                      ticktext=[f"{10**v:,.0f}" for v in tickvals])
    fig.update_yaxes(title_text="Star rating", range=[0.8, 5.05])
    fig.update_layout(
        title="Every App in the 2026 Catalogue — Hover Any Dot for the Real Name",
        height=640, legend=dict(orientation="h", y=-0.16),
    )
    path = save_interactive(fig, "m03_app_explorer")

    pct_bt_apps = len(giants) / len(apps) * 100
    pct_bt_installs = giants["min_installs"].sum() / apps["min_installs"].sum() * 100

    return [{
        "id": "app-explorer",
        "kicker": "Part 3 · Meet the Market",
        "title": "11,176 real apps, not a category average",
        "narrative": [
            "Every chart so far in this report aggregates up to the category level. This one "
            "doesn't — it's every single app in the live 2026 scrape, one dot each, positioned by "
            "how many people installed it and how it's currently rated. Nothing is text-labeled on "
            "the chart itself; hover any dot to see the real app name, its developer, and its "
            "category. That trade — no static labels — is what makes it possible to look at all "
            "11,176 apps at once instead of a top-20 list.",
            f"The amber diamonds are big tech and pre-installed publishers — Google, Meta, Samsung, "
            f"Microsoft, and similar — flagged separately because they aren't real competition for a "
            f"new developer; they ship on the phone before day one, or ride a billion-user platform "
            f"most indie developers will never have access to. They're only "
            f"<strong>{pct_bt_apps:.1f}%</strong> of the apps in this catalogue but "
            f"<strong>{pct_bt_installs:.0f}%</strong> of all installs — which is exactly why they're "
            "excluded from every competition and opportunity metric elsewhere in this report (market "
            "landscape, developer concentration, and the closing opportunity table). Follow the green "
            "dots; that's the market an indie developer is actually competing in.",
        ],
        "figures": [
            {"type": "interactive", "path": path,
             "caption": "Green = independent developers. Amber diamonds = big tech / pre-installed. Hover any point for the app name."},
        ],
    }]
