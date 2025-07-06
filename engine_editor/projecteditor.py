from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import toml


class ProjectEditor(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.modified = False

        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.version_input = QLineEdit()
        self.window_title_input = QLineEdit()        

        # Connect signals
        self.name_input.textChanged.connect(self.mark_modified)
        self.version_input.textChanged.connect(self.mark_modified)
        self.window_title_input.textChanged.connect(self.mark_modified)


        self.layout.addRow("Project Name:", self.name_input)
        self.layout.addRow("Version:", self.version_input)
        self.layout.addRow("Window Title:",self.window_title_input)


        self.load_from_file()

    def load_from_file(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = toml.load(f)

            # Block signals to avoid setting modified during initial load
            self.name_input.blockSignals(True)
            self.version_input.blockSignals(True)
            self.window_title_input.blockSignals(True)

            self.name_input.setText(data.get("name", ""))
            self.version_input.setText(data.get("version", "")) 
            self.window_title_input.setText(data.get("window_title", "")) 

            self.name_input.blockSignals(False)
            self.version_input.blockSignals(False)
            self.window_title_input.blockSignals(False)

            self.modified = False  # Reset after loading

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project.toml:\n{e}")

    def mark_modified(self):
        self.modified = True

    def is_modified(self):
        return self.modified

    def save(self):
        try:
            data = {
                "name": self.name_input.text(),
                "version": self.version_input.text(),
                "window_title": self.window_title_input.text()

            }

            with open(self.path, "w", encoding="utf-8") as f:
                toml.dump(data, f)

            self.modified = False  # Reset after saving
            

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
