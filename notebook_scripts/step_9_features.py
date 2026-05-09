# Step 9 — App Features & Monetization Insights
print("Running Feature Insights Analysis...")
print("Note: 'Size' and 'Content Rating' are missing in this dataset. Analyzing Ad & IAP support instead.")

if 'adSupported' in df.columns:
    df['adSupported'] = df['adSupported'].fillna(0).astype(bool)
if 'offersIAP' in df.columns:
    df['offersIAP'] = df['offersIAP'].fillna(0).astype(bool)

if 'adSupported' in df.columns and 'offersIAP' in df.columns:
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df[df['Rating'] > 0], x='adSupported', y='Rating', palette='coolwarm')
    plt.title('Impact of Ads on App Ratings')
    plt.savefig('output/9_1_ads_vs_rating.png')
    plt.show()
    
    ad_iap_crosstab = pd.crosstab(df['adSupported'], df['offersIAP'], normalize='all') * 100
    plt.figure(figsize=(7, 5))
    sns.heatmap(ad_iap_crosstab, annot=True, fmt='.1f', cmap='YlGnBu', cbar_kws={'label': 'Percentage (%)'})
    plt.title('Prevalence: Ads vs In-App Purchases')
    plt.xlabel('Offers IAP')
    plt.ylabel('Ad Supported')
    plt.savefig('output/9_2_ads_vs_iap_heatmap.png')
    plt.show()

    iap_by_cat = df.groupby('Category')['offersIAP'].mean().sort_values(ascending=False).head(15) * 100
    plt.figure(figsize=(12, 6))
    sns.barplot(x=iap_by_cat.index, y=iap_by_cat.values, palette='flare')
    plt.xticks(rotation=90)
    plt.title('Top 15 Categories by % of Apps Offering In-App Purchases')
    plt.ylabel('% of Apps')
    plt.tight_layout()
    plt.savefig('output/9_3_iap_by_category.png')
    plt.show()
else:
    print("Required columns (adSupported, offersIAP) not found. Skipping Step 9.")
