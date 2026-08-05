"""Section 9 — Opportunity Synthesis: combine every signal into a single ranked shortlist."""
import numpy as np
import pandas as pd

from analysis import data_prep as dp


def _minmax(s):
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min())


def _score(genre_stats, min_apps):
    df = genre_stats[genre_stats["app_count"] >= min_apps].copy().set_index("genre")
    df["log_demand"] = np.log10(df["median_installs"].clip(lower=1))
    df["low_competition"] = 1 - _minmax(np.log10(df["app_count"]))
    df["low_monopoly"] = 1 - _minmax(df["cr3_share"])
    df["demand_score"] = _minmax(df["log_demand"])
    df["quality_bar"] = _minmax(df["avg_score"])
    df["opportunity_score"] = (
        0.35 * df["low_competition"] + 0.30 * df["demand_score"]
        + 0.20 * df["low_monopoly"] + 0.15 * (1 - df["quality_bar"])
    ) * 100
    return df.sort_values("opportunity_score", ascending=False).head(10)


def _rows(top10):
    rows_html = []
    for genre, r in top10.iterrows():
        rows_html.append(f"""
        <tr>
          <td class="cat-name">{genre}</td>
          <td>{int(r['app_count']):,}</td>
          <td>{r['median_installs']:,.0f}</td>
          <td>{r['avg_score']:.2f}</td>
          <td>{r['cr3_share']*100:.0f}%</td>
          <td><span class="score-pill">{r['opportunity_score']:.0f}</span></td>
        </tr>""")
    return "\n".join(rows_html)


def build():
    top10 = _score(dp.new_genre_stats_indie(), min_apps=20)
    winner = top10.index[0]
    runner_up = top10.index[1]

    return [{
        "id": "opportunity",
        "kicker": "Part 9 · Opportunity Synthesis",
        "title": "Where the numbers point, if you were shipping a new app this quarter",
        "narrative": [
            "Pulling every signal from this report into one score — competition density, demand per "
            "app, how monopolized the category is by its top 3 players, and how high the quality bar "
            "sits — surfaces a shortlist rather than a single answer. No category is a guaranteed win; "
            "this ranks where the <em>structural</em> conditions (crowding, concentration, demand) are "
            "most favorable, independent of whether you personally have the right idea or team for it. "
            "Big tech is excluded here for the same reason argued earlier in this report — checked "
            "against the full, unfiltered catalogue, the top of this ranking barely moves either way, "
            "which is itself a useful sanity check: these categories are genuinely indie-friendly, not "
            "just 'friendly because Google isn't in it.'",
            f"<strong>{winner}</strong> and <strong>{runner_up}</strong> top the list: enough proven "
            "demand to know people download in this space, without the extreme crowding or top-3 "
            "monopoly that defines categories like Games or Communication. That's a starting point for "
            "due diligence, not a substitute for it — go read the actual top apps in these categories "
            "before committing.",
        ],
        "table_html": f"""
        <div class="table-wrap">
        <table class="opp-table">
          <thead><tr>
            <th>Category</th><th>Apps</th><th>Median installs</th><th>Avg rating</th>
            <th>Top-3 share</th><th>Opportunity score</th>
          </tr></thead>
          <tbody>{_rows(top10)}</tbody>
        </table>
        </div>
        """,
        "figures": [],
    }]
