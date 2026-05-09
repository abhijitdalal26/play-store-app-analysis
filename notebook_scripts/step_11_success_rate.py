# Step 11 — The Reality of App Success
print("Running Success Rate Analysis...")

df['Is Successful'] = (df['Installs'] >= 100000) & (df['Rating'] >= 4.0)

total_apps = len(df)
successful_apps = df['Is Successful'].sum()
success_rate = (successful_apps / total_apps) * 100

print(f"Total Apps on the Store: {total_apps:,}")
print(f"Apps that actually reached 100k+ installs with a 4.0+ rating: {successful_apps:,}")
print(f"The Macro Success Rate is only: {success_rate:.2f}%\n")

success_by_cat = df.groupby('Category').agg(
    Total_Apps=('App', 'count'),
    Successful_Apps=('Is Successful', 'sum')
)
success_by_cat['Success Rate (%)'] = (success_by_cat['Successful_Apps'] / success_by_cat['Total_Apps']) * 100

top_cats = success_by_cat.sort_values(by='Total_Apps', ascending=False).head(15)

plt.figure(figsize=(12, 6))
sns.barplot(x=top_cats.index, y=top_cats['Success Rate (%)'], palette='magma')
plt.xticks(rotation=90)
plt.title('Success Rate (% of apps >= 100k installs & >= 4.0 rating) in Top 15 Largest Categories')
plt.ylabel('Success Rate (%)')
plt.tight_layout()
plt.savefig('output/11_1_success_rate_by_category.png')
plt.show()

highest_success = success_by_cat[success_by_cat['Total_Apps'] > 5000].sort_values(by='Success Rate (%)', ascending=False).head(10)
print("Categories with the HIGHEST absolute chance of success:")
display(highest_success[['Total_Apps', 'Success Rate (%)']])
