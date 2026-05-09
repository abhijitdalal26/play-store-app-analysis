# Step 8 — Pricing Analysis
print("Running Pricing Analysis...")

type_counts = df['Type'].value_counts()
plt.figure(figsize=(6, 6))
plt.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', colors=['#3498db', '#e67e22'])
plt.title('Free vs Paid Apps')
plt.savefig('output/8_1_free_vs_paid_pie.png')
plt.show()

paid_apps = df[(df['Type'] == 'Paid') & (df['Price'] > 0)]
plt.figure(figsize=(10, 5))
sns.histplot(paid_apps[paid_apps['Price'] <= 50]['Price'], bins=50, color='green')
plt.title('Price Distribution of Paid Apps (Under $50)')
plt.xlabel('Price ($)')
plt.savefig('output/8_2_price_distribution.png')
plt.show()

plt.figure(figsize=(8, 6))
sns.boxplot(data=df[df['Rating'] > 0], x='Type', y='Rating', palette='Set1')
plt.title('Ratings: Free vs Paid')
plt.savefig('output/8_3_ratings_free_vs_paid.png')
plt.show()

paid_apps['Revenue Proxy'] = paid_apps['Price'] * paid_apps['Installs']
cat_revenue = paid_apps.groupby('Category')['Revenue Proxy'].sum().sort_values(ascending=False).head(15)

plt.figure(figsize=(12, 6))
sns.barplot(x=cat_revenue.index, y=cat_revenue.values, palette='magma')
plt.xticks(rotation=90)
plt.title('Top 15 Categories by Paid App Revenue Proxy (Price x Installs)')
plt.ylabel('Minimum Revenue Proxy ($)')
plt.tight_layout()
plt.savefig('output/8_4_revenue_proxy_by_category.png')
plt.show()
