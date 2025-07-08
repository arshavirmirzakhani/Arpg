from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

class EditorWidget:
    def is_modified(self) -> bool:
        return False

    def save(self):
        pass
    
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