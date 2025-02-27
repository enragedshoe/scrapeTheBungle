import os
import shutil

def move_project_contents(old_project, new_project_root):
    """
    Moves all files and folders from the old_project directory up to new_project_root.
    """
    if not os.path.exists(old_project):
        print(f"Directory {old_project} does not exist. Exiting.")
        return
    
    # List contents of the old project folder and move them to the new root
    for item in os.listdir(old_project):
        src_path = os.path.join(old_project, item)
        dest_path = os.path.join(new_project_root, item)
        print(f"Moving '{src_path}' to '{dest_path}'")
        shutil.move(src_path, dest_path)
    
    # Remove the old project folder once it is empty
    try:
        os.rmdir(old_project)
        print(f"Removed empty folder: {old_project}")
    except Exception as e:
        print(f"Error removing folder {old_project}: {e}")

def update_internal_references(root_dir, old_name, new_name):
    """
    Recursively searches for .py files in root_dir and replaces occurrences of old_name with new_name.
    Use this if your code contains explicit references to the old folder name.
    """
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(subdir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    new_content = content.replace(old_name, new_name)
                    if new_content != content:
                        print(f"Updating references in {file_path}")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

def main():
    # Make sure to run this script from F:\Projects\scrapeTheBungle
    root_dir = os.getcwd()  
    old_project_folder = os.path.join(root_dir, "scrapeTheBungle")
    
    print("Moving project contents...")
    move_project_contents(old_project_folder, root_dir)
    
    # Optionally, update internal references if any .py file mentions "scrapeTheBungle"
    print("Updating internal references from 'scrapeTheBungle' to 'scrapeTheBungle'...")
    update_internal_references(root_dir, "scrapeTheBungle", "scrapeTheBungle")
    
    print("\nProject has been restructured. The project is now named 'scrapeTheBungle' in the root directory.")

if __name__ == "__main__":
    main()
