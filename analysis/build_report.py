"""Assembles every analysis module into one self-contained, portfolio-quality HTML report."""
from pathlib import Path
from datetime import datetime

from analysis import data_prep as dp
from analysis import m01_market, m02_evolution, m03_app_explorer, m03_quality, m04_monetization
from analysis import m05_developers, m06_freshness, m07_geo_discovery, m08_opportunity

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT.parent / "report"
REPORT_DIR.mkdir(exist_ok=True)


def hero_stats():
    old = dp.old_headline_stats().iloc[0]
    new = dp.new_apps()
    return [
        {"value": f"{int(old['n_apps']):,}", "label": "apps in the 2022 archive"},
        {"value": f"{len(new):,}", "label": "apps in the live 2026 scrape"},
        {"value": f"{int(old['n_developers']):,}", "label": "distinct developers, 2022"},
        {"value": f"{old['pct_free']*100:.0f}%", "label": "of the 2022 catalogue is free"},
    ]


def figure_html(fig):
    if fig["type"] == "static":
        return f"""
        <figure class="chart chart-static">
          <img src="../analysis/{fig['path']}" alt="{fig['caption']}" loading="lazy">
          <figcaption>{fig['caption']}</figcaption>
        </figure>"""
    else:
        iframe_src = f"../analysis/{fig['path']}"
        return f"""
        <figure class="chart chart-interactive">
          <iframe src="{iframe_src}" loading="lazy"></iframe>
          <figcaption>{fig['caption']} <span class="interactive-tag">interactive — hover &amp; zoom</span></figcaption>
        </figure>"""


def section_html(sec, index):
    paras = "".join(f"<p>{p}</p>" for p in sec.get("narrative", []))
    figs = "".join(figure_html(f) for f in sec.get("figures", []))
    table = sec.get("table_html", "")
    num = f"{index:02d}"
    return f"""
    <section class="story-section" id="{sec['id']}">
      <div class="section-index">{num}</div>
      <div class="section-body">
        <p class="kicker">{sec['kicker']}</p>
        <h2>{sec['title']}</h2>
        <div class="narrative">{paras}</div>
        {table}
        <div class="figure-stack">{figs}</div>
      </div>
    </section>"""


def build():
    all_sections = []
    all_sections += m01_market.build()
    all_sections += m02_evolution.build()
    all_sections += m03_app_explorer.build()
    all_sections += m03_quality.build()
    all_sections += m04_monetization.build()
    all_sections += m05_developers.build()
    all_sections += m06_freshness.build()
    all_sections += m07_geo_discovery.build()
    all_sections += m08_opportunity.build()

    hero = hero_stats()
    hero_html = "".join(
        f'<div class="stat"><div class="stat-value">{h["value"]}</div><div class="stat-label">{h["label"]}</div></div>'
        for h in hero
    )
    sections_html = "".join(section_html(s, i + 1) for i, s in enumerate(all_sections))

    toc_html = "".join(
        f'<a href="#{s["id"]}"><span class="toc-num">{i+1:02d}</span>{s["title"]}</a>'
        for i, s in enumerate(all_sections)
    )

    generated = datetime.now().strftime("%B %Y")

    html = TEMPLATE.format(
        hero_html=hero_html, sections_html=sections_html, toc_html=toc_html, generated=generated,
    )
    out = REPORT_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Google Play Store, Decoded — A Data Story</title>
<style>
  :root {{
    --ink: #1B1F3B;
    --paper: #FBFAF7;
    --paper-alt: #F3F0E7;
    --primary: #2F6F4F;
    --old: #B5772F;
    --line: #E4DFD1;
    --muted: #6B6858;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: "Georgia", "Iowan Old Style", serif;
    line-height: 1.65;
  }}
  h1, h2, h3, .kicker, .stat-label, .toc a, nav, .interactive-tag {{
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  }}
  a {{ color: var(--primary); }}

  /* ── Hero ───────────────────────────────────────────── */
  .hero {{
    min-height: 92vh; display: flex; flex-direction: column; justify-content: center;
    padding: 6vh 8vw; background:
      radial-gradient(circle at 15% 20%, rgba(47,111,79,0.10), transparent 45%),
      radial-gradient(circle at 85% 75%, rgba(181,119,47,0.10), transparent 45%),
      var(--paper);
    border-bottom: 1px solid var(--line);
  }}
  .eyebrow {{
    font-family: "Segoe UI", Arial, sans-serif; letter-spacing: 0.18em; text-transform: uppercase;
    font-size: 0.78rem; color: var(--old); font-weight: 600; margin-bottom: 1.2rem;
  }}
  .hero h1 {{
    font-size: clamp(2.4rem, 5.5vw, 4.4rem); margin: 0 0 1.2rem; line-height: 1.08; max-width: 18ch;
  }}
  .hero .lede {{ font-size: 1.25rem; max-width: 62ch; color: #3A3830; margin-bottom: 2.6rem; }}
  .stat-row {{ display: flex; flex-wrap: wrap; gap: 2.6rem; }}
  .stat-value {{
    font-family: "Segoe UI", Arial, sans-serif; font-size: 2.1rem; font-weight: 700; color: var(--primary);
  }}
  .stat-label {{ font-size: 0.85rem; color: var(--muted); max-width: 16ch; }}

  /* ── Table of contents ──────────────────────────────── */
  .toc {{ padding: 5vh 8vw; border-bottom: 1px solid var(--line); background: var(--paper-alt); }}
  .toc h3 {{ text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.85rem; color: var(--muted); margin-bottom: 1.4rem; }}
  .toc-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.6rem 2rem; }}
  .toc a {{
    display: flex; gap: 0.8rem; align-items: baseline; text-decoration: none; color: var(--ink);
    font-size: 0.98rem; padding: 0.35rem 0; border-bottom: 1px dotted transparent;
  }}
  .toc a:hover {{ border-bottom-color: var(--primary); color: var(--primary); }}
  .toc-num {{ font-weight: 700; color: var(--old); font-size: 0.85rem; }}

  /* ── Sections ───────────────────────────────────────── */
  .story-section {{
    display: grid; grid-template-columns: 90px 1fr; gap: 1.5rem;
    padding: 7vh 8vw; max-width: 1180px; margin: 0 auto; border-bottom: 1px solid var(--line);
  }}
  .section-index {{
    font-family: "Segoe UI", Arial, sans-serif; font-size: 3.2rem; font-weight: 800;
    color: var(--line); line-height: 1;
  }}
  .kicker {{
    text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.78rem; font-weight: 700;
    color: var(--old); margin-bottom: 0.6rem;
  }}
  .story-section h2 {{ font-size: clamp(1.5rem, 3vw, 2.1rem); margin: 0 0 1.3rem; max-width: 26ch; line-height: 1.25; }}
  .narrative p {{ font-size: 1.08rem; color: #2A2820; max-width: 72ch; margin: 0 0 1.1rem; }}
  .narrative strong {{ color: var(--primary); }}

  .figure-stack {{ display: flex; flex-direction: column; gap: 2.4rem; margin-top: 2.2rem; }}
  figure.chart {{ margin: 0; }}
  figure.chart img {{ width: 100%; border-radius: 6px; border: 1px solid var(--line); background: white; }}
  figure.chart iframe {{
    width: 100%; height: 560px; border: 1px solid var(--line); border-radius: 6px; background: white;
  }}
  figcaption {{
    font-family: "Segoe UI", Arial, sans-serif; font-size: 0.85rem; color: var(--muted);
    margin-top: 0.6rem; display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  }}
  .interactive-tag {{
    color: var(--primary); font-weight: 600; white-space: nowrap;
  }}

  /* ── Opportunity table ─────────────────────────────── */
  .table-wrap {{ overflow-x: auto; margin: 1.6rem 0; }}
  table.opp-table {{
    border-collapse: collapse; width: 100%; font-family: "Segoe UI", Arial, sans-serif;
    font-size: 0.92rem; min-width: 640px;
  }}
  table.opp-table th {{
    text-align: left; padding: 0.7rem 0.9rem; background: var(--ink); color: var(--paper);
    font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em;
  }}
  table.opp-table td {{ padding: 0.65rem 0.9rem; border-bottom: 1px solid var(--line); }}
  table.opp-table tr:nth-child(even) {{ background: var(--paper-alt); }}
  td.cat-name {{ font-weight: 600; }}
  .score-pill {{
    display: inline-block; background: var(--primary); color: white; border-radius: 20px;
    padding: 0.15rem 0.7rem; font-weight: 700;
  }}

  /* ── Footer ─────────────────────────────────────────── */
  footer {{
    padding: 6vh 8vw; text-align: center; color: var(--muted);
    font-family: "Segoe UI", Arial, sans-serif; font-size: 0.85rem;
  }}

  @media (max-width: 720px) {{
    .story-section {{ grid-template-columns: 1fr; }}
    .section-index {{ font-size: 1.6rem; }}
    figure.chart iframe {{ height: 420px; }}
  }}
</style>
</head>
<body>

  <header class="hero">
    <p class="eyebrow">A Data Story · Google Play Store 2022 → 2026</p>
    <h1>3.4 million apps chased the same download button. Almost all of them lost.</h1>
    <p class="lede">
      This report merges a 3.45-million-app archive of the Play Store from 2022 with a fresh,
      country-by-country scrape of 11,000+ live apps in 2026 to answer a practical question:
      structurally, where does opportunity actually sit on the store today — and where is it an
      illusion of size?
    </p>
    <div class="stat-row">{hero_html}</div>
  </header>

  <nav class="toc">
    <h3>In this report</h3>
    <div class="toc-grid">{toc_html}</div>
  </nav>

  <main>
    {sections_html}
  </main>

  <footer>
    Built from the 2022 tapivedotcom Play Store archive and a 2026 first-party scrape across ten
    country storefronts · Generated {generated}
  </footer>

</body>
</html>
"""


if __name__ == "__main__":
    out = build()
    print(f"Report written to {out}")
