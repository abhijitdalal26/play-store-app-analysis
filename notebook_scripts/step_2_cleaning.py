print("Starting Data Cleaning...")

# Drop exact duplicates based on appId
initial_rows = len(df)
df = df.drop_duplicates(subset=['appId'], keep='last')
print(f"Dropped {initial_rows - len(df)} duplicate apps.")

# Handle Missing Values
df['Rating'] = df['Rating'].fillna(0.0)

if df['Type'].dtype in [bool, float, int]:
    df['Type'] = df['Type'].map({True: 'Free', False: 'Paid', 1.0: 'Free', 0.0: 'Paid'})
df['Type'] = df['Type'].fillna('Free')

df['Installs'] = pd.to_numeric(df['Installs'], errors='coerce').fillna(0).astype(int)
df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce').fillna(0).astype(int)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0.0)

df['Last Updated'] = pd.to_datetime(df['Last Updated'], errors='coerce')
df = df.dropna(subset=['App'])

print("-" * 50)
print(f"Cleaned Shape: {df.shape}")
print("Null Values Check:")
print(df.isnull().sum())
print("-" * 50)
