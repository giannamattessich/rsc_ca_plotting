from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal as Signal


class BarrierDialog(QDialog):
    barrier_coords_selected = Signal(list)
    dialog_closed = Signal()

    def __init__(self, plotting_obj):
        super().__init__()
        self.row_counter = 0
        self.setWindowTitle('Barrier Coordinates Select')
        self.line_edits = []
        self.num_sessions = plotting_obj.num_sessions
        self.arena_x_len = plotting_obj.arena_x_length
        self.arena_y_len = plotting_obj.arena_y_length
        self.barrier_coords = [[[None, None], [None, None]] for _ in range(self.num_sessions)]

        self.main_layout = QVBoxLayout()
        self.label_layout = QHBoxLayout()
        self.first_row_layout = QHBoxLayout()
        self.select_insert_layout = QHBoxLayout()

        # setup select and insert buttons  -> TO DO : delete row button
        self.insert_button = QPushButton("Insert Row", self)
        self.insert_button.setStyleSheet("background-color: 'light blue'")
        self.insert_button.clicked.connect(self.insert_row)
        self.select_insert_layout.addWidget(self.insert_button)
        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.save_coords)
        self.select_button.setStyleSheet("background-color: 'light blue'")
        self.select_insert_layout.addWidget(self.select_button)
        self.main_layout.addLayout(self.select_insert_layout)


        labels = ['Session with Barrier', 'Barrier start- x coord', 'Barrier start- y coord',
                   'Barrier end- x coord', 'Barrier end- y coord']   
        # store parent layouts for each row of line edits 
        self.inserted_layouts = []
        # add labels and first row of line edits
        for label_text in labels:
            label = QLabel(label_text)    
            line_edit = QLineEdit()
            self.label_layout.addWidget(label)
            self.first_row_layout.addWidget(line_edit)
        self.inserted_layouts.append(self.first_row_layout)
        self.main_layout.addLayout(self.label_layout)
        self.main_layout.addLayout(self.first_row_layout)
        self.setLayout(self.main_layout)
        self.show()

    # get idx of layout and idx of line edit on layout to find entered positions
    def get_line_edit_at_pos(self, layout_num, line_edit_idx):
        line_edit_text = self.inserted_layouts[layout_num].itemAt(line_edit_idx).widget().text()
        if line_edit_text.isdigit():
            return int(line_edit_text)
        else:
            return ''
    
    def insert_row(self):
        new_layout = QHBoxLayout()
        for i in range(5):
            line_edit = QLineEdit()
            new_layout.insertWidget(i, line_edit)
        self.inserted_layouts.append(new_layout)
        self.main_layout.addLayout(new_layout)

    # check whether selected coordinates and session num is valid
    def check_valid_coords(self, barrier_x_start, barrier_y_start, barrier_x_end, barrier_y_end):
        if (barrier_x_start > self.arena_x_len) or (barrier_x_start < 0):
            raise ValueError('Barrier- x start is greater than the arena length or less than 0. Try again with a different value.')
        if (barrier_y_start > self.arena_y_len) or (barrier_y_start < 0):
            raise ValueError('Barrier- y start is greater than the arena length or less than 0. Try again with a different value.')
        if (barrier_x_end > self.arena_x_len) or (barrier_x_end < 0):
            raise ValueError('Barrier- x end is greater than the arena length or less than 0. Try again with a different value.')
        if (barrier_y_end > self.arena_y_len) or (barrier_y_end < 0):
            raise ValueError('Barrier- y end is greater than the arena length or less than 0. Try again with a different value.')



    def save_coords(self):
        for layout_idx in range(len(self.inserted_layouts)):
            try:
                session_num = self.get_line_edit_at_pos(layout_idx, 0)
                print(session_num)
                barrier_session_idx = session_num - 1
                barrier_x_start = self.get_line_edit_at_pos(layout_idx, 1)
                barrier_y_start = self.get_line_edit_at_pos(layout_idx, 2)
                barrier_x_end = self.get_line_edit_at_pos(layout_idx, 3)
                barrier_y_end = self.get_line_edit_at_pos(layout_idx, 4)
                coords = [barrier_x_start, barrier_y_start, barrier_x_end, barrier_y_end]
                all_lines_in_row = [True if (point != '') else False for point in coords]

                if all(all_lines_in_row) & (self.num_sessions > barrier_session_idx):
                    self.check_valid_coords(barrier_x_start, barrier_y_start, barrier_x_end, barrier_y_end)
                    self.barrier_coords[barrier_session_idx] = ([[barrier_x_start, barrier_y_start],
                                                                    [barrier_x_end, barrier_y_end]])  
                    self.barrier_coords_selected.emit(self.barrier_coords)
                elif not all(all_lines_in_row):
                    raise ValueError('Barrier Coordinates in a row have been left blank.')
                elif (barrier_session_idx > self.num_sessions):
                    raise ValueError('Barrier session provided is greater than the number of sessions')
            except:
                raise ValueError('Session num provided is not an integer')
        
        print(f'barrier_coords:{self.barrier_coords}')
    
    #def get_coords(self):
    #    return self.barrier_coords

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            "Do you want to continue selecting coordinates?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.No:
            event.accept()
           # self.barrier_coords = [[[None, None], [None, None]] for _ in range(self.num_sessions)]
            self.dialog_closed.emit()
        else:
            event.ignore()

            