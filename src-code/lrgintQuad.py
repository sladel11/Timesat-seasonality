import rasterio
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Load Raster Data
with rasterio.open(r"") as src2, \
     rasterio.open(r"") as src1:
    raster1 = src1.read(1)
    raster2 = src2.read(1)
    
    # Ensure alignment (simplified, assumes same extent/resolution)
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

# Bin Raster2 into intervals and calculate mean for each bin
points_per_bin = 300  # Adjust this value as needed
n_bins = max(2, int(np.floor(len(df) / points_per_bin)))

# Create dynamic bins using pd.qcut to ensure roughly equal number of points per bin
df['Raster2_bin'] = pd.qcut(df['Raster2'], q=n_bins, duplicates='drop')
 
bin_means = df.groupby('Raster2_bin')['Raster2'].mean()
bin_raster1_mean = df.groupby('Raster2_bin')['Raster1'].mean()

# Prepare DataFrame for regression
regression_df = pd.DataFrame({
    'Raster2_mean': bin_means,
    'Raster1_mean': bin_raster1_mean
}).dropna()

rcParams['font.family'] = 'Garamond'
x_ranges = [(10, 200)]  # Example ranges
colors = ["orange", "green"]

plt.figure(figsize=(8, 6))

for i, (x_min, x_max) in enumerate(x_ranges):
    subset = regression_df[(regression_df['Raster2_mean'] >= x_min) & (regression_df['Raster2_mean'] < x_max)].copy()
    
    # Add squared term of Raster2_mean
    subset['Raster2_mean_sq'] = subset['Raster2_mean'] ** 2

    # Perform OLS quadratic regression
    X = subset[['Raster2_mean', 'Raster2_mean_sq']]  # Use both linear and squared terms
    y = subset['Raster1_mean']  # Fixed column name
    
    # Add a constant for the intercept
    X = sm.add_constant(X)
    
    # Fit the model
    ols_model = sm.OLS(y, X).fit()
    
    # Print regression results
    print(ols_model.summary())
    
    # Extract regression coefficients
    intercept, coef_x, coef_x_sq = ols_model.params
    
    
    # Compute the peak of the quadratic function (x_peak = -b / 2a)
    x_peak = -coef_x / (2 * coef_x_sq)
    
    # Predict y at the peak
    y_peak = intercept + coef_x * x_peak + coef_x_sq * x_peak ** 2
    
    # Plot data and fitted line
    plt.scatter(subset['Raster2_mean'], subset['Raster1_mean'], alpha=0.6, color=colors[i])
    plt.plot(subset['Raster2_mean'], ols_model.predict(X), color=colors[i], label=f"(R²={ols_model.rsquared:.4f}, p={ols_model.pvalues['Raster2_mean']:.4e})")
    
    # Plot dotted line at the peak
    plt.axvline(x=x_peak, color='black', linestyle='dotted', label=f"Peak at x = {x_peak:.2f}")

plt.xlabel("Seasonal Total Soil Moisture (cm³/cm³)", fontsize=16)
plt.ylabel("Length of Lag (days)", fontsize=16)

# Remove outermost plot box
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)

plt.legend(fontsize=12)
plt.grid(alpha=0.4)
plt.tight_layout()  # Adjust layout
plt.savefig("quadratic_regression_plot_with_peak.png", dpi=300)  # Save at 300 dpi
plt.show()


