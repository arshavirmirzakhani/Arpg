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
            snapped_x = round(value.x())
            snapped_y = round(value.y())
            snapped_pos = QPointF(snapped_x, snapped_y)

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
        self._drag_start_pos = None

        self.setMouseTracking(True)

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        self.view = GraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing, False)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.cursorMoved.connect(self.update_coordinates)

        self.pixmap = QPixmap(self.image_path)
        if self.pixmap.isNull():
            QMessageBox.critical(self, "Error", "Failed to load image.")
            return

        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(
            self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-2)
        self.scene.addItem(self.checker_item)

        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.pixmap_item.setZValue(-1)
        self.scene.addItem(self.pixmap_item)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.view)

        self.coord_label = QLabel("Mouse: ")
        left_layout.addWidget(self.coord_label)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, stretch=1)

        self.tile_width_spin = QSpinBox()
        self.tile_width_spin.setRange(1, 1024)
        self.tile_width_spin.setValue(16)
        self.tile_width_spin.valueChanged.connect(self.update_selection_rect)

        self.tile_height_spin = QSpinBox()
        self.tile_height_spin.setRange(1, 1024)
        self.tile_height_spin.setValue(16)
        self.tile_height_spin.valueChanged.connect(self.update_selection_rect)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Sprite Width:"))
        right_panel.addWidget(self.tile_width_spin)
        right_panel.addWidget(QLabel("Sprite Height:"))
        right_panel.addWidget(self.tile_height_spin)
        right_panel.addStretch()

        main_layout.addLayout(right_panel)

        self.selection_rect = MovableRect()
        self.selection_rect.setPen(QPen(Qt.red, 0))
        self.selection_rect.setBrush(QColor(255, 0, 0, 50))
        self.selection_rect.set_position_callback(self.on_rect_moved)
        self.scene.addItem(self.selection_rect)
        self.update_selection_rect()

    def generate_checkerboard_pixmap(self, width, height, tile_size=8):
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        light = QColor(200, 200, 200)
        dark = QColor(150, 150, 150)

        painter = QPainter(pixmap)
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
            self.coord_label.setText(f"Mouse: ({x}, {y}) | Rect: ({self.selection_rect.pos().toPoint().x()}, {self.selection_rect.pos().toPoint().x()})")
        else:
            self.coord_label.setText("Mouse: Out of bounds")

    def is_modified(self) -> bool:
        return self.modified

    def save(self):
        pass

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self._zoom *= 1.25
        else:
            self._zoom *= 0.8
        self.view.resetTransform()
        self.view.scale(self._zoom, self._zoom)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = True
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.pos() - self._drag_start_pos
            self._drag_start_pos = event.pos()
            self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().value() - delta.x())
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().value() - delta.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
