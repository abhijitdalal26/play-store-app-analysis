import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import os

# Set plotting style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# Create output folder for charts
os.makedirs("output", exist_ok=True)

print("Loading dataset (this might take a minute for 3.45M rows)...")

# Path to the dataset
csv_path = "google-play-dataset/google-play-dataset-by-tapivedotcom.csv"

# Load in chunks to manage memory, then concatenate
chunks = []
for chunk in pd.read_csv(csv_path, chunksize=100000, low_memory=False):
    chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)
print(f"Dataset loaded successfully!")

# Auto-detect and remap columns from Tapivedotcom schema to expected schema
column_mapping = {
    'title': 'App',
    'genre': 'Category',
    'score': 'Rating',
    'reviews': 'Reviews',
    'minInstalls': 'Installs',
    'free': 'Type',
    'price': 'Price',
    'dateUpdated': 'Last Updated'
}

df.rename(columns=column_mapping, inplace=True)

# Keep only the columns we need for analysis
columns_to_keep = ['App', 'appId', 'Category', 'Rating', 'Reviews', 'Installs', 
                   'Type', 'Price', 'Last Updated', 'adSupported', 'offersIAP']
                   
existing_cols = [col for col in columns_to_keep if col in df.columns]
df = df[existing_cols]

print("-" * 50)
print(f"Shape: {df.shape}")
print("-" * 50)
print("Data Types:")
print(df.dtypes)
print("-" * 50)
display(df.head())
