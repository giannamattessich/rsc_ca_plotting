import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QLabel
from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
from PyQt5.QtCore import Qt

class CircularImageCheckBox(QCheckBox):
    def __init__(self, text, image_path, parent=None):
        super().__init__(parent)
        self.text_label = QLabel(text)
        self.image_path = image_path
        self.checked = False
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QCheckBox { padding: 0; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a circular image
        image = self.createCircularImage()

        # Set the circular image as the background
        self.setStyleSheet(f"QCheckBox:checked {{ background-image: url({image}); }}")
        self.setStyleSheet("QCheckBox { border: 2px solid gray; border-radius: 10px; }")

        layout.addWidget(self.text_label)
        layout.setContentsMargins(5, 5, 5, 5)

    def createCircularImage(self):
        size = 20  # Size of the circular image
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a circular shape
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)

        # Load and draw the image
        icon = QPixmap(self.image_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, size, size, icon)

        painter.end()

        # Save the circular image to a temporary file and return its path
        temp_image_path = "temp_circular_image.png"
        image.save(temp_image_path)

        return temp_image_path

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QWidget()
    window.setGeometry(100, 100, 300, 150)
    window.setWindowTitle('Circular Image CheckBox')

    checkbox = CircularImageCheckBox('Toggle Image', r'src\frontend\GUI Images\pokeball_red.png')
    checkbox.stateChanged.connect(lambda state: checkbox.setCheckState(Qt.Checked) if state == Qt.Unchecked else checkbox.setCheckState(Qt.Unchecked))

    layout = QVBoxLayout(window)
    layout.addWidget(checkbox)
    
    window.show()

    sys.exit(app.exec_())
