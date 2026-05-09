# Step 6 — App Survival Analysis
import datetime
print("Running Survival Analysis...")

baseline_date = pd.to_datetime("2022-11-01")
df['Days Since Update'] = (baseline_date - df['Last Updated']).dt.days

df['Status'] = 'Zombie'
df.loc[(df['Days Since Update'] <= 730) & (df['Rating'] >= 3.5) & (df['Installs'] >= 1000), 'Status'] = 'Survived'
df.loc[(df['Days Since Update'] >= 1095) | ((df['Rating'] > 0) & (df['Rating'] < 2.0)) | (df['Installs'] < 100), 'Status'] = 'Dead'

survival_counts = df.groupby(['Category', 'Status']).size().unstack(fill_value=0)
survival_counts['Total'] = survival_counts.sum(axis=1)
survival_counts['Survival Rate %'] = (survival_counts['Survived'] / survival_counts['Total']) * 100
survival_counts = survival_counts.sort_values(by='Survival Rate %', ascending=False)

print("Survival Rate by Category (Top 10):")
display(survival_counts[['Survival Rate %', 'Survived', 'Dead', 'Total']].head(10))

traits = df[df['Status'].isin(['Survived', 'Dead'])].groupby('Status').agg({
    'Rating': 'mean',
    'Installs': 'median',
    'Price': 'mean',
    'Days Since Update': 'mean'
}).round(2)

print("\nWhat do Surviving vs Dead apps have in common?")
display(traits)
