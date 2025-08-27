from PySide6.QtCore import QObject, QEvent, Qt


class ResizeFilter(QObject):
    def __init__(self, pixmap_item, parent=None):
        super().__init__(parent)
        self.pixmap_item = pixmap_item

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize and self.pixmap_item is not None:
            obj.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        return False
