from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from editorwidget import EditorWidget, GraphicsView


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
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.modified = False
        self._zoom = 1.0
        self._dragging = False

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # --- Left Panel (Animation Controls) ---
        self.add_anim_btn = QPushButton("Add Animation")
        self.remove_anim_btn = QPushButton("Remove Animation")
        self.rename_anim_btn = QPushButton("Rename Animation")

        self.add_anim_btn.clicked.connect(self.add_animation_state)
        self.remove_anim_btn.clicked.connect(self.remove_animation_state)
        self.rename_anim_btn.clicked.connect(self.rename_animation_state)

        self.anim_list = QListWidget()
        self.anim_list.setSelectionMode(QAbstractItemView.SingleSelection)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Animation States:"))
        left_layout.addWidget(self.add_anim_btn)
        left_layout.addWidget(self.remove_anim_btn)
        left_layout.addWidget(self.rename_anim_btn)
        left_layout.addWidget(self.anim_list)
        left_layout.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)

        # --- Center Panel ---
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
            QMessageBox.critical(self, "Error", "Failed to load image.")
            return

        # Background Checkerboard
        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(
            self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-2)
        self.scene.addItem(self.checker_item)

        # Foreground Image
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.pixmap_item.setZValue(-1)
        self.scene.addItem(self.pixmap_item)

        center_layout.addWidget(self.view)

        # Mouse/Rect Position Label
        self.coord_label = QLabel("Mouse: ")
        center_layout.addWidget(self.coord_label)

        # --- Frames Panel ---
        self.frames_list = QListWidget()
        self.frames_list.setFixedHeight(64)  # Reduced height
        self.frames_list.setViewMode(QListView.IconMode)
        self.frames_list.setIconSize(QSize(48, 48))  # Slightly smaller icons
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
        main_layout.addWidget(center_widget, stretch=1)

        # --- Right Panel ---
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

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Sprite Width:"))
        right_panel.addWidget(self.tile_width_spin)
        right_panel.addWidget(QLabel("Sprite Height:"))
        right_panel.addWidget(self.tile_height_spin)
        right_panel.addSpacing(10)
        right_panel.addWidget(QLabel("Animation FPS:"))
        right_panel.addWidget(self.fps_spin)
        right_panel.addStretch()
        main_layout.addLayout(right_panel)

        # --- Selection Rectangle ---
        self.selection_rect = MovableRect()
        self.selection_rect.setPen(QPen(QColor(0, 0, 255, 255), 0))
        self.selection_rect.setBrush(QColor(0, 0, 255, 50))
        self.selection_rect.set_position_callback(self.on_rect_moved)
        self.scene.addItem(self.selection_rect)
        self.update_selection_rect()

        # --- Animation Frame Storage ---
        self.anim_frames = {}  # {animation_name: [QPointF, ...]}

    def generate_checkerboard_pixmap(self, width, height, tile_size=8):
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
        w = self.tile_width_spin.value()
        h = self.tile_height_spin.value()
        self.selection_rect.setRect(0, 0, w, h)

    def on_rect_moved(self, pos: QPointF):
        x, y = int(pos.x()), int(pos.y())
        self.coord_label.setText(f"Selection Rect Position: ({x}, {y})")

    def update_coordinates(self, scene_pos: QPointF):
        image_pos = self.pixmap_item.mapFromScene(scene_pos)
        x, y = int(image_pos.x()), int(image_pos.y())
        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            rect_pos = self.selection_rect.pos()
            self.coord_label.setText(f"Mouse: ({x}, {y}) | Rect: ({rect_pos.x()}, {rect_pos.y()})")
        else:
            self.coord_label.setText("Mouse: Out of bounds")

    def is_modified(self) -> bool:
        return self.modified

    def save(self):
        # Placeholder for save logic
        pass

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
            self.view.horizontalScrollBar().setValue(
                self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def add_animation_state(self):
        name, ok = QInputDialog.getText(self, "Add Animation", "Enter animation name:")
        if ok and name:
            if name in self.anim_frames:
                QMessageBox.warning(self, "Duplicate", f"Animation '{name}' already exists.")
                return
            self.anim_list.addItem(name)
            self.anim_frames[name] = []
            self.frames_list.clear()
            self.modified = True

    def remove_animation_state(self):
        selected = self.anim_list.currentRow()
        if selected >= 0:
            name = self.anim_list.item(selected).text()
            del self.anim_frames[name]
            self.anim_list.takeItem(selected)
            self.frames_list.clear()
            self.modified = True

    def rename_animation_state(self):
        selected_item = self.anim_list.currentItem()
        if not selected_item:
            QMessageBox.information(self, "No Selection", "Select an animation to rename.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Animation", "Enter new name:", text=selected_item.text())
        if ok and new_name and new_name != selected_item.text():
            if new_name in self.anim_frames:
                QMessageBox.warning(self, "Duplicate", f"Animation '{new_name}' already exists.")
                return
            old_name = selected_item.text()
            self.anim_frames[new_name] = self.anim_frames.pop(old_name)
            selected_item.setText(new_name)
            self.modified = True

    def add_frame(self):
        current_item = self.anim_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Animation", "Select an animation first.")
            return
        name = current_item.text()
        pos = self.selection_rect.pos()
        self.anim_frames[name].append(pos)
        self.frames_list.addItem(f"Frame {len(self.anim_frames[name])}")
        self.modified = True

    def remove_frame(self):
        current_item = self.anim_list.currentItem()
        index = self.frames_list.currentRow()
        if current_item and index >= 0:
            name = current_item.text()
            del self.anim_frames[name][index]
            self.frames_list.takeItem(index)
            self.modified = True

    def select_frame(self, index):
        current_item = self.anim_list.currentItem()
        if current_item and index >= 0:
            name = current_item.text()
            frames = self.anim_frames.get(name, [])
            if 0 <= index < len(frames):
                pos = frames[index]
                self.selection_rect.setPos(pos)
