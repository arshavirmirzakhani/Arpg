import os
import toml

def is_directory_empty(path):
    return os.path.isdir(path) and not os.listdir(path)

def create_assets(path):
    os.makedirs(path + "/assets", exist_ok=True)

def create_global(path):
    os.makedirs(path + "/global", exist_ok=True)
    
def create_project(path):
    create_assets(path)
    create_global(path)
    
    with open(path+"/project.toml", "w", encoding="utf-8") as f:
        data = {
            "name": "new project",
            "version": "1.0.0",
            "window_title": "game title"
        }
        toml.dump(data, f)