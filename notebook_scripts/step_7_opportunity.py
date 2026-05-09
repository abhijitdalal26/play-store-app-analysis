# Step 7 — Easy to Grow Categories
print("Calculating Opportunity Scores...")

opp_df = df.groupby('Category').agg({
    'App': 'count',
    'Installs': 'mean',
    'Rating': lambda x: x[x>0].mean()
}).rename(columns={'App': 'Competition', 'Installs': 'Avg Demand', 'Rating': 'Avg Happiness'})

opp_df = opp_df[opp_df['Competition'] > 500].copy()
scaler = MinMaxScaler()

opp_df['Score_Comp'] = 1 - scaler.fit_transform(opp_df[['Competition']])
opp_df['Score_Demand'] = scaler.fit_transform(opp_df[['Avg Demand']])
opp_df['Score_Happiness'] = scaler.fit_transform(opp_df[['Avg Happiness']].fillna(0))

opp_df['Opportunity Score'] = (opp_df['Score_Demand'] * 0.4) + (opp_df['Score_Comp'] * 0.4) + (opp_df['Score_Happiness'] * 0.2)
opp_df = opp_df.sort_values(by='Opportunity Score', ascending=False)

print("Top 10 'Easiest to Grow' Categories:")
display(opp_df[['Competition', 'Avg Demand', 'Avg Happiness', 'Opportunity Score']].head(10))

plt.figure(figsize=(12, 8))
sns.scatterplot(data=opp_df, x='Competition', y='Avg Demand', size='Opportunity Score', 
                hue='Opportunity Score', sizes=(50, 1000), palette='viridis', alpha=0.7)

for i in range(5):
    plt.text(opp_df['Competition'].iloc[i], opp_df['Avg Demand'].iloc[i], opp_df.index[i], fontsize=10, weight='bold')

plt.title('Category Opportunity Map (Bubble Size = Opportunity Score)')
plt.xlabel('Competition (Total Apps)')
plt.ylabel('Demand (Avg Installs)')
plt.yscale('log')
plt.xscale('log')
plt.savefig('output/7_1_opportunity_bubble.png')
plt.show()
