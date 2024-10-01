# Timesat-seasonality

access to data used
[SMAP SM](https://nsidc.org/data/nsidc-0779/versions/1)

## Part 1. SMAP data preprocessing

### 1. Clipping GeoTIFF
The image file contains data for the whole world, reducing the file size for analysis will be a more effective approach.

original GeoTIFF file           |  Clipped GeoTIFF fille
:-------------------------:|:-------------------------:
![](images/OriginalTIFSMAP.png)  |  ![](images/clippedtifCA.png)

[Code for clipping to your extent](src-code/cliptif.py)

### 2. Converting to Band interleaved by line (BIL)
TIMESAT can only process specific file tyoes including BIL and not TIF, so we will have to convert the images. 
Also, there are two bands, one for the ascending path of the L band radiometer and one for the descending path.
These bands will have to be seperated during the BIL conversion. 

[Code for conversion to bil](src-code/TifToBILSMAP.py)

[More information on BIL files](https://desktop.arcgis.com/en/arcmap/latest/manage-data/raster-and-images/bil-bip-and-bsq-raster-files.htm)

Confirm the conversion is successful by using [TIMESAT](https://web.nateko.lu.se/timesat/timesat.asp)

 *TSM_Imageviewer* allows you to look at your image.
Determine the number of rows and columns by looking at the header file of the bil file
Also, for the image file type look under n bits

![]()

 

