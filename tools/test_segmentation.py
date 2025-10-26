import pandas as pd
import json
from feature import customer_segmentation

# Create sample data
n = 100
data = {
    'Invoice ID': [f'INV-{i}' for i in range(n)],
    'Date': pd.date_range(start='2023-01-01', periods=n).astype(str),
    'Total': [100 + i for i in range(n)],
    'Quantity': [i % 10 + 1 for i in range(n)],
    'Unit price': [10 + (i % 20) for i in range(n)],
}

df = pd.DataFrame(data)

# Run segmentation
seg = customer_segmentation(df.copy(), n_clusters=3)

# Prepare cluster stats similar to api.py
cluster_stats = seg.groupby('Cluster').agg({
    'Total': ['mean', 'sum', 'count'],
    'Quantity': ['mean', 'sum']
}).reset_index()

# Flatten multi-index columns
if isinstance(cluster_stats.columns, pd.MultiIndex):
    cluster_stats.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in cluster_stats.columns.values]

# Rename Cluster to Cluster_
if 'Cluster' in cluster_stats.columns:
    cluster_stats = cluster_stats.rename(columns={'Cluster': 'Cluster_'})

clusters = cluster_stats.to_dict('records')
print(json.dumps({'success': True, 'clusters': clusters, 'n_clusters': 3}, indent=2))
