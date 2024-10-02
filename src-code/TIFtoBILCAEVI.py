import arcpy
import os

# Set the workspace
arcpy.env.workspace = r"C:\Users\laszews\Documents\Thesis\EVI\Mosaic\clipped_mosaics"
snap_raster_path = r"C:\Users\laszews\Documents\Thesis\2016SMAP\Band_1\BIL\NSIDC-0779_EASE2_G1km_SMAP_SM_DS_20160328_band1.bil"

# Set the snap raster environment
arcpy.env.snapRaster = snap_raster_path
arcpy.env.extent = snap_raster_path

# Get a list of all TIFF files in the workspace that start with 'clipped_mosaic'
tif_files = arcpy.ListRasters('clipped_mosaic*.tif')

# Check if there are any TIFF files that match the criteria
if not tif_files:
    print("No TIFF files starting with 'clipped_mosaic' found in the workspace.")
else:
    for tif_file in tif_files:
        file_path = os.path.join(arcpy.env.workspace, tif_file)
        
        # Calculate statistics for the clipped raster
        print(f"Calculating statistics for {file_path}...")
        arcpy.management.CalculateStatistics(file_path)

        # Define intermediate file paths
        tif_folder = os.path.join(arcpy.env.workspace, "TIF")
        os.makedirs(tif_folder, exist_ok=True)
        aligned_raster_path = os.path.join(tif_folder, f"aligned_{tif_file}")
        
        # Align the raster to the snap raster
        print(f"Aligning {file_path} to the snap raster...")
        arcpy.management.ProjectRaster(
            in_raster=file_path,
            out_raster=aligned_raster_path,
            out_coor_system=arcpy.Describe(snap_raster_path).spatialReference,
            cell_size=arcpy.Describe(snap_raster_path).meanCellWidth
        )
        
        # Define output BIL folder and path
        bil_folder = os.path.join(arcpy.env.workspace, "BIL")
        os.makedirs(bil_folder, exist_ok=True)
        out_bil_path = os.path.join(bil_folder, f"{tif_file}.bil")
        
        # Convert the aligned raster to BIL format
        print(f"Converting {aligned_raster_path} to {out_bil_path}...")
        arcpy.conversion.RasterToOtherFormat(aligned_raster_path, bil_folder, "BIL")
        print(f"Converted {aligned_raster_path} to {out_bil_path}.")
    
    print("All operations completed successfully.")

