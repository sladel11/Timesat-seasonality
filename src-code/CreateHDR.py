import os

def create_envi_header(file_path):
    """Generate an ENVI header file for the given file path."""
    header_content = (
        "ENVI\n"
        " description = {{{}}}\n".format(file_path) +
        "samples = 998\n"
        "lines = 966\n"
        "bands = 1\n"
        "header offset = 0\n"
        "file type = ENVI Standard\n"
        "data type = 4\n"
        "interleave = bsq\n"
        "byte order = 0\n"
        "map info = {WGS 84, 1, 1, -12010740.280, 4902383.786,  1000.895023349560006, 1000.895023349560006}\n"
        "coordinate system string = {PROJCS[\"WGS_1984_EASE-Grid_2.0_Global\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Behrmann\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",0.0],PARAMETER[\"Standard_Parallel_1\",30.0],UNIT[\"Meter\",1.0]]}\n"
        "Pixel Size = (1000.895023349560006,-1000.895023349560006)"
        "band names = {Band 1}\n"
        "data ignore value = -2"
    )
    
    # Construct header file path
    header_file_path = file_path + '.hdr'
    
    # Write header content to the file
    with open(header_file_path, 'w') as header_file:
        header_file.write(header_content)
    
    print(f"Header file created: {header_file_path}")

def generate_headers_for_smap_files(folder_path):
    """Generate ENVI header files for all  files in the given folder."""
    for filename in os.listdir(folder_path):
        if not filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            create_envi_header(file_path)

# Replace with the path to your folder containing ENVI files
folder_path = r'path/to/files'
generate_headers_for_smap_files(folder_path)
