import os
import shutil
from pathlib import Path

# List all new directory's content
listOfDirectory = {
    "Picture_Folder": [".jpeg", ".jpg", ".gif", ".png"],
    "Video_Folder": [".wmv", ".mov", ".mp4",".mpg", ".mpeg", ".mkv"],
    "Zip_Folder": [".iso", ".tar", ".gz", ".rz", ".7z",".dmg",".rar", ".zip"],
    "Music_Folder": [".mp3", ".msv",".wav", ".wma"],
    "PDF_Folder": [".pdf"],
    "Text_Folder": [".txt", ".in", ".out", ".log", ".md"],
}

def organize_files(target_dir):
    """
    Organizes files in the target_dir into subdirectories based on their extensions.
    """
    path = Path(target_dir)
    
    # Iterate through all files in the target directory
    for file_path in path.iterdir():
        # Skip directories and the script itself
        if file_path.is_file() and file_path.name != 'main.py':
            file_extension = file_path.suffix.lower()
            
            # Find the appropriate folder for this file
            for folder_name, extensions in listOfDirectory.items():
                if file_extension in extensions:
                    target_folder = path / folder_name
                    destination = target_folder / file_path.name
                    
                    # Create the folder only if we have a file to put in it
                    target_folder.mkdir(exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(file_path), str(destination))
                    print(f"Moved '{file_path.name}' to '{folder_name}'")
                    break

if __name__ == "__main__":
    while True:
        target_directory = input("Enter the directory path to organize: ").strip()
        if os.path.isdir(target_directory):
            break
        print("Error: The specified path is not a valid directory. Please try again.")

    print(f"Organizing files in: {target_directory}")
    organize_files(target_directory)
    print("Done organizing!")
