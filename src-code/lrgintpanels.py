import rasterio
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Load Raster Data
with rasterio.open(r"C:\Users\laszews\Documents\Thesis\LrgInt\LrgIntSM.tif") as src2, \
     rasterio.open(r'C:\Users\laszews\Documents\Thesis\MIddleofSeason\subtracted_raster.tif') as src1, \
     rasterio.open(r'C:\Users\laszews\Documents\Thesis\nlcdmask.tif') as src_land_cover:
    raster1 = src1.read(1)
    raster2 = src2.read(1)
    land_cover = src_land_cover.read(1)
    
    # Ensure alignment (simplified, assumes same extent/resolution)
    assert src1.shape == src2.shape, "Rasters must have the same shape!"

# Mask no-data values (assuming -9999 as no-data value for demonstration)
nodata1 = src1.nodata or -9999
nodata2 = src2.nodata or -9999
land_cover_nodata = src_land_cover.nodata or -9999

mask1 = raster1 != nodata1
mask2 = raster2 != nodata2
mask_land_cover = land_cover != land_cover_nodata
valid_mask = mask1 & mask2 & mask_land_cover

# Flatten and filter valid data
raster1_values = raster1[valid_mask]
raster2_values = raster2[valid_mask]
land_cover_values = land_cover[valid_mask]

# Create DataFrame
df = pd.DataFrame({
    'Raster1': raster1_values,
    'Raster2': raster2_values,
    'LandCover': land_cover_values
})

# Set plotting font
rcParams['font.family'] = 'Garamond'

# Define x_ranges and corresponding colors for the regressions (skip 0 to 10)
x_ranges = [(0, 200)]
colors = ["orange", "green"]

# Define desired number of data points per bin for dynamic binning
points_per_bin = 300  # Adjust this value as needed

# Specify the land cover classes for the panels
selected_classes = [42, 52, 71, 82]

# Mapping of land cover codes to names
land_cover_names = {42: "Evergreen Forest", 52: "Shrubland", 71: "Grassland", 82: "Cropland"}

# Create subplots (2x2 grid)
fig, axs = plt.subplots(2, 2, figsize=(14, 12))
axs = axs.flatten()

# Loop over the selected land cover classes
for i, land_cover_class in enumerate(selected_classes):
    ax = axs[i]
    df_lc = df[df['LandCover'] == land_cover_class].copy()
    
    # Compute number of bins based on desired points per bin (at least 2 bins)
    n_bins = max(2, int(np.floor(len(df_lc) / points_per_bin)))
    
    # Create dynamic bins using pd.qcut to ensure roughly equal number of points per bin
    df_lc['Raster2_bin'] = pd.qcut(df_lc['Raster2'], q=n_bins, duplicates='drop')
    
    # Calculate the mean Raster2 and Raster1 for each bin
    bin_means = df_lc.groupby('Raster2_bin')['Raster2'].mean()
    bin_raster1_mean = df_lc.groupby('Raster2_bin')['Raster1'].mean()
    
    # Prepare DataFrame for regression
    regression_df = pd.DataFrame({
        'Raster2_mean': bin_means,
        'Raster1_mean': bin_raster1_mean
    }).dropna().reset_index(drop=True)
    
    # Loop over the defined x_ranges to perform quadratic OLS regression for each subset
    for j, (x_min, x_max) in enumerate(x_ranges):
        subset = regression_df[(regression_df['Raster2_mean'] >= x_min) & 
                               (regression_df['Raster2_mean'] < x_max)].copy()
        
        if len(subset) > 1:  # Ensure there is enough data for regression
            subset['Raster2_mean_sq'] = subset['Raster2_mean'] ** 2
            X = subset[['Raster2_mean', 'Raster2_mean_sq']]
            y = subset['Raster1_mean']
            X = sm.add_constant(X)
            ols_model = sm.OLS(y, X).fit()
            r_squared = ols_model.rsquared
            p_value = ols_model.pvalues['Raster2_mean']
            a, b = ols_model.params[1], ols_model.params[2]  # Coefficients for x² and x
            equation = f"y = {a:.2e}x² + {b:.2e}x"  # Quadratic equation string
            
            color = colors[j] if j < len(colors) else "black"
            
            # Plot the scatter points and regression line using the assigned color
            ax.scatter(subset['Raster2_mean'], subset['Raster1_mean'], alpha=0.6, color=color)
            
            # For a smooth line, sort the subset by Raster2_mean
            sorted_subset = subset.sort_values('Raster2_mean')
            ax.plot(sorted_subset['Raster2_mean'], 
                    ols_model.predict(sm.add_constant(sorted_subset[['Raster2_mean', 'Raster2_mean_sq']])),
                    color=color,
                    label=f" (R²={r_squared:.4f}, p={p_value:.4e})")
            
            y_offset = 0.95 - 0.05 * j  # Stagger vertically with each range

            
                
            # Extract regression coefficients
            intercept, coef_x, coef_x_sq = ols_model.params
            
            
            # Compute the peak of the quadratic function (x_peak = -b / 2a)
            x_peak = -coef_x / (2 * coef_x_sq)
            
            # Plot the peak line for this subplot
            ax.axvline(x=x_peak, color='black', linestyle='dotted', label=f"Peak at x = {x_peak:.2f}")
            
        else:
            print(f"Not enough data for land cover {land_cover_class} in range {x_min}-{x_max}.")
    
    # Set axis limits and formatting
    ax.set_title(land_cover_names.get(land_cover_class, str(land_cover_class)), fontsize=14)
    ax.set_xlabel("Seasonal Total Soil Moisture (cm³/cm³)", fontsize=12)
    ax.set_ylabel("Length of Lag (days)", fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.4)
    
    # Set y-axis limits from -40 to 80 and x-axis limits from 10 to 200 (skipping 0-10)
    ax.set_ylim(-40, 90)
    ax.set_xlim(5, 180)

plt.tight_layout()
plt.savefig("quadratic_regression_panels_with_equation_and_peak.png", dpi=300)
plt.show()

