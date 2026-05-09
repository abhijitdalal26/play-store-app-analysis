# Step 4 — Category & Genre Trends
print("Running Category Trends Analysis...")

top_cats_count = df['Category'].value_counts().head(20)
plt.figure(figsize=(12, 6))
sns.barplot(x=top_cats_count.index, y=top_cats_count.values, palette='mako')
plt.xticks(rotation=90)
plt.title('Top 20 Categories by Number of Apps (Competition)')
plt.ylabel('Number of Apps')
plt.tight_layout()
plt.savefig('output/4_1_top_categories_count.png')
plt.show()

top_cats_installs = df.groupby('Category')['Installs'].sum().sort_values(ascending=False).head(20)
plt.figure(figsize=(12, 6))
sns.barplot(x=top_cats_installs.index, y=top_cats_installs.values, palette='rocket')
plt.xticks(rotation=90)
plt.title('Top 20 Categories by Total Installs (Demand)')
plt.ylabel('Total Installs')
plt.tight_layout()
plt.savefig('output/4_2_top_categories_installs.png')
plt.show()

cat_stats = df.groupby('Category').agg({'App': 'count', 'Installs': 'mean'}).rename(columns={'App': 'App Count', 'Installs': 'Avg Installs'})

most_competitive = cat_stats.sort_values(by=['App Count', 'Avg Installs'], ascending=[False, True]).head(10)
print("Most Competitive Categories (Hard to break in):")
display(most_competitive)

least_saturated = cat_stats[(cat_stats['App Count'] > 1000)].sort_values(by=['Avg Installs', 'App Count'], ascending=[False, True]).head(10)
print("\nLeast Saturated Categories (High opportunity):")
display(least_saturated)
