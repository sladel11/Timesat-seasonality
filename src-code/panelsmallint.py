import rasterio
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Load Raster Data
with rasterio.open(r"C:\Users\laszews\Documents\Thesis\SMAPintegrals\SmIntSM.tif") as src2, \
     rasterio.open(r'C:\Users\laszews\Documents\Thesis\MIddleofSeason\subtracted_raster.tif') as src1, \
     rasterio.open(r'C:\Users\laszews\Documents\Thesis\nlcdmask.tif') as src_land_cover:
    
    raster1 = src1.read(1)
    raster2 = src2.read(1)
    land_cover = src_land_cover.read(1)
    
    # Ensure alignment (assumes same extent/resolution)
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

# Set font to Garamond
rcParams['font.family'] = 'Garamond'

# Define x ranges and colors for the regressions
x_ranges = [(0, 12), (12, 100)]
colors = ["blue", "orange", "green"]

# Define dynamic binning parameter: desired number of points per bin
points_per_bin = 300  # Adjust as needed

# Specify the selected land cover classes and mapping to names
selected_classes = [42, 52, 71, 82]
land_cover_names = {42: "Evergreen Forest", 52: "Shrubland", 71: "Grassland", 82: "Cropland"}

# Create a 2x2 panel figure
fig, axs = plt.subplots(2, 2, figsize=(14, 12))
axs = axs.flatten()

for i, lc_class in enumerate(selected_classes):
    ax = axs[i]
    
    # Subset the data for the current land cover class
    df_lc = df[df['LandCover'] == lc_class].copy()
    
    # Determine number of bins based on desired points per bin (ensure at least 2 bins)
    n_bins = max(2, int(np.floor(len(df_lc) / points_per_bin)))
    
    # Create dynamic bins with roughly equal number of points per bin
    df_lc['Raster2_bin'] = pd.qcut(df_lc['Raster2'], q=n_bins, duplicates='drop')
    
    # Calculate the mean Raster2 and mean Raster1 values for each bin
    bin_means = df_lc.groupby('Raster2_bin')['Raster2'].mean()
    bin_raster1_mean = df_lc.groupby('Raster2_bin')['Raster1'].mean()
    
    # Prepare a DataFrame for regression analysis
    regression_df = pd.DataFrame({
        'Raster2_mean': bin_means,
        'Raster1_min': bin_raster1_mean
    }).dropna().reset_index(drop=True)
    for j, (x_min, x_max) in enumerate(x_ranges):
        # Subset binned data for the current x range
        subset = regression_df[(regression_df['Raster2_mean'] >= x_min) & 
                               (regression_df['Raster2_mean'] < x_max)].copy()
        
        if len(subset) > 1:  # Ensure there is enough data for regression
            X = subset['Raster2_mean']
            y = subset['Raster1_min']
            X = sm.add_constant(X)
            ols_model = sm.OLS(y, X).fit()
            r_squared = ols_model.rsquared
            p_value = ols_model.pvalues[1]
            slope = ols_model.params[1]  # Slope of the regression line
            intercept = ols_model.params[0]  # Intercept of the regression line
            equation = f"y = {slope:.4f}x + {intercept:.4f}"  # Linear equation string
            
            color = colors[j] if j < len(colors) else "black"
            
            # Plot the scatter points and regression line using the assigned color
            ax.scatter(subset['Raster2_mean'], subset['Raster1_min'], alpha=0.6, color=color)
            
            # For a smooth line, sort the subset by Raster2_mean
            sorted_subset = subset.sort_values('Raster2_mean')
            ax.plot(sorted_subset['Raster2_mean'], 
                    ols_model.predict(sm.add_constant(sorted_subset['Raster2_mean'])),
                    color=color,
                    label=f" (R²={r_squared:.4f}, p={p_value:.4e})")
            y_offset = 0.95 - 0.05 * j  # Stagger vertically with each range

            # Add the equation as text on the plot
            ax.text(0.2, y_offset, equation, transform=ax.transAxes, fontsize=12, verticalalignment='top', color=color)
        else:
            print(f"Not enough data for land cover {lc_class} in range {x_min}-{x_max}.")

    # Set axis labels and panel title (using land cover name)
    ax.set_xlabel("Seasonal Soil Moisture Accumulation (cm³/cm³)", fontsize=12)
    ax.set_ylabel("Length of Lag (days)", fontsize=12)
    ax.set_title(land_cover_names.get(lc_class, str(lc_class)), fontsize=14)
    ax.axvline(x=12, color='gray', linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.4)
    ax.set_ylim(-30, 115)
    ax.set_xlim(0, 75)
    
from scipy.stats import ks_2samp, f_oneway, ttest_ind
from itertools import combinations

# Perform Kolmogorov-Smirnov test between each pair of land cover classes
ks_results = {}
pairwise_comparisons = list(combinations(selected_classes, 2))

for lc1, lc2 in pairwise_comparisons:
    data1 = df[df['LandCover'] == lc1]['Raster1']
    data2 = df[df['LandCover'] == lc2]['Raster1']
    ks_stat, ks_p = ks_2samp(data1, data2)
    ks_results[(lc1, lc2)] = (ks_stat, ks_p)
    
    print(f"KS test between {land_cover_names.get(lc1, str(lc1))} and {land_cover_names.get(lc2, str(lc2))}: D={ks_stat:.4f}, p={ks_p:.4e}")

# Perform ANOVA to compare means across all four land cover types
anova_stat, anova_p = f_oneway(
    df[df['LandCover'] == selected_classes[0]]['Raster1'],
    df[df['LandCover'] == selected_classes[1]]['Raster1'],
    df[df['LandCover'] == selected_classes[2]]['Raster1'],
    df[df['LandCover'] == selected_classes[3]]['Raster1']
)
print(f"ANOVA test across all four land covers: F={anova_stat:.4f}, p={anova_p:.4e}")

# Perform pairwise t-tests
ttest_results = {}
for lc1, lc2 in pairwise_comparisons:
    data1 = df[df['LandCover'] == lc1]['Raster1']
    data2 = df[df['LandCover'] == lc2]['Raster1']
    t_stat, t_p = ttest_ind(data1, data2, equal_var=False)
    ttest_results[(lc1, lc2)] = (t_stat, t_p)
    
    print(f"t-test between {land_cover_names.get(lc1, str(lc1))} and {land_cover_names.get(lc2, str(lc2))}: t={t_stat:.4f}, p={t_p:.4e}")
plt.tight_layout()
plt.savefig("dynamic_combined_regression_panels.png", dpi=300)
plt.show()
