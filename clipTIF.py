import arcpy
import os

# Set the workspace
arcpy.env.workspace = r"Where/you/store/rasters/in/tif"

# Path to the California shapefile
clipping_shapefile = r"shapefile/for/clipping"

# Ensure the shapefile exists
if not arcpy.Exists(clipping_shapefile):
    print(f"Shapefile {clipping_shapefile} does not exist.")
    sys.exit()

# Get a list of all TIFF files in the workspace
tif_files = arcpy.ListRasters('*.tif')

# Check if there are any TIFF files that match the criteria
if not tif_files:
    print("No TIFF files' found in the workspace.")
else:
    # Loop through each TIFF file
    for tif_file in tif_files:
        # Get the full path to the file
        file_path = os.path.join(arcpy.env.workspace, tif_file)
        
        # Define the output path for the clipped file
        clipped_file_path = os.path.join(arcpy.env.workspace, f"clipped_{tif_file}")
        
        # Delete the existing clipped raster if it already exists
        if arcpy.Exists(clipped_file_path):
            arcpy.Delete_management(clipped_file_path)
        
        # Clip the raster using the shapefile
        print(f"Clipping {file_path} using the shapefile...")
        arcpy.management.Clip(file_path, 
                              "#", 
                              clipped_file_path, 
                              clipping_shapefile, 
                              "#", 
                              "ClippingGeometry", 
                              "NO_MAINTAIN_EXTENT")
        
        # Calculate statistics for the clipped raster
        print(f"Calculating statistics for {clipped_file_path}...")
        arcpy.management.CalculateStatistics(clipped_file_path)
        
        # Extract bands using the band IDs method
        out_bands_raster = arcpy.ia.ExtractBand(clipped_file_path, band_ids=[1, 2])
     
        
        # Loop through each band
        for band_index in [1, 2]:
            # Create separate folders for each band
            band_folder = os.path.join(arcpy.env.workspace, f"Band_{band_index}")
            os.makedirs(band_folder, exist_ok=True)

            # Define the output band file path
            out_band_path = os.path.join(band_folder, f"{tif_file[:-4]}_band{band_index}.tif")

            # Check if the output band file already exists
            if not os.path.exists(out_band_path):
                # Extract the band
                out_band = arcpy.ia.ExtractBand(out_bands_raster, band_ids=[band_index])

                # Save the extracted band
                out_band.save(out_band_path)

                print(f"Saved {out_band_path}")
            else:
                print(f"Band {out_band_path} already exists. Skipping...")

        

            # Clean up
            del out_band_path

        # Clean up
        del out_bands_raster            
    print("All operations completed successfully.")
