# Timesat-seasonality

access to data used
[SMAP SM](https://nsidc.org/data/nsidc-0779/versions/1)

## Part 1. SMAP data preprocessing

### Clipping tif 
The image file contains data for the whole world, reducing the file size for analysis will be a more effective approach.

original tif file           |  Clipped tif fille
:-------------------------:|:-------------------------:
![]()  |  ![](https://...Ocean.png)

[Code for clipping to your extent](src-code/cliptif.py)

