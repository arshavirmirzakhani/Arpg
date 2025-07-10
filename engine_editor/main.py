from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from sympy import im
import toml
import sys
import os
import zipfile
import glob

from project import *
from projecteditor import ProjectEditor
from imageviewer import ImageViewer
from spritesheeteditor import SpritesheetEditor

import qdarkstyle

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Arpg Editor")
        self.setWindowState(Qt.WindowState.WindowMaximized)

        # Toolbar
        self.toolbar = self.addToolBar("Toolbar")

        self.open_project_action = QPushButton("Open", self)
        self.open_project_action.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen))
        self.open_project_action.clicked.connect(self.open_project_directory_dialog)
        self.toolbar.addWidget(self.open_project_action)
        
        self.new_project_action = QPushButton("New", self)
        self.new_project_action.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew))
        self.new_project_action.clicked.connect(self.new_project_directory_dialog)
        self.toolbar.addWidget(self.new_project_action)

        self.save_action = QPushButton("Save", self)
        self.save_action.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave))
        self.save_action.clicked.connect(self.save_project)
        self.toolbar.addWidget(self.save_action)
        
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_project)
        
        self.export_action = QPushButton("Export", self)
        self.export_action.setIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSend))
        self.export_action.clicked.connect(self.export_project)
        self.toolbar.addWidget(self.export_action)


        # Assets tree
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)
        self.model.setRootPath("")

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(QModelIndex())
        self.tree_view.clicked.connect(self.on_tree_item_clicked)

        # Main content area as tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # Dock widget for assets
        self.assets_dock_widget = QDockWidget("Assets", self)
        self.assets_dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.assets_dock_widget.setWidget(self.tree_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.assets_dock_widget)

        self.current_project_path = ""

    def open_project_directory_dialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Folder", "")
        if not directory:
            return

        self.current_project_path = directory
        
        project_cfg_path = os.path.join(directory, "project.toml")

        if os.path.isfile(project_cfg_path) and self.is_valid_project_config(project_cfg_path):
            self.model.setRootPath(directory)
            self.tree_view.setRootIndex(self.model.index(directory))
            self.current_project_path = directory
        else:
            QMessageBox.warning(
                self,
                "Invalid Project",
                "The selected folder does not contain a valid 'project.toml' file."
            )
            self.tree_view.setRootIndex(QModelIndex())

    def new_project_directory_dialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Folder", "")
        if not directory:
            return


        if not is_directory_empty(directory):
            QMessageBox.warning(
                self,
                "Directory is not empty",
                "The selected folder is not empty."
            )
            self.tree_view.setRootIndex(QModelIndex())          
            return

        create_project(directory)

        self.model.setRootPath(directory)
        self.tree_view.setRootIndex(self.model.index(directory))
        self.current_project_path = directory
        
            
    def is_valid_project_config(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = toml.load(f)
            return "name" in data and "version" in data
        except Exception as e:
            return False

    def on_tree_item_clicked(self, index: QModelIndex):
        file_path = self.model.filePath(index)

        if not os.path.isfile(file_path):
            return  # Ignore directories

        if os.path.basename(file_path) == "project.toml":
            self.open_project_toml_tab(file_path)
        elif (self.current_project_path + "/assets") in file_path and self.is_image_file(file_path):
            self.open_image_tab(file_path)

    def is_image_file(self, file_path):
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
        return file_path.lower().endswith(image_extensions)

    def open_image_tab(self, path):
        # Check if tab already open
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, ImageViewer) and widget.image_path == path:
                self.tab_widget.setCurrentIndex(i)
                return

        #viewer = ImageViewer(path)
        viewer = SpritesheetEditor(path)
        self.tab_widget.addTab(viewer, os.path.basename(path))
        self.tab_widget.setCurrentWidget(viewer)

    def open_project_toml_tab(self, path):
        # Check if the tab is already open
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "project.toml":
                self.tab_widget.setCurrentIndex(i)
                return

        editor = ProjectEditor(path)
        self.tab_widget.addTab(editor, "project.toml")
        self.tab_widget.setCurrentWidget(editor)

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)

        if hasattr(widget, "is_modified") and widget.is_modified():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "This tab has unsaved changes. Do you want to save before closing?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            elif reply == QMessageBox.Yes and hasattr(widget, "save"):
                widget.save()

        self.tab_widget.removeTab(index)

    def save_project(self):
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, "save") and callable(getattr(widget, "save")):
                widget.save()
            else:
                pass
        
        QMessageBox.information(self, "Saved", "project saved successfully.")

    def export_project(self):
        with zipfile.ZipFile(self.current_project_path + "/data.arpg","w") as zip:
            zip.write(self.current_project_path + "/project.toml","project.toml")
            
            zip.writestr("global/","")
            for file in glob.iglob(self.current_project_path + "/global/*.toml"):
                zip.write(file,file[len(self.current_project_path):])

            zip.writestr("stages/","")
            for file in glob.iglob(self.current_project_path + "/stages/*.toml"):
                zip.write(file,file[len(self.current_project_path):])
                
            zip.writestr("actors/","")
            for file in glob.iglob(self.current_project_path + "/actors/*.toml"):
                zip.write(file,file[len(self.current_project_path):])
              
            zip.writestr("assets/","")  
            for file in glob.iglob(self.current_project_path + "/assets/*"):
                zip.write(file,file[len(self.current_project_path):])
        
        QMessageBox.information(self, "Export", "project exported successfully.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.exec()