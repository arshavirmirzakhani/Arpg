from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from editorwidget import EditorWidget
import shutil


class ImageViewer(QWidget, EditorWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.modified = False

        self._zoom = 1.0
        self._dragging = False
        self._drag_start_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)


        self.view = QGraphicsView()
        self.view.setRenderHint(self.view.renderHints() & ~self.view.renderHints().SmoothPixmapTransform)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.pixmap = QPixmap(self.image_path)
        if self.pixmap.isNull():
            QMessageBox.critical(self, "Error", "Failed to load image.")
            return

        # Create checkerboard background item
        self.checker_item = QGraphicsPixmapItem(self.generate_checkerboard_pixmap(self.pixmap.width(), self.pixmap.height()))
        self.checker_item.setZValue(-1)  # Ensure it's behind the image
        self.scene.addItem(self.checker_item)

        # Add image on top
        self.pixmap_item = QGraphicsPixmapItem(self.pixmap)
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.FastTransformation)
        self.scene.addItem(self.pixmap_item)

        layout.addWidget(self.view)
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

    def is_modified(self) -> bool:
        return self.modified

    def save(self):
        try:
            shutil.copy(self.image_path, self.image_path)
            self.modified = False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}")

    def wheelEvent(self, event: QWheelEvent):
        # Zoom in/out with mouse wheel
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