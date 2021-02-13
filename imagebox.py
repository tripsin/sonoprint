from PySide2.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit, QListView, QListWidget

class ImageList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)




class ImageBox(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setChecked(True)
        self.setTitle('empty')
        self.layout = QVBoxLayout(self)

        self.img = QLabel()
        self.img.setScaledContents(True)
        self.layout.addWidget(self.img)

        self.txt = QLineEdit(self)
        self.layout.addWidget(self.txt)

        self.setLayout(self.layout)
        self.setFixedWidth(320)
        self.setFixedHeight(240)

    def enable(self):
        self.setChecked(True)

    def disable(self):
        self.setChecked(False)

    def set_title(self, name):
        self.setTitle(name)

    def set_image(self, pixmap):
        self.img.setPixmap(pixmap)
