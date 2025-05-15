import arcpy
import os
from arcpy.sa import ExtractByMask, SetNull

# Set the workspace and output folder
folder1 = r"C:\Users\laszews\Documents\Thesis\SMAPintegrals\tif"  # Folder 1 path
folder2 = r"C:\Users\laszews\Documents\Thesis\MIddleofSeason\EVITIF"  # Folder 2 path
output_folder = r"C:\Users\laszews\Documents\Thesis\SMAPintegrals"  # Output folder
output_subtracted_path = os.path.join(output_folder, "subtracted_raster1.tif")  # Path for the subtracted raster
arcpy.env.overwriteOutput = True

# Ensure output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to calculate the mean raster for a given folder
def calculate_mean_raster(input_folder, mask_raster, divide_by_start=1):
    tif_files = [f for f in os.listdir(input_folder) if f.endswith('season1.tif') or f.endswith('season1.tiff')]
    
    if not tif_files:
        print(f"No GeoTIFF files found in {input_folder}.")
        return None

    valid_rasters = []

    # Loop through each GeoTIFF file and process
    for index, tif in enumerate(tif_files):
        input_raster = os.path.join(input_folder, tif)
        print(f"Processing {tif}...")

        # Create a raster object
        raster = arcpy.Raster(input_raster)

        # Apply the mask to the raster (Extract by Mask)
        extracted_raster = ExtractByMask(raster, mask_raster)
        
        processed_raster = SetNull((extracted_raster == -1) | (extracted_raster == -2), extracted_raster)
        
        # Apply folder-specific processing logic
        #if folder_label == "folder2":
        #    processed_raster = (nullified_raster - (46 * index)) * 8
        #else:  # For folder1
        #    processed_raster = nullified_raster - (365 * index)

        processed_raster_path = os.path.join(output_folder, f"processed_{index+1}_{tif}")
        processed_raster.save(processed_raster_path)
        print(f"Saved processed raster to {processed_raster_path}")

        # Add the cleaned raster to the list
        valid_rasters.append(processed_raster)

    # Average the valid rasters
    mean_raster = arcpy.sa.CellStatistics(valid_rasters, statistics_type="MEAN")
    if input_folder == folder2:
        mean_raster_path = os.path.join(output_folder, f"mofs_processed_mean_EVI.tif")
        mean_raster.save(mean_raster_path)
    else:
        mean_raster_path = os.path.join(output_folder, f"LrgIntSM.tif")
        mean_raster.save(mean_raster_path)

    return mean_raster

# Define the mask raster (use the appropriate mask file for extraction)
mask_raster = r"C:\Users\laszews\Documents\Thesis\us_eco_l3_state_boundaries\CaliforniaEcoRegion.shp"  # Adjust this to the path of your mask raster

# Calculate mean rasters for both folders, using Extract by Mask
mean_raster1 = calculate_mean_raster(folder1, mask_raster)  # Only divide for folder1
mean_raster2 = calculate_mean_raster(folder2, mask_raster)  # Multiply by 8 for folder2

# Check if both mean rasters were successfully created
if mean_raster1 is not None and mean_raster2 is not None:
    # Subtract mean raster of the first folder from the mean raster of the second folder
    subtracted_raster = mean_raster2 - mean_raster1

    # Save the resulting raster to the output folder
    subtracted_raster.save(output_subtracted_path)

    print(f"Subtracted mean rasters and saved to {output_subtracted_path}")

print("Processing complete.")


