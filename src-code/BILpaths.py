import os
import arcpy

def find_bil_files(directory, output_file_band1, output_file_band2):
    # Lists to store paths of .bil files
    band1_files = []
    band2_files = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('band1.bil'):
                # Get the full path of the band1.bil file
                full_path = os.path.join(root, file)
                band1_files.append(full_path)
            elif file.endswith('band2.bil'):
                # Get the full path of the band2.bil file
                full_path = os.path.join(root, file)
                band2_files.append(full_path)
    
    # Write the paths to the output file for band1.bil
    with open(output_file_band1, 'w') as f_band1:
        for path in band1_files:
            f_band1.write(f"{path}\n")

    # Write the paths to the output file for band2.bil
    with open(output_file_band2, 'w') as f_band2:
        for path in band2_files:
            f_band2.write(f"{path}\n")
    
    return len(band1_files), len(band2_files)


# Example usage
directory_to_search = r"C:\Users\laszews\Documents\Thesis"
output_file_path_band1 = r'textfile\for\bil\paths1'
output_file_path_band2 = r'textfile\for\bil\paths2'

band1_count, band2_count = find_bil_files(directory_to_search, output_file_path_band1, output_file_path_band2)

print(f"Band1 files written: {band1_count}")
print(f"Band2 files written: {band2_count}")


print("done")
