import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Constants for Styling
PRIMARY_COLOR = "#3A86C8"   # Slate Blue
SECONDARY_COLOR = "#F15C5C" # Coral Red
ACCENT_COLOR = "#2EB872"    # Green
PALETTE = [PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR, "#FFB84C", "#A555EC", "#3F72AF"]

def plot_market_dynamics(apps, genre_counts):
    """
    Figure 1: Genre Market Dynamics (App Count vs. Median Installs vs. Concentration)
    """
    fig, ax = plt.subplots(figsize=(12, 7.5))

    # Calculate metrics per genre
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

    # Filter to top 15 genres by app volume to keep visual clean
    top_15_genres = genre_counts.head(15).index
    plot_data = genre_metrics.loc[top_15_genres].reset_index()

    # Multi-dimensional scatter
    scatter = ax.scatter(
        plot_data['app_count'], 
        plot_data['median_installs'], 
        s=plot_data['cr3'] * 1200, 
        c=plot_data['cr3'], 
        cmap="coolwarm", 
        alpha=0.8, 
        edgecolors="black", 
        linewidths=1.2
    )

    # Annotate genre names
    for idx, row in plot_data.iterrows():
        ax.annotate(
            row['genre'], 
            xy=(row['app_count'], row['median_installs']),
            xytext=(12, -4), 
            textcoords='offset points', 
            fontsize=9, 
            weight='bold'
        )

    # Colorbar for Concentration Ratio (CR3)
    cbar = fig.colorbar(scatter, ax=ax, label="Monopoly Concentration Index (CR3)")
    cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    cbar.set_ticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])

    ax.set_title("Market Opportunity Matrix: Competition Volume vs. Median Downloads & Monopoly Index", pad=15)
    ax.set_xlabel("Volume of Competition (Number of Apps)")
    ax.set_ylabel("Market Demand (Median Installs - Log Scale)")
    ax.set_yscale('log')
    ax.grid(True, which="both", ls="--", alpha=0.3)

    # Add size legend manually
    for size in [0.2, 0.5, 0.8]:
        ax.scatter([], [], s=size * 1200, c="gray", alpha=0.5, edgecolors="black", label=f"CR3 = {size*100:.0f}%")
    ax.legend(title="Monopoly dominance (CR3)", loc="upper right")

    plt.tight_layout()
    plt.show()


def plot_rating_density_ridges(apps, genre_counts):
    """
    Figure 2: Rating Density Ridges (KDE Distributions of top 8 Genres)
    """
    fig, axes = plt.subplots(8, 1, figsize=(10, 11), sharex=True)
    top_8_genres = genre_counts.head(8).index

    for i, genre in enumerate(top_8_genres):
        ax = axes[i]
        genre_data = apps[apps['genre'] == genre]['score'].dropna()
        sns.kdeplot(genre_data, fill=True, color=PALETTE[i % len(PALETTE)], alpha=0.6, ax=ax, lw=1.5)
        ax.set_xlim(1.0, 5.0)
        ax.set_ylabel("")
        ax.text(1.1, 0.15, genre, fontweight="bold", fontsize=11, color="#2B2D42")
        ax.patch.set_alpha(0)
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.grid(False)
        if i < 7:
            ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax.tick_params(axis='y', which='both', left=False, labelleft=False)

    fig.suptitle("User Sentiment Footprint: Rating Distributions across Top 8 Genres (Joyplot)", fontsize=15, y=0.98)
    axes[-1].set_xlabel("App Rating Score (Stars)")
    plt.tight_layout()
    plt.show()


def plot_monetization_mix(apps, genre_counts):
    """
    Figure 3: Monetization Mix (Ad-Supported, IAP, Hybrid, or Purely Free) Across Top 10 Genres
    """
    top_10_genres = genre_counts.head(10).index
    apps_top_10 = apps[apps['genre'].isin(top_10_genres)].copy()

    def get_monetization_model(row):
        if row['free'] == False:
            return 'Paid Premium'
        if row['ad_supported'] and row['in_app_purchases']:
            return 'Hybrid (Ads + IAP)'
        if row['ad_supported']:
            return 'Ad-Supported Only'
        if row['in_app_purchases']:
            return 'IAP Only'
        return 'Purely Free'

    apps_top_10['monetization_type'] = apps_top_10.apply(get_monetization_model, axis=1)

    # Create percentage crosstab
    monetization_crosstab = pd.crosstab(apps_top_10['genre'], apps_top_10['monetization_type'], normalize='index') * 100
    cols_order = ['Purely Free', 'Ad-Supported Only', 'IAP Only', 'Hybrid (Ads + IAP)', 'Paid Premium']
    monetization_crosstab = monetization_crosstab.reindex(columns=cols_order).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6.5))
    monetization_crosstab.plot(kind='barh', stacked=True, color=['#A555EC', '#FFB84C', PRIMARY_COLOR, ACCENT_COLOR, SECONDARY_COLOR], ax=ax, width=0.7)

    # Annotate percentages
    for p in ax.patches:
        width = p.get_width()
        if width > 5:
            x = p.get_x() + width / 2
            y = p.get_y() + p.get_height() / 2
            ax.annotate(f"{width:.0f}%", (x, y), ha='center', va='center', color='white', fontweight='bold', fontsize=9)

    ax.set_title("Revenue Architecture: Monetization Models across Top 10 Competitive Genres", pad=15)
    ax.set_xlabel("Share of Applications (%)")
    ax.set_ylabel("")
    ax.legend(title="Monetization Strategy", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


def plot_publisher_landscape(dev_portfolio, multi_app_indies, solo_hit_indies, gini_coeff):
    """
    Figure 4: Lorenz Curve & Giants vs. Indie Powerhouses Comparison
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

    # Left: Lorenz Curve
    sorted_installs = np.sort(dev_portfolio['total_installs'].values)
    n = len(sorted_installs)
    cum_installs = np.cumsum(sorted_installs)
    cum_installs_pct = cum_installs / cum_installs[-1]
    equality = np.linspace(0, 1, n)

    ax1.plot(equality, equality, label="Line of Perfect Equality", color="gray", linestyle="--")
    ax1.plot(np.linspace(0, 1, n), cum_installs_pct, label=f"Lorenz Curve (Gini = {gini_coeff:.3f})", color=PRIMARY_COLOR, lw=2)
    ax1.fill_between(np.linspace(0, 1, n), equality, cum_installs_pct, color=PRIMARY_COLOR, alpha=0.15)
    ax1.set_title("Inequality of App Installations (Lorenz Curve)", pad=12)
    ax1.set_xlabel("Cumulative Share of Developers (Sorted by Installs)")
    ax1.set_ylabel("Cumulative Share of Total Installs")
    ax1.legend(loc="upper left")

    # Right: Giants vs Indie Powerhouses Scatter Plot
    plot_devs = dev_portfolio[dev_portfolio['avg_score'].notna() & (dev_portfolio['total_installs'] > 0)].copy()
    giants_df = plot_devs[plot_devs['is_giant']]
    non_giants_df = plot_devs[~plot_devs['is_giant']]

    # Scatter for non-giants
    scatter = ax2.scatter(
        non_giants_df['app_count'], 
        non_giants_df['avg_score'], 
        s=np.log10(non_giants_df['total_installs']) * 40, 
        c=non_giants_df['total_installs'], 
        cmap="coolwarm", 
        alpha=0.6, 
        edgecolors="w", 
        linewidths=0.5, 
        label="Indie/Mid-Sized"
    )

    # Scatter for giants
    ax2.scatter(
        giants_df['app_count'], 
        giants_df['avg_score'], 
        s=np.log10(giants_df['total_installs']) * 40, 
        color="#888888", 
        marker="X", 
        alpha=0.8, 
        label="Tech Giants (Google/MS/Meta/etc)"
    )

    # Colorbar
    fig.colorbar(scatter, ax=ax2, label="Total Installations")

    # Annotate top multi-app indies
    for idx, row in multi_app_indies.head(4).iterrows():
        ax2.annotate(
            row['developer'], 
            xy=(row['app_count'], row['avg_score']),
            xytext=(5, 5), 
            textcoords='offset points', 
            fontsize=9, 
            weight='bold',
            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3, ec="orange")
        )

    # Annotate top solo hit indies
    for idx, row in solo_hit_indies.head(4).iterrows():
        ax2.annotate(
            row['developer'], 
            xy=(1, row['avg_score']),
            xytext=(15, -10), 
            textcoords='offset points', 
            fontsize=9, 
            arrowprops=dict(arrowstyle="->", color=SECONDARY_COLOR, lw=0.8),
            weight='bold'
        )

    ax2.set_xscale('log')
    ax2.set_xlim(0.8, dev_portfolio['app_count'].max() * 1.5)
    ax2.set_ylim(1.0, 5.2)
    ax2.set_title("Publisher Landscape: Giants vs. Indie Powerhouses", pad=12)
    ax2.set_xlabel("App Portfolio Count (Log Scale)")
    ax2.set_ylabel("Average App Rating (Score)")
    ax2.legend(loc="lower left")

    plt.tight_layout()
    plt.show()


def plot_regional_heatmap(country_merged, top_15_genres):
    """
    Figure 5: Regional Demand Matrix (Median Installations by Country and Genre Heatmap)
    """
    country_genre_pivot = country_merged.pivot_table(
        index='genre', 
        columns='country', 
        values='min_installs', 
        aggfunc='median'
    ).fillna(0)

    # Filter to top 15 genres
    country_genre_pivot_filtered = country_genre_pivot.loc[top_15_genres.intersection(country_genre_pivot.index)]

    fig, ax = plt.subplots(figsize=(11, 8.5))
    sns.heatmap(
        np.log10(country_genre_pivot_filtered + 1), 
        cmap="YlGnBu", 
        annot=True, 
        fmt=".1f", 
        linewidths=.5, 
        cbar_kws={'label': 'Log10(Median Installs + 1)'}, 
        ax=ax
    )
    ax.set_title("Regional Penetration Matrix: Log-Scale Median Downloads by Genre & Country", pad=15)
    ax.set_xlabel("Country Code")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.show()


def plot_keyword_discovery(discovery, apps):
    """
    Figure 6: Keyword Discovery Intelligence Map (Installs vs. Rating Score vs. App Density)
    """
    if 'keyword' in discovery.columns and discovery['keyword'].notna().sum() > 0:
        discovery_apps = discovery.merge(apps[['app_id', 'score', 'min_installs']], on='app_id', how='inner')
        keyword_stats = discovery_apps.groupby('keyword').agg(
            median_installs=('min_installs', 'median'),
            avg_score=('score', 'mean'),
            app_count=('app_id', 'count')
        ).reset_index()
        
        # Filter to keywords with at least 5 apps
        keyword_stats_filtered = keyword_stats[keyword_stats['app_count'] >= 5].sort_values(by='app_count', ascending=False).head(20)
        
        fig, ax = plt.subplots(figsize=(12, 7.5))
        scatter = ax.scatter(
            keyword_stats_filtered['median_installs'], 
            keyword_stats_filtered['keyword'], 
            s=keyword_stats_filtered['app_count'] * 20, 
            c=keyword_stats_filtered['avg_score'], 
            cmap="coolwarm", 
            alpha=0.8, 
            edgecolors="black", 
            linewidths=0.8
        )
        
        cbar = fig.colorbar(scatter, ax=ax, label="Average Rating (Score)")
        
        ax.set_xscale('log')
        ax.set_title("Search Keyword Discovery Landscape: Organic Installations vs. Average Score", pad=15)
        ax.set_xlabel("Median Installations (Log Scale)")
        ax.set_ylabel("")
        ax.grid(True, which="both", ls="--", alpha=0.3)
        
        for count in [5, 10, 20]:
            ax.scatter([], [], s=count * 20, c="gray", alpha=0.6, edgecolors="black", label=f"{count} Apps Surfaced")
        ax.legend(title="Keyword App Density", loc="upper left")
        
        plt.tight_layout()
        plt.show()
    else:
        print("Keyword analysis plot skipped since keyword column contains no values.")
