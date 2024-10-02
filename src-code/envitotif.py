import os
import rasterio

def convert_envi_to_geotiff(envi_file_path, geotiff_file_path):
    """Convert a single ENVI file to GeoTIFF format."""
    with rasterio.open(envi_file_path) as src:
        data = src.read(1)  # Assuming single band
        metadata = src.meta
        
        # Print metadata for verification (optional)
        print("Metadata read from ENVI file:")
        print(metadata)

        with rasterio.open(geotiff_file_path, 'w', **metadata) as dst:
            dst.write(data, 1)  # Write the data to the first band

    print(f"GeoTIFF file created: {geotiff_file_path}")

def batch_convert_envi_folder(input_folder, output_folder):
    """Convert all ENVI files in a folder to GeoTIFF format."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # Create output folder if it does not exist

    for file_name in os.listdir(input_folder):
        if not file_name.endswith('.hdr'):
            envi_file_path = os.path.join(input_folder, file_name)
            geotiff_file_name = file_name + '.tif'  # Add '.tif' extension
            geotiff_file_path = os.path.join(output_folder, geotiff_file_name)
            
            convert_envi_to_geotiff(envi_file_path, geotiff_file_path)

# Example usage
input_folder = r""  # Folder containing ENVI files
output_folder = r""  # Folder to save GeoTIFF files

batch_convert_envi_folder(input_folder, output_folder)
