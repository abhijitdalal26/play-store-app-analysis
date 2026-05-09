# Step 3 — Ratings & Reviews Analysis
print("Running Ratings & Reviews Analysis...")

rated_apps = df[df['Rating'] > 0]

plt.figure(figsize=(10, 5))
sns.histplot(rated_apps['Rating'], bins=20, kde=True, color='skyblue')
plt.title('Distribution of App Ratings')
plt.xlabel('Rating (1 to 5)')
plt.ylabel('Count of Apps')
plt.savefig('output/3_1_rating_distribution.png')
plt.show()

avg_rating_cat = rated_apps.groupby('Category')['Rating'].mean().sort_values(ascending=False)
plt.figure(figsize=(12, 6))
sns.barplot(x=avg_rating_cat.index, y=avg_rating_cat.values, palette='viridis')
plt.xticks(rotation=90)
plt.title('Average Rating by Category')
plt.ylabel('Average Rating')
plt.tight_layout()
plt.savefig('output/3_2_avg_rating_category.png')
plt.show()

sample_df = rated_apps[rated_apps['Reviews'] < rated_apps['Reviews'].quantile(0.95)].sample(min(50000, len(rated_apps)))
plt.figure(figsize=(8, 6))
sns.scatterplot(data=sample_df, x='Rating', y='Reviews', alpha=0.1, color='purple')
plt.title('Reviews vs. Rating')
plt.savefig('output/3_3_reviews_vs_rating.png')
plt.show()

high_rating = len(rated_apps[rated_apps['Rating'] >= 4.5])
low_rating = len(rated_apps[rated_apps['Rating'] < 4.5])
plt.figure(figsize=(6, 6))
plt.pie([high_rating, low_rating], labels=['>= 4.5', '< 4.5'], autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
plt.title('Proportion of Highly Rated Apps')
plt.savefig('output/3_4_high_vs_low_rating_pie.png')
plt.show()
