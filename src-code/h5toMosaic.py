import h5py
import os
import numpy as np
import datetime as dt
import re
import arcpy
import time

# Enable GDAL exceptions
from osgeo import gdal, gdal_array
gdal.UseExceptions()

# Update to dir on your OS containing VIIRS files
inDir = r"to/data"
os.chdir(inDir)  # Change to working directory
outDir = r"\TIF" # new tif images
mosaicDir = r"\Mosaic"  # New directory for mosaicked files
california_shapefile = r"" #shapefiel for clipping
clippedMosaicDir = os.path.join(mosaicDir, "clipped_mosaics")


# Ensure arcpy environment settings
arcpy.env.workspace = inDir
arcpy.env.overwriteOutput = True

# List all .h5 files in the directory
files = arcpy.ListRasters('*.h5')

# Ensure the output and mosaic directories exist
if not os.path.exists(outDir):
    os.makedirs(outDir)
if not os.path.exists(mosaicDir):
    os.makedirs(mosaicDir)
if not os.path.exists(clippedMosaicDir):
    os.makedirs(clippedMosaicDir)

# Extract dates from file names and group by date
file_dict = {}
date_pattern = re.compile(r"\d{2}_\d{2}_\d{4}$")

for inFile in files:
    outName = inFile.rsplit('.', 1)[0]  # Parse out the file extension, keep file name
    yeardoy = inFile.split('.')[1][1:]  # Split filename to retrieve acquisition date
    date = dt.datetime.strptime(yeardoy, '%Y%j').strftime('%Y_%m_%d')  # Convert YYYYDDD to MM_DD_YYYY
    
    if date not in file_dict:
        file_dict[date] = []
    file_dict[date].append(inFile)
    
    f = h5py.File(inFile, 'r') # Read in VIIRS HDF-EOS5 file and set to variable

    # List groups in file
    groups = list(f.keys())
    print(f"Groups in the file: {groups}")
     
    # List contents of HDFEOS group
    hdf_grids = list(f['HDFEOS']['GRIDS'].keys())
    print(f"Contents of HDFEOS/GRIDS: {hdf_grids}")
        
    # Access the specific dataset you need 
    evi_dataset = f['HDFEOS']['GRIDS']['VIIRS_Grid_16Day_VI_1km']

    list(f['HDFEOS']['GRIDS']['VIIRS_Grid_16Day_VI_1km']['Data Fields'])

    fileMetadata = f['HDFEOS INFORMATION']['StructMetadata.0'][()].decode('utf-8').split()  # Read file metadata

    h5_objs = []            # Create empty list
    f.visit(h5_objs.append) # Walk through directory tree, retrieve objects and append to list
    # Search for SDS with 1km or 500m grid
    all_datasets = [obj for grid in hdf_grids for obj in h5_objs if isinstance(f[obj], h5py.Dataset) and grid in obj]

    r = f[[a for a in all_datasets if 'EVI2' in a][0]]
    print(r)

    ulc = [i for i in fileMetadata if 'UpperLeftPointMtrs' in i][0]    # Search file metadata for the upper left corner of the file
    ulcLon = float(ulc.split('=(')[-1].replace(')', '').split(',')[0]) # Parse metadata string for upper left corner lon value
    ulcLat = float(ulc.split('=(')[-1].replace(')', '').split(',')[1]) # Parse metadata string for upper left corner lat value

    yRes, xRes = -926.6254330555555,  926.6254330555555 # Define the x and y resolution   
    geoInfo = (ulcLon, xRes, 0, ulcLat, 0, yRes)        # Define geotransform parameters

    prj = 'PROJCS["unnamed",\
    GEOGCS["Unknown datum based upon the custom spheroid", \
    DATUM["Not specified (based on custom spheroid)", \
    SPHEROID["Custom spheroid",6371007.181,0]], \
    PRIMEM["Greenwich",0],\
    UNIT["degree",0.0174532925199433]],\
    PROJECTION["Sinusoidal"], \
    PARAMETER["longitude_of_center",0], \
    PARAMETER["false_easting",0], \
    PARAMETER["false_northing",0], \
    UNIT["Meter",1]]'
    print(prj)

    data = r[()] # Extract data array
    fillValue = r.attrs['_FillValue'][0] # Extract fill value attribute

    outputName = os.path.join(outDir, '{}_{}.tif'.format(outName, date))
    nRow, nCol = data.shape[0], data.shape[1]                                  # Define rows/cols from array size
    dataType = gdal_array.NumericTypeCodeToGDALTypeCode(data.dtype)             # Define output data type
    driver = gdal.GetDriverByName('GTiff')
    
    try:
        outFile = driver.Create(outputName, nCol, nRow, 1, dataType)            # Specify parameters of the GeoTIFF
        if outFile is None:
            raise RuntimeError(f"Failed to create output file: {outputName}")
        band = outFile.GetRasterBand(1)                                         # Get band 1
        band.WriteArray(data)                                                   # Write data array to band 1
        band.FlushCache()                                                       # Export data
        band.SetNoDataValue(float(fillValue))                                   # Set fill value
        outFile.SetGeoTransform(geoInfo)                                        # Set Geotransform
        outFile.SetProjection(prj)                                              # Set projection
        outFile = None                                                          # Close file
        print('Processing: {}'.format(outputName)) 
    except RuntimeError as e:
        print(f"Error: {e}")
    
    f.close()  # Close the HDF5 file

print("All files processed.")


for date, file_list in file_dict.items():
    tiff_files = [os.path.join(outDir, f"{os.path.splitext(os.path.basename(f))[0]}_{date}.tif") for f in file_list]
    print(tiff_files)
    
    if len(tiff_files) > 1:
        mosaic_name = os.path.join( f"mosaic_{date}.tif")
        
        arcpy.MosaicToNewRaster_management(
            tiff_files,
            mosaicDir,
            mosaic_name,
            coordinate_system_for_the_raster="",
            pixel_type="32_BIT_FLOAT",
            cellsize="",
            number_of_bands=1,
            mosaic_method="LAST",
            mosaic_colormap_mode="FIRST"
        )
        print(f"Mosaic created for date {date}: {mosaic_name}")
        
        # Pause to ensure the mosaic file is written to disk
        time.sleep(1)  # Adjust the sleep time as needed

        mosaic_name = os.path.join(mosaicDir, f"mosaic_{date}.tif")
        
        # Check if the mosaic file exists before clipping
        if os.path.exists(mosaic_name):
            clipped_mosaic_name = os.path.join(clippedMosaicDir, f"clipped_mosaic_{date}.tif")
            
            arcpy.management.Clip(
                mosaic_name, 
                "#", 
                clipped_mosaic_name, 
                california_shapefile, 
                "#", 
                "ClippingGeometry", 
                "NO_MAINTAIN_EXTENT"
            )
            
            print(f"Clipped mosaic created for date {date}: {clipped_mosaic_name}")
        else:
            print(f"Error: Mosaic file {mosaic_name} does not exist.")
        
print("Mosaicking complete.")
