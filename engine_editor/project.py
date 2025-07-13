from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import os
import toml

SPRITESHEET_TYPES = ["none", "four direction", "eight direction"]

DEFAULT_STATES = {
    "eight direction": [],
    "four direction": ["left_walk","right_walk","up_walk","down_walk","left_idle","right_idle","up_idle","down_idle"],
    "none": ["default"]
}

class NewSpritesheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Spritesheet")
        self.setModal(True)

        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("Name:", self.name_input)

        self.sprite_type_input = QComboBox()
        self.sprite_type_input.addItems(SPRITESHEET_TYPES)
        layout.addRow("Sprite Type:", self.sprite_type_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "type": self.sprite_type_input.currentText()
        }


def is_directory_empty(path):
    return os.path.isdir(path) and not os.listdir(path)

def create_spritsheets(path):
    os.makedirs(path + "/spritesheets", exist_ok=True)

def create_new_spritesheet(self, path):
    dialog = NewSpritesheetDialog(self)
    if dialog.exec() != QDialog.Accepted:
        return 

    data = dialog.get_data()
    name = data["name"]

    if not name:
        QMessageBox.warning(self, "Missing Name", "Spritesheet name cannot be empty.")
        return

    file_path = os.path.join(path + "/spritesheets/", f"{name}.toml")
    if os.path.exists(file_path):
        QMessageBox.warning(self, "Exists", "A spritesheet with same name already exists.")
        return

    spritesheet_data = {
        "name": name,
        "type": data["type"]
    }

    with open(file_path, "w", encoding="utf-8") as f:
        toml.dump(spritesheet_data, f)

    self.open_spritesheeteditor_tab(file_path)

def create_assets(path):
    os.makedirs(path + "/assets", exist_ok=True)

def create_global(path):
    os.makedirs(path + "/global", exist_ok=True)
    
def create_project(path):
    create_assets(path)
    create_global(path)
    create_spritsheets(path)
    
    with open(path+"/project.toml", "w", encoding="utf-8") as f:
        data = {
            "name": "new project",
            "version": "1.0.0",
            "window_title": "game title"
        }
        toml.dump(data, f)