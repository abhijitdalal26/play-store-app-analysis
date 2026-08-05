"""
Shared visual identity for every chart in the report — one palette, one
typographic voice, one set of helpers for saving static (PNG) and
interactive (Plotly HTML fragment) figures.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.io as pio

ROOT = Path(__file__).resolve().parent
FIG_DIR = ROOT / "figures"
INT_DIR = ROOT / "interactive"
FIG_DIR.mkdir(exist_ok=True)
INT_DIR.mkdir(exist_ok=True)

# ── Palette ─────────────────────────────────────────────────────────────
INK = "#1B1F3B"
PAPER = "#FBFAF7"
PRIMARY = "#2F6F4F"      # deep green  – 2026 / fresh data
OLD = "#B5772F"          # amber/rust  – 2022 / legacy data
CORAL = "#D65F5F"
BLUE = "#3B6FA0"
PURPLE = "#8457A3"
GOLD = "#D2A02A"
GREY = "#9A9A9A"

CATEGORICAL = [PRIMARY, OLD, BLUE, CORAL, PURPLE, GOLD, "#4FA3A0", "#C2708C"]
DIVERGING = "RdYlGn"
SEQ_GREEN = "Greens"

sns.set_theme(style="whitegrid", rc={
    "axes.facecolor": PAPER,
    "figure.facecolor": PAPER,
    "axes.edgecolor": "#DEDAD0",
    "grid.color": "#E7E3D8",
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "Helvetica"],
})

PLOTLY_LAYOUT = dict(
    font=dict(family="Segoe UI, Arial, sans-serif", color=INK, size=13),
    plot_bgcolor=PAPER,
    paper_bgcolor=PAPER,
    margin=dict(l=60, r=30, t=60, b=50),
    hoverlabel=dict(bgcolor="white", font_size=12),
)


def thousands(ax, axis="y"):
    fmt = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def save_static(fig, name, dpi=160):
    fp = FIG_DIR / f"{name}.png"
    fig.savefig(fp, dpi=dpi, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    return f"figures/{name}.png"


def save_interactive(fig, name, hover_only_labels=False):
    fig.update_layout(**PLOTLY_LAYOUT)
    fp = INT_DIR / f"{name}.html"
    pio.write_html(fig, fp, include_plotlyjs="cdn", full_html=False, config={"displaylogo": False})
    if hover_only_labels:
        _strip_labels_on_hover_capable_devices(fp)
    return f"interactive/{name}.html"


def _strip_labels_on_hover_capable_devices(fp):
    """Bubble/keyword charts ship with on-chart text labels (mode='markers+text') so touch
    devices, which can't hover, can still read them. On a mouse-driven laptop/desktop that
    text just clutters a dense chart when the tooltip already carries it — this snippet
    detects real hover capability at load time and switches those traces back to
    marker-only, deferring to the tooltip instead."""
    snippet = """
<script>
(function() {
  function stripLabelsIfHoverCapable() {
    var hoverCapable = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (!hoverCapable) return;
    document.querySelectorAll('.plotly-graph-div').forEach(function(gd) {
      if (!gd.data) return;
      var idx = [];
      gd.data.forEach(function(tr, i) { if (tr.text && tr.mode && tr.mode.indexOf('text') !== -1) idx.push(i); });
      if (idx.length) Plotly.restyle(gd, {mode: 'markers'}, idx);
    });
  }
  window.addEventListener('load', function() { setTimeout(stripLabelsIfHoverCapable, 30); });
})();
</script>
"""
    with fp.open("a", encoding="utf-8") as f:
        f.write(snippet)
