import sys
sys.path.append(r'C:\Users\Gianna\Documents\Python Scripts\rsc_ca_plotting')
from src.frontend.MainUI import MainUI
from PyQt5.QtWidgets import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainUI()
    mainWindow.show()
    sys.exit(app.exec_())