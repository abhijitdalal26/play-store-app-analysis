import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Color Palette ───────────────────────────────────────────────────
PRIMARY   = "#3A86C8"   # Slate Blue
CORAL     = "#F15C5C"   # Coral Red
GREEN     = "#2EB872"   # Green
AMBER     = "#FFB84C"   # Amber
PURPLE    = "#A555EC"   # Purple
NAVY      = "#3F72AF"   # Navy
PALETTE   = [PRIMARY, CORAL, GREEN, AMBER, PURPLE, NAVY,
             "#E07BE0", "#45B7D1", "#FF6B6B", "#4ECDC4"]

LAYOUT_DEFAULTS = dict(
    font_family="Inter, Arial, sans-serif",
    plot_bgcolor="#FAFBFC",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=60, r=30, t=70, b=50),
)


# ════════════════════════════════════════════════════════════════════
# FIGURE 1 – Market Opportunity Matrix (Bubble Chart)
# ════════════════════════════════════════════════════════════════════
def plot_market_dynamics(apps, genre_counts):
    """Interactive bubble chart: Competition Volume × Median Downloads × Monopoly Index."""

    genre_metrics = apps.groupby('genre').agg(
        app_count=('app_id', 'count'),
        median_installs=('min_installs', 'median'),
        total_installs=('min_installs', 'sum')
    )
    cr3 = apps.groupby('genre').apply(
        lambda x: x.nlargest(3, 'min_installs')['min_installs'].sum() / x['min_installs'].sum(),
        include_groups=False
    ).fillna(0)
    genre_metrics['cr3'] = cr3

    top_15 = genre_counts.head(15).index
    df = genre_metrics.loc[top_15].reset_index()
    df['cr3_pct'] = (df['cr3'] * 100).round(1)

    fig = px.scatter(
        df,
        x='app_count',
        y='median_installs',
        size='cr3_pct',
        color='cr3_pct',
        text='genre',
        color_continuous_scale='RdYlBu_r',
        size_max=55,
        hover_data={
            'genre': True,
            'app_count': ':,',
            'median_installs': ':,.0f',
            'cr3_pct': ':.1f'
        },
        labels={
            'app_count': 'Number of Apps',
            'median_installs': 'Median Installs',
            'cr3_pct': 'Monopoly Index (CR3 %)'
        },
    )
    fig.update_traces(textposition='top center', textfont_size=10)
    fig.update_yaxes(type='log')
    fig.update_layout(
        title='Market Opportunity Matrix: Competition vs. Downloads vs. Monopoly',
        **LAYOUT_DEFAULTS,
        coloraxis_colorbar_title='CR3 %',
        height=550,
    )
    fig.show()


# ════════════════════════════════════════════════════════════════════
# FIGURE 2 – Rating Distribution Ridges (Box + Violin)
# ════════════════════════════════════════════════════════════════════
def plot_rating_density_ridges(apps, genre_counts):
    """Interactive violin chart showing rating distributions across top 8 genres."""

    top_8 = genre_counts.head(8).index
    df = apps[apps['genre'].isin(top_8)][['genre', 'score']].dropna()
    # Order genres by volume (most apps first)
    df['genre'] = pd.Categorical(df['genre'], categories=top_8, ordered=True)

    fig = px.violin(
        df,
        y='genre',
        x='score',
        color='genre',
        color_discrete_sequence=PALETTE,
        orientation='h',
        box=True,
        points=False,
        labels={'score': 'Rating Score (Stars)', 'genre': ''},
    )
    fig.update_layout(
        title='User Sentiment: Rating Distributions across Top 8 Genres',
        showlegend=False,
        xaxis_range=[1, 5],
        **LAYOUT_DEFAULTS,
        height=500,
    )
    fig.show()


# ════════════════════════════════════════════════════════════════════
# FIGURE 3 – Monetization Model Split (Stacked Bar)
# ════════════════════════════════════════════════════════════════════
def plot_monetization_mix(apps, genre_counts):
    """Interactive 100% stacked bar: monetization models per genre."""

    top_10 = genre_counts.head(10).index
    subset = apps[apps['genre'].isin(top_10)].copy()

    def monetization_label(row):
        if not row['free']:
            return 'Paid Premium'
        if row['ad_supported'] and row['in_app_purchases']:
            return 'Hybrid (Ads + IAP)'
        if row['ad_supported']:
            return 'Ad-Supported Only'
        if row['in_app_purchases']:
            return 'IAP Only'
        return 'Purely Free'

    subset['model'] = subset.apply(monetization_label, axis=1)

    ct = pd.crosstab(subset['genre'], subset['model'], normalize='index') * 100
    order = ['Purely Free', 'Ad-Supported Only', 'IAP Only', 'Hybrid (Ads + IAP)', 'Paid Premium']
    ct = ct.reindex(columns=order).fillna(0)

    colors = {
        'Purely Free': PURPLE,
        'Ad-Supported Only': AMBER,
        'IAP Only': PRIMARY,
        'Hybrid (Ads + IAP)': GREEN,
        'Paid Premium': CORAL,
    }

    fig = go.Figure()
    for col in order:
        fig.add_trace(go.Bar(
            y=ct.index,
            x=ct[col],
            name=col,
            orientation='h',
            marker_color=colors[col],
            hovertemplate='%{y}<br>' + col + ': %{x:.1f}%<extra></extra>',
        ))

    fig.update_layout(
        barmode='stack',
        title='Revenue Architecture: Monetization Models across Top 10 Genres',
        xaxis_title='Share of Applications (%)',
        yaxis_title='',
        legend_title='Monetization Strategy',
        **LAYOUT_DEFAULTS,
        height=480,
    )
    fig.show()


# ════════════════════════════════════════════════════════════════════
# FIGURE 4 – Publisher Landscape (Lorenz + Giants vs Indies scatter)
# ════════════════════════════════════════════════════════════════════
def plot_publisher_landscape(dev_portfolio, multi_app_indies, solo_hit_indies, gini_coeff):
    """Two-panel interactive chart: Lorenz Curve + Giants vs. Indie Powerhouses."""

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f'Lorenz Curve (Gini = {gini_coeff:.3f})',
            'Giants vs. Indie Powerhouses'
        ],
        horizontal_spacing=0.1,
    )

    # ── Left: Lorenz Curve ──
    sorted_inst = np.sort(dev_portfolio['total_installs'].values)
    n = len(sorted_inst)
    cum_pct = np.cumsum(sorted_inst) / sorted_inst.sum()
    x_vals = np.linspace(0, 1, n)

    fig.add_trace(go.Scatter(
        x=x_vals, y=x_vals,
        mode='lines', line=dict(dash='dash', color='gray'),
        name='Perfect Equality',
        hoverinfo='skip',
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=x_vals, y=cum_pct,
        mode='lines', line=dict(color=PRIMARY, width=2),
        fill='tonexty', fillcolor='rgba(58,134,200,0.12)',
        name=f'Lorenz (Gini={gini_coeff:.3f})',
    ), row=1, col=1)

    fig.update_xaxes(title_text='Cumulative Share of Developers', row=1, col=1)
    fig.update_yaxes(title_text='Cumulative Share of Installs', row=1, col=1)

    # ── Right: Scatter ──
    plot_devs = dev_portfolio[
        dev_portfolio['avg_score'].notna() & (dev_portfolio['total_installs'] > 0)
    ].copy()
    giants = plot_devs[plot_devs['is_giant']]
    indies = plot_devs[~plot_devs['is_giant']]

    # Non-giants
    fig.add_trace(go.Scatter(
        x=indies['app_count'],
        y=indies['avg_score'],
        mode='markers',
        marker=dict(
            size=np.clip(np.log10(indies['total_installs'] + 1) * 4, 4, 30),
            color=np.log10(indies['total_installs'] + 1),
            colorscale='Viridis',
            opacity=0.5,
            line=dict(width=0.5, color='white'),
        ),
        name='Indie / Mid-Sized',
        text=indies['developer'],
        hovertemplate='%{text}<br>Apps: %{x}<br>Avg Score: %{y:.2f}<extra></extra>',
    ), row=1, col=2)

    # Giants
    fig.add_trace(go.Scatter(
        x=giants['app_count'],
        y=giants['avg_score'],
        mode='markers',
        marker=dict(
            size=12, color='#888888', symbol='x',
            line=dict(width=1, color='#555555'),
        ),
        name='Tech Giants',
        text=giants['developer'],
        hovertemplate='%{text}<br>Apps: %{x}<br>Avg Score: %{y:.2f}<extra></extra>',
    ), row=1, col=2)

    # Annotate top indie powerhouses
    for _, row in multi_app_indies.head(3).iterrows():
        fig.add_annotation(
            x=np.log10(row['app_count']),
            y=row['avg_score'],
            text=row['developer'],
            showarrow=True, arrowhead=2,
            font=dict(size=10, color=CORAL),
            xref='x2', yref='y2',
        )

    fig.update_xaxes(type='log', title_text='App Portfolio Count (log)', row=1, col=2)
    fig.update_yaxes(range=[1, 5.2], title_text='Average Rating', row=1, col=2)

    fig.update_layout(
        title='Publisher Landscape: Installation Inequality & Indie Powerhouses',
        **LAYOUT_DEFAULTS,
        height=480,
        width=1050,
        showlegend=True,
        legend=dict(x=0.01, y=-0.12, orientation='h'),
    )
    fig.show()


# ════════════════════════════════════════════════════════════════════
# FIGURE 5 – Regional Demand Heatmap
# ════════════════════════════════════════════════════════════════════
def plot_regional_heatmap(country_merged, top_15_genres):
    """Interactive heatmap: Log-scale median installs by Genre × Country."""

    pivot = country_merged.pivot_table(
        index='genre', columns='country',
        values='min_installs', aggfunc='median',
    ).fillna(0)

    filtered = pivot.loc[top_15_genres.intersection(pivot.index)]
    log_vals = np.log10(filtered + 1)

    fig = px.imshow(
        log_vals,
        color_continuous_scale='YlGnBu',
        aspect='auto',
        labels=dict(x='Country', y='Genre', color='Log₁₀(Median Installs+1)'),
    )
    fig.update_layout(
        title='Regional Penetration Matrix: Downloads by Genre & Country',
        **LAYOUT_DEFAULTS,
        height=550,
    )
    fig.show()


# ════════════════════════════════════════════════════════════════════
# FIGURE 6 – Keyword Discovery Dot Plot
# ════════════════════════════════════════════════════════════════════
def plot_keyword_discovery(discovery, apps):
    """Interactive dot plot: keyword installs vs. rating vs. app density."""

    if 'keyword' not in discovery.columns or discovery['keyword'].notna().sum() == 0:
        print("Keyword analysis skipped – keyword column contains no values.")
        return

    merged = discovery.merge(apps[['app_id', 'score', 'min_installs']], on='app_id', how='inner')
    kw = merged.groupby('keyword').agg(
        median_installs=('min_installs', 'median'),
        avg_score=('score', 'mean'),
        app_count=('app_id', 'count'),
    ).reset_index()

    kw = kw[kw['app_count'] >= 5].sort_values('app_count', ascending=False).head(20)

    fig = px.scatter(
        kw,
        x='median_installs',
        y='keyword',
        size='app_count',
        color='avg_score',
        color_continuous_scale='RdYlGn',
        size_max=35,
        hover_data={
            'keyword': True,
            'median_installs': ':,.0f',
            'avg_score': ':.2f',
            'app_count': True,
        },
        labels={
            'median_installs': 'Median Installs',
            'keyword': '',
            'avg_score': 'Avg Rating',
            'app_count': 'Apps Surfaced',
        },
    )
    fig.update_xaxes(type='log')
    fig.update_layout(
        title='Keyword Discovery Landscape: Installs vs. Rating vs. App Density',
        **LAYOUT_DEFAULTS,
        height=550,
        coloraxis_colorbar_title='Avg Rating',
    )
    fig.show()
