import rasterio
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Load Raster Data
with rasterio.open(r"C:\Users\laszews\Documents\Thesis\SMAPintegrals\SmIntSM.tif") as src2, \
     rasterio.open(r'C:\Users\laszews\Documents\Thesis\MIddleofSeason\subtracted_raster.tif') as src1:
    raster1 = src1.read(1)
    raster2 = src2.read(1)
    
    # Ensure alignment
    assert src1.shape == src2.shape, "Rasters must have the same shape!"

# Mask no-data values (assuming -9999 as no-data value for demonstration)
nodata1 = src1.nodata or -9999
nodata2 = src2.nodata or -9999

mask1 = raster1 != nodata1
mask2 = raster2 != nodata2
valid_mask = mask1 & mask2  # Only valid pixels in both rasters

# Flatten and filter valid data
raster1_values = raster1[valid_mask]
raster2_values = raster2[valid_mask]

# Create DataFrame
df = pd.DataFrame({
    'Raster1': raster1_values,
    'Raster2': raster2_values
})

# Define number of bins dynamically based on data size
points_per_bin = 300# Adjust this value as needed
n_bins = max(2, int(np.floor(len(df) / points_per_bin)))

# Perform dynamic binning using quantiles
df['Raster2_bin'] = pd.qcut(df['Raster2'], q=n_bins, duplicates='drop')

# Calculate mean Raster2 and mean Raster1 for each bin
bin_means = df.groupby('Raster2_bin')['Raster2'].mean()
min_values = df.groupby('Raster2_bin')['Raster1'].mean()

# Prepare DataFrame for regression
regression_df = pd.DataFrame({
    'Raster2_mean': bin_means,
    'Raster1_min': min_values
}).dropna()

# Set font to Garamond
rcParams['font.family'] = 'Garamond'

# Define x ranges
x_ranges = [(0, 12), (12, 100)]
colors = ['blue', 'orange', 'green']

# Create figure
plt.figure(figsize=(8, 6))

# Loop over x_ranges and perform OLS regression
for i, (x_min, x_max) in enumerate(x_ranges):
    subset = regression_df[(regression_df['Raster2_mean'] >= x_min) & (regression_df['Raster2_mean'] < x_max)]
    
    if len(subset) > 1:
        X = subset['Raster2_mean']
        y = subset['Raster1_min']
        X = sm.add_constant(X)
        ols_model = sm.OLS(y, X).fit()
        r_squared = ols_model.rsquared
        p_value = ols_model.pvalues[1]
        
        # Scatter and regression line
        plt.scatter(subset['Raster2_mean'], subset['Raster1_min'], alpha=0.6, color=colors[i])
        plt.plot(subset['Raster2_mean'], ols_model.predict(X), label=f"{x_min}-{x_max}: R²={r_squared:.4f}, p={p_value:.4e}", color=colors[i])
    else:
        print(f"Not enough data in range {x_min}-{x_max} for regression.")

# Labels and customization
plt.xlabel("Seasonal Soil Moisture Accumulation (cm³/cm³)", fontsize=16)
plt.ylabel("Length of Lag (days)", fontsize=16)
plt.axvline(x=12, color='gray', linestyle='--', alpha=0.7)
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.legend(fontsize=12)
plt.grid(alpha=0.4)

# Save and show plot
plt.tight_layout()
plt.savefig("dynamic_combined_regression_plot.png", dpi=300)
plt.show()
