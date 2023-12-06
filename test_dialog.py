from PyQt5.QtWidgets import QLineEdit, QPushButton, QWidget, QHBoxLayout, QMainWindow, QDialog, QTableWidget, QApplication
from PyQt5.QtCore import pyqtSlot as Slot
import sys

class Dialog(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout()
        self.layouts_list = []
        self.button = QPushButton("Add layout")
        self.print_button = QPushButton('Set')
        self.main_layout.addWidget(self.button)
        self.main_layout.addWidget(self.print_button)
        self.button.clicked.connect(self.add_layout)
        self.print_button.clicked.connect(self.get_item)
        self.setLayout(self.main_layout)

    def add_layout(self):
        new_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.line_edit_2 = QLineEdit()
        new_layout.addWidget(self.line_edit)
        new_layout.addWidget(self.line_edit_2)
        self.layouts_list.append(new_layout)
        self.main_layout.addLayout(new_layout)

    def get_item(self):
        print([self.layouts_list[0].itemAt(0).widget().text(), self.layouts_list[0].itemAt(1).widget().text()])
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = Dialog()
    mainWindow.show()
    #mainWindow.get_item()
    sys.exit(app.exec_())


    
    
    # def insert_row(self):
    #     new_dict = {}
    #     new_layout = QHBoxLayout()
    #     self.button_layout.addLayout(new_layout)
    #     for i in range(5):
    #         line_edit = QLineEdit()
    #         new_layout.addWidget(line_edit)
    #         if i == 0:
    #             new_dict['session_num'] = line_edit
    #         elif i == 1:
    #             new_dict['barrier_x_start'] = line_edit
    #         elif i == 2:
    #             new_dict['barrier_y_start'] = line_edit
    #         elif i == 3:
    #             new_dict['barrier_x_end'] = line_edit
    #         elif i == 4:
    #             new_dict['barrier_y_end'] = line_edit
    #     self.line_edit_rows.append(new_dict)
    #     self.main_layout.addLayout(new_layout)


        

    # def insert_row(self):
    #     new_row = []
    #     new_layout = QHBoxLayout()
    #     for _ in range(5):
    #         new_button_group = QGroupBox()
    #         new_layout.addWidget(new_button_group)
    #         line_edit = QLineEdit()
    #         new_button_group.addWidget(line_edit)
    #         new_row.append(new_button_group)
    #         new_layout.addWidget(line_edit)
    #     self.group_boxes.append(new_row)
    #         #new_row.append(line_edit.text())
    #         #new_layout.addWidget(line_edit)

    #     self.main_layout.addLayout(new_layout)
    #     #self.line_edits.append(new_row)