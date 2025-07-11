from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from editorwidget import EditorWidget, GraphicsView
import toml
import os

class AnimationState:
    def __init__(self, name, fps=12):
        self.name = name
        self.fps = fps
        self.frames = []

    def add_frame(self, pos: QPointF):
        self.frames.append(pos)

    def remove_frame(self, index: int):
        if 0 <= index < len(self.frames):
            del self.frames[index]

    def rename(self, new_name):
        self.name = new_name


class MovableRect(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        self.callback = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            snapped_pos = QPointF(round(value.x()), round(value.y()))
            if self.callback:
                self.callback(snapped_pos)
            return snapped_pos
        return super().itemChange(change, value)

    def set_position_callback(self, callback):
        self.callback = callback


class SpritesheetEditor(QWidget, EditorWidget):
    def __init__(self, toml_path,project_path):
        super().__init__()
        self.toml_path = toml_path
        self.project_path = project_path
        self.image_path = ""
        self.modified = False
        self._zoom = 1.0
        self._dragging = False
        self.anim_states: dict[str, AnimationState] = {}

        self.setup_ui()

        self.pixmap = QPixmap(self.image_path)
        if self.pixmap.isNull():
            pass
        
        self.update_selection_rect()
        
        self.load()

    def setup_ui(self):
        self.setWindowTitle("Spritesheet Editor")

        # --- Splitter for main layout ---
        main_splitter = QSplitter(Qt.Horizontal)
        layout = QHBoxLayout(self)
        layout.addWidget(main_splitter)
        self.setLayout(layout)

        # --- Left Panel (Animation Controls) ---
        self.add_anim_btn = QPushButton("Add Animation")
        self.remove_anim_btn = QPushButton("Remove Animation")
        self.rename_anim_btn = QPushButton("Rename Animation")

        self.add_anim_btn.clicked.connect(self.add_animation_state)
        self.remove_anim_btn.clicked.connect(self.remove_animation_state)
        self.rename_anim_btn.clicked.connect(self.rename_animation_state)

        self.anim_list = QListWidget()
        self.anim_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.anim_list.currentItemChanged.connect(lambda *_: self.on_animation_changed())

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Animation States:"))
        left_layout.addWidget(self.add_anim_btn)
        left_layout.addWidget(self.remove_anim_btn)
        left_layout.addWidget(self.rename_anim_btn)
        left_layout.addWidget(self.anim_list)
        left_layout.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(120)  # Optional: prevent collapse

        # --- Center Panel (Graphics View + Frame List) ---
        center_layout = QVBoxLayout()

        self.view = GraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing, False)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.cursorMoved.connect(self.update_coordinates)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.pixmap = QPixmap(self.image_path)
        if self.pixmap.isNull():
            pass

        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(
            self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-2)
        self.scene.addItem(self.checker_item)

        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.pixmap_item.setZValue(-1)
        self.scene.addItem(self.pixmap_item)

        center_layout.addWidget(self.view)

        self.coord_label = QLabel("Mouse: ")
        center_layout.addWidget(self.coord_label)

        self.frames_list = QListWidget()
        self.frames_list.setFixedHeight(64)
        self.frames_list.setViewMode(QListView.IconMode)
        self.frames_list.setIconSize(QSize(48, 48))
        self.frames_list.setResizeMode(QListWidget.Adjust)
        self.frames_list.setMovement(QListWidget.Static)
        self.frames_list.setSpacing(4)

        self.add_frame_btn = QPushButton("Add Frame")
        self.remove_frame_btn = QPushButton("Remove Frame")

        self.add_frame_btn.clicked.connect(self.add_frame)
        self.remove_frame_btn.clicked.connect(self.remove_frame)
        self.frames_list.currentRowChanged.connect(self.select_frame)

        center_layout.addWidget(QLabel("Frames:"))
        center_layout.addWidget(self.frames_list)

        frame_btns_layout = QHBoxLayout()
        frame_btns_layout.addWidget(self.add_frame_btn)
        frame_btns_layout.addWidget(self.remove_frame_btn)
        center_layout.addLayout(frame_btns_layout)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # --- Right Panel (Settings) ---
        
        self.load_image_btn = QPushButton("Load Image")
        self.load_image_btn.clicked.connect(self.load_image)        
        
        self.tile_width_spin = QSpinBox()
        self.tile_width_spin.setRange(1, 1024)
        self.tile_width_spin.setValue(16)
        self.tile_width_spin.valueChanged.connect(self.update_selection_rect)

        self.tile_height_spin = QSpinBox()
        self.tile_height_spin.setRange(1, 1024)
        self.tile_height_spin.setValue(16)
        self.tile_height_spin.valueChanged.connect(self.update_selection_rect)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(12)
        self.fps_spin.setSuffix(" FPS")
        
        self.fps_spin.valueChanged.connect(self.on_fps_changed)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.load_image_btn)
        right_layout.addSpacing(10)
        right_layout.addWidget(QLabel("Sprite Width:"))
        right_layout.addWidget(self.tile_width_spin)
        right_layout.addWidget(QLabel("Sprite Height:"))
        right_layout.addWidget(self.tile_height_spin)
        right_layout.addSpacing(10)
        right_layout.addWidget(QLabel("Animation FPS:"))
        right_layout.addWidget(self.fps_spin)
        right_layout.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setMinimumWidth(100)

        # --- Add all panels to splitter ---
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(center_widget)
        main_splitter.addWidget(right_widget)

        main_splitter.setStretchFactor(0, 0)  # Left panel
        main_splitter.setStretchFactor(1, 1)  # Center (main focus)
        main_splitter.setStretchFactor(2, 0)  # Right panel

        main_splitter.setSizes([150, 800, 120])

        # --- Selection Rectangle ---
        self.selection_rect = MovableRect()
        self.selection_rect.setPen(QPen(QColor(0, 0, 255, 255), 0))
        self.selection_rect.setBrush(QColor(0, 0, 255, 50))
        self.selection_rect.set_position_callback(self.on_rect_moved)
        self.scene.addItem(self.selection_rect)
        self.update_selection_rect()

        # --- Animation Frame Storage ---
        self.anim_frames = {}

    def load_image(self):
        dialog = QFileDialog(self, "Select Spritesheet Image", self.project_path + "/assets")
        dialog.setNameFilter("Images (*.png *.jpg *.bmp *.gif)")
        dialog.setFileMode(QFileDialog.ExistingFile)

        if dialog.exec():
            selected = dialog.selectedFiles()[0]
            if selected.startswith(self.project_path + "/assets"):
                self.image_path = selected
                self.pixmap = QPixmap(self.image_path)
                if not self.pixmap.isNull():
                    self.update_image_scene()
                    self.modified = True
            else:
                QMessageBox.warning(self, "Invalid Selection", "Please select an image from within the 'assets' directory.")

    def update_image_scene(self):
        self.scene.removeItem(self.pixmap_item)
        self.scene.removeItem(self.checker_item)

        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(
            self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-2)
        self.scene.addItem(self.checker_item)

        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.pixmap_item.setZValue(-1)
        self.scene.addItem(self.pixmap_item)

    def generate_checkerboard_pixmap(self, width, height, tile_size=8):
        if width <= 0 or height <= 0:
            return QPixmap()  
        
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        light, dark = QColor(200, 200, 200), QColor(150, 150, 150)
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                color = light if ((x // tile_size + y // tile_size) % 2 == 0) else dark
                painter.fillRect(x, y, tile_size, tile_size, color)
        painter.end()
        return pixmap

    def update_selection_rect(self):
        w, h = self.tile_width_spin.value(), self.tile_height_spin.value()
        self.selection_rect.setRect(0, 0, w, h)

    def on_rect_moved(self, pos: QPointF):
        self.coord_label.setText(f"Selection Rect Position: ({int(pos.x())}, {int(pos.y())})")
        anim = self.get_current_animation()
        index = self.frames_list.currentRow()
        if anim and 0 <= index < len(anim.frames):
            anim.frames[index] = pos
            self.modified = True

    def on_animation_changed(self):
        anim = self.get_current_animation()
        if not anim:
            return
        self.fps_spin.blockSignals(True)
        self.fps_spin.setValue(anim.fps)
        self.fps_spin.blockSignals(False)

        self.frames_list.clear()
        for i, _ in enumerate(anim.frames):
            self.frames_list.addItem(f"Frame {i + 1}")
            
        if anim.frames:
            self.frames_list.setCurrentRow(0) 

    def on_fps_changed(self, fps):
        anim = self.get_current_animation()
        if anim:
            anim.fps = fps
            self.modified = True

    def get_current_animation(self) -> AnimationState | None:
        item = self.anim_list.currentItem()
        if not item:
            return None
        return self.anim_states.get(item.text())

    def add_animation_state(self):
        name, ok = QInputDialog.getText(self, "Add Animation", "Enter animation name:")
        if ok and name and name not in self.anim_states:
            anim = AnimationState(name)
            self.anim_states[name] = anim
            self.anim_list.addItem(name)
            self.frames_list.clear()
            self.modified = True

    def remove_animation_state(self):
        row = self.anim_list.currentRow()
        if row >= 0:
            name = self.anim_list.item(row).text()
            del self.anim_states[name]
            self.anim_list.takeItem(row)
            self.frames_list.clear()
            self.modified = True

    def rename_animation_state(self):
        item = self.anim_list.currentItem()
        if not item:
            return
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Animation", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            if new_name in self.anim_states:
                QMessageBox.warning(self, "Duplicate", f"Animation '{new_name}' already exists.")
                return
            anim = self.anim_states.pop(old_name)
            anim.rename(new_name)
            self.anim_states[new_name] = anim
            item.setText(new_name)
            self.modified = True

    def add_frame(self):
        anim = self.get_current_animation()
        if anim:
            pos = self.selection_rect.pos()
            anim.add_frame(pos)
            self.frames_list.addItem(f"Frame {len(anim.frames)}")
            self.modified = True

    def remove_frame(self):
        anim = self.get_current_animation()
        index = self.frames_list.currentRow()
        if anim and 0 <= index < len(anim.frames):
            anim.remove_frame(index)
            self.frames_list.takeItem(index)
            self.modified = True

    def select_frame(self, index):
        anim = self.get_current_animation()
        if anim and 0 <= index < len(anim.frames):
            self.selection_rect.setPos(anim.frames[index])

    def update_coordinates(self, scene_pos: QPointF):
        image_pos = self.pixmap_item.mapFromScene(scene_pos)
        x, y = int(image_pos.x()), int(image_pos.y())
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            rect_pos = self.selection_rect.pos()
            self.coord_label.setText(f"Mouse: ({x}, {y}) | Rect: ({rect_pos.x()}, {rect_pos.y()})")
        else:
            self.coord_label.setText("Mouse: Out of bounds")

    def wheelEvent(self, event: QWheelEvent):
        self._zoom *= 1.25 if event.angleDelta().y() > 0 else 0.8
        self.view.resetTransform()
        self.view.scale(self._zoom, self._zoom)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._dragging = True
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.pos() - self._drag_start_pos
            self._drag_start_pos = event.pos()
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def is_modified(self) -> bool:
        return self.modified

    def load(self):
        if not os.path.exists(self.toml_path):
            return

        with open(self.toml_path, "r") as f:
            data = toml.load(f)

        rel_image_path = data.get("image_path", "")
        abs_image_path = os.path.join(self.project_path, "assets", rel_image_path)
        if os.path.exists(abs_image_path):
            self.image_path = abs_image_path
            self.pixmap = QPixmap(self.image_path)
            if not self.pixmap.isNull():
                self.update_image_scene()

        self.tile_width_spin.setValue(data.get("width", 16))
        self.tile_height_spin.setValue(data.get("height", 16))
        self.fps_spin.setValue(data.get("fps", 12))

        self.anim_states.clear()
        self.anim_list.clear()
        self.frames_list.clear()

        states = data.get("states", {})
        for name, state_data in states.items():
            anim = AnimationState(name)
            for frame in state_data.get("frames", []):
                if isinstance(frame, list) and len(frame) == 2:
                    pos = QPointF(frame[0], frame[1])
                    anim.add_frame(pos)
            self.anim_states[name] = anim
            self.anim_list.addItem(name)

        if self.anim_list.count() > 0:
            self.anim_list.setCurrentRow(0)

        self.modified = False


    def save(self):
        if not self.image_path:
            QMessageBox.warning(self, "Save Error", "No image loaded.")
            return

        rel_image_path = os.path.relpath(self.image_path, self.project_path + "/assets").replace("\\", "/")

        data = {
            "image_path": rel_image_path,
            "fps": self.fps_spin.value(),
            "width": self.tile_width_spin.value(),
            "height": self.tile_height_spin.value(),
            "states": {}
        }

        for name, anim in self.anim_states.items():
            frames = []
            for frame in anim.frames:
                frames.append([int(frame.x()), int(frame.y())])
            data["states"][name] = {"frames": frames}

        with open(self.toml_path, "w") as f:
            toml.dump(data, f)

        self.modified = False

