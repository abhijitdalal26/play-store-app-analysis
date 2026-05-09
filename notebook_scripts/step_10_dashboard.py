# Step 10 — Summary Dashboard
print("Generating Summary Dashboard...")

total_apps = len(df)
avg_rating = df[df['Rating'] > 0]['Rating'].mean()
median_installs = df['Installs'].median()
percent_free = (len(df[df['Type'] == 'Free']) / total_apps) * 100
survival_rate = (len(df[df['Status'] == 'Survived']) / total_apps) * 100 if 'Status' in df.columns else 0
top_category = df['Category'].value_counts().index[0]

print("\n" + "="*50)
print("🏆 PLAY STORE ANALYSIS DASHBOARD 🏆".center(50))
print("="*50)
print(f"📱 Total Apps Analyzed  : {total_apps:,}")
print(f"⭐ Average Rating       : {avg_rating:.2f} / 5.0")
print(f"📥 Median Installs      : {median_installs:,.0f}")
print(f"🆓 Percentage Free      : {percent_free:.1f}%")
print(f"🧟 Survival Rate        : {survival_rate:.1f}%")
print(f"👑 Top Category         : {top_category}")
print("="*50)

print("\n✅ All visual charts have been saved to the '/output' folder.")
print("You can view them by checking that directory in your workspace.")
