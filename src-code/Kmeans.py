import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from matplotlib import rcParams
import colorsys


# List of raster files
raster_files = [
    r"C:\Users\laszews\Documents\Thesis\MIddleofSeason\subtracted_raster.tif",
    r"C:\Users\laszews\Documents\Thesis\SMAPintegrals\SmIntSM.tif",
    r"C:\Users\laszews\Documents\Thesis\LrgInt\LrgIntSM.tif",
    r"C:\Users\laszews\Documents\Thesis\lengthofSeason\processed_mean_EVI.tif"

]
import json

# Load the lyrx file
lyrx_path = r"C:\Users\laszews\Documents\cluster\clusterpolyactual.lyrx"
with open(lyrx_path, 'r') as file:
    lyrx_data = json.load(file)

# Extract cluster color mapping
cluster_colors = {}
renderer = lyrx_data['layerDefinitions'][0]['renderer']
cluster_classes = renderer['groups'][0]['classes']
cluster_colors = {}

for cls in cluster_classes:
    try:
        cluster_id = int(cls['label'])  # assumes label is a number like "0", "1", etc.
        
        # Extract HSV color
        hsv_color = cls['symbol']['symbol']['symbolLayers'][1]['color']['values']  # [H, S, V, A]
        h, s, v = hsv_color[:3]
        
        # Normalize HSV to 0-1 and convert to RGB
        r, g, b = colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)
        rgb = tuple(int(x * 255) for x in (r, g, b))
        hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)

        cluster_colors[cluster_id] = hex_color
    except Exception as e:
        print(f"Error parsing {cls['label']}: {e}")

# Print results
print("Cluster colors:")
for k in sorted(cluster_colors.keys()):
    print(f"Cluster {k}: {cluster_colors[k]}")
    
# Set font to Garamond
rcParams['font.family'] = 'Garamond'
# Prepare a dictionary to store all raster data
all_data = {}
height, width = None, None  # To store common dimensions
original_values = {}  # Store original values before standardization

# Dictionary to store ecoregion classifications
ecoregion_values = {}

for i, raster_file in enumerate(raster_files):
    with rasterio.open(raster_file) as src:
        band = src.read(1)  # Read first band
        if height is None or width is None:
            height, width = band.shape  # Initialize with the dimensions of the first raster

        # Handle missing values
        if raster_file == r"C:\Users\laszews\Documents\Thesis\us_eco_l3_state_boundaries\rasterEcoRegion.tif":
            print(f"Resizing StateWMA raster to {height}x{width}.")
            band = np.resize(band, (height, width))  # Resize to expected dimensions
            band = np.where(band == -3.4028235E+38, np.nan, band)


        # Generate coordinates only once
        if i == 0:
            x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))
            all_data['x'] = x_coords.flatten()
            all_data['y'] = y_coords.flatten()

        # Extract filename and use it as the column name
        raster_name = raster_file.split("\\")[-1].replace('.tif', '')
        all_data[f'value_{i+1}'] = band.flatten()
        
        # Store original values before filtering
        original_values[raster_name] = band.flatten()

# Convert to DataFrame
df = pd.DataFrame(all_data)


# Remove invalid values (e.g., -3.4028235E+38)
invalid_value = np.float32('-3.4028235E+38')
df = df[df['value_1'] != invalid_value]

# Save original indices before standardization
df['orig_x'] = df['x'].astype(int)
df['orig_y'] = df['y'].astype(int)

# Now filter original values to match df's index
for name in original_values:
    df[name] = original_values[name][df.index]

# Standardize raster values and coordinates
scaler = StandardScaler()
scaled_features = scaler.fit_transform(df[['x','y'] + [f'value_{i+1}' for i in range(len(raster_files))]])
df[['x', 'y'] + [f'value_{i+1}' for i in range(len(raster_files))]] = scaled_features

# Save cleaned and standardized data
df.to_csv("raster_pixels_cleaned_standardized.csv", index=False)

# Perform K-Means clustering using standardized data
num_clusters = 13# Adjust the number of clusters as needed
kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=20)
df['cluster'] = kmeans.fit_predict(df[['y','value_1','value_2', 'value_3', 'value_4']])  

# Save clustered data with original values and ecoregion name
df.to_csv("raster_clusters_with_coords_cleaned_standardized.csv", index=False)

from sklearn.metrics import silhouette_score

# Sample 10,000 rows for faster testing (adjust if needed)
sample_df = df.sample(n=30000, random_state=42)
X_sample = sample_df[['y','value_1','value_2', 'value_3', 'value_4']]
X = X_sample

# Elbow method
inertias = []
silhouette_scores = []
k_range = range(2, 15)  # Adjust upper limit if needed

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=20)
    labels = kmeans.fit_predict(X)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X, labels))

# Plot elbow chart
plt.figure(figsize=(12, 6))
plt.plot(k_range, inertias, marker='o', linestyle='-')
plt.xlabel("Number of Clusters (k)",fontsize=18)
plt.ylabel("Average Inertia",fontsize=18)
plt.xticks(k_range)
sns.despine(top=True, right=True)
plt.tick_params(axis='both', labelsize=12)  # Increase the font size of the axis ticks
plt.grid(True)
plt.show()

# Plot silhouette scores
plt.figure(figsize=(12, 6))
plt.plot(k_range, silhouette_scores, marker='s', color='darkorange')
plt.xlabel("Number of Clusters (k)",fontsize=18)
plt.ylabel("Average Silhouette Score",fontsize=18)
sns.despine(top=True, right=True)
plt.xticks(k_range)
plt.ylim(0, .4)
plt.tick_params(axis='both', labelsize=12)  # Increase the font size of the axis ticks

plt.grid(True)
plt.show()
 

# Visualize clusters
plt.figure(figsize=(10, 8))
scatter = plt.scatter(df['x'], df['y'], c=df['cluster'], cmap='viridis', marker='.')
plt.colorbar(scatter, label="Cluster ID")
plt.xlabel("Standardized X Coordinate")
plt.ylabel("Standardized Y Coordinate")
plt.title("K-Means Clustering of Raster Data (Standardized Coordinates & Values)")
plt.show()

print("CSV files saved: raster_pixels_cleaned_standardized.csv and raster_clusters_with_coords_cleaned_standardized.csv")

# Convert clusters back to raster format
with rasterio.open(raster_files[0]) as src:
    meta = src.meta.copy()
    height, width = src.shape

# Create an empty raster initialized with nodata values
cluster_raster = np.full((height, width), -1, dtype=np.int32)  # -1 as nodata value

# Ensure indices are within valid range
valid_mask = (df['orig_x'] >= 0) & (df['orig_x'] < width) & (df['orig_y'] >= 0) & (df['orig_y'] < height)
df_valid = df[valid_mask]  # Filter only valid coordinates

# Assign clusters
cluster_raster[df_valid['orig_y'], df_valid['orig_x']] = df_valid['cluster'].values

# Update metadata for a single-band output raster
meta.update(dtype=rasterio.int32, count=1, nodata=-1)

# Save the clustered raster
output_raster = "raster_clusters_standardized_kmeansno13.tif"
with rasterio.open(output_raster, 'w', **meta) as dst:
    dst.write(cluster_raster, 1)

print(f"Cluster raster saved as {output_raster}")

cluster_colors = {str(k): v for k, v in cluster_colors.items()}
flierprops = dict(marker='.', color='gray', markersize=6, alpha=0.5)  # Adjust the alpha for transparency

plt.figure(figsize=(14, 9))  # Make the figure wider
sns.boxplot(x='cluster', y='subtracted_raster', data=df, width=.9, linewidth=0.4, palette=cluster_colors, flierprops=flierprops)  # Adjust box width and outline thickness
plt.xlabel("Cluster", fontsize=24)
plt.ylabel("Seasonal Lag (EVI - SM)", fontsize=24)
sns.despine(top=True, right=True)
plt.xticks(rotation=45)
plt.tick_params(axis='both', labelsize=18)  # Increase the font size of the axis ticks
plt.show()

# Box plot for value_2 distribution by cluster, color-coded by ecoregion
plt.figure(figsize=(14, 9))  # Make the figure wider
sns.boxplot(x='cluster', y='SmIntSM', data=df, width=.9, linewidth=0.4, palette=cluster_colors, flierprops=flierprops)  # Adjust box width and outline thickness
plt.xlabel("Cluster", fontsize=24)
plt.ylabel("Seasonal SM Accumulation (No Base Value)", fontsize=20)
sns.despine(top=True, right=True)
plt.xticks(rotation=45)
plt.tick_params(axis='both', labelsize=18)  # Increase the font size of the axis ticks
plt.show()

# Box plot for LrgIntSM distribution by cluster, color-coded by ecoregion
plt.figure(figsize=(14, 9))  # Make the figure wider
sns.boxplot(x='cluster', y='LrgIntSM', data=df, width=.9, linewidth=0.4, palette=cluster_colors, flierprops=flierprops)  # Adjust box width and outline thickness
plt.xlabel("Cluster", fontsize=24)
plt.ylabel("Total Seasonal SM Accumulation", fontsize=24)
sns.despine(top=True, right=True)
plt.xticks(rotation=45)
plt.tick_params(axis='both', labelsize=18)  # Increase the font size of the axis ticks
plt.show()

# Box plot for processed_mean_EVI distribution by cluster, color-coded by ecoregion
plt.figure(figsize=(14, 9))  # Make the figure wider
sns.boxplot(x='cluster', y='processed_mean_EVI', data=df, width=.9, linewidth=0.4, palette=cluster_colors, flierprops=flierprops)  # Adjust box width and outline thickness
plt.xlabel("Cluster", fontsize=24)
plt.ylabel("Length of Vegetation Season", fontsize=24)
sns.despine(top=True, right=True)
plt.xticks(rotation=45)
plt.tick_params(axis='both', labelsize=18)  # Increase the font size of the axis ticks
plt.show()
