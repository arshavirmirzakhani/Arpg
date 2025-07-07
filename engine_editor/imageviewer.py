from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from editorwidget import EditorWidget


# Custom QGraphicsView that emits a signal when the mouse moves
class GraphicsView(QGraphicsView):
    cursorMoved = Signal(QPointF)  # Emits scene position of cursor

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        self.cursorMoved.emit(scene_pos)


class ImageViewer(QWidget, EditorWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.modified = False

        self._zoom = 1.0
        self._dragging = False
        self._drag_start_pos = None

        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Use the custom view
        self.view = GraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing, False)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Connect the custom signal
        self.view.cursorMoved.connect(self.update_coordinates)

        # Check if image exists
        self.pixmap = QPixmap(self.image_path)
        if self.pixmap.isNull():
            QMessageBox.critical(self, "Error", "Failed to load image.")
            return

        # Checkerboard background
        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-1)
        self.scene.addItem(self.checker_item)

        # Image item
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.scene.addItem(self.pixmap_item)

        layout.addWidget(self.view)

        # Coordinate display
        self.coord_label = QLabel("Coordinates: ")
        layout.addWidget(self.coord_label)

        self.setLayout(layout)

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

    def update_coordinates(self, scene_pos: QPointF):
        image_pos = self.pixmap_item.mapFromScene(scene_pos)
        x, y = int(image_pos.x()), int(image_pos.y())

        if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
            self.coord_label.setText(f"Coordinates: ({x}, {y})")
        else:
            self.coord_label.setText("Coordinates: Out of bounds")

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
