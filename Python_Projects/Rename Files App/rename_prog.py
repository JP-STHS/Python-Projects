import os
#Code taken from ChatGPT output
#Program that quickly modifies all files in a directory to be in sequential order;
#This is useful when dealing with sub-class folders with identical names that need to be placed in one large folder

def rename_files(directory):
    # Get a list of all files in the directory
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    
    # Rename each file to ensure unique names
    for index, file_path in enumerate(files):
        # Extract the file extension
        file_dir = os.path.dirname(file_path)
        file_ext = os.path.splitext(file_path)[1]
        
        # Create a new unique name
        new_name = f"image_{index+1}{file_ext}"
        new_path = os.path.join(file_dir, new_name)
        
        # Rename the file
        os.rename(file_path, new_path)
        print(f"Renamed: {file_path} -> {new_path}")

# Specify the directory containing the negative images
directory = "INSERT DIRECTORY HERE"

rename_files(directory)
