from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox
from PyQt5.QtCore import QObject, pyqtSignal as Signal


class BarrierDialog(QDialog):
    barrier_coords_selected = Signal()

    def __init__(self, plotting_obj):
        super().__init__()
        self.row_counter = 0
        self.setWindowTitle('Barrier Coordinates Select')
        self.line_edits = []
        self.num_sessions = plotting_obj.num_sessions
        self.barrier_coords = [[[None, None], [None, None]] for _ in range(self.num_sessions)]

        self.main_layout = QVBoxLayout()
        self.label_layout = QHBoxLayout()
        self.first_row_layout = QHBoxLayout()
        select_insert_layout = QHBoxLayout()

        # setup select and insert buttons  -> TO DO : delete row button
        self.insert_button = QPushButton("Insert Row", self)
        self.insert_button.setStyleSheet("background-color: 'light blue'")
        self.insert_button.clicked.connect(self.insert_row)
        select_insert_layout.addWidget(self.insert_button)
        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.save_coords)
        self.select_button.setStyleSheet("background-color: 'light blue'")
        select_insert_layout.addWidget(self.select_button)
        self.main_layout.addLayout(select_insert_layout)


        labels = ['Session with Barrier', 'Barrier start- x coord', 'Barrier start- y coord',
                   'Barrier end- x coord', 'Barrier end- y coord']   
        self.inserted_layouts = []
        for label_idx, label_text in enumerate(labels):
            label = QLabel(label_text)    
            line_edit = QLineEdit()
            self.label_layout.addWidget(label)
            self.first_row_layout.addWidget(line_edit)
        self.inserted_layouts.append(self.first_row_layout)
        self.main_layout.addLayout(self.label_layout)
        self.main_layout.addLayout(self.first_row_layout)
        self.setLayout(self.main_layout)
        self.show()

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

                    self.barrier_coords[barrier_session_idx] = ([[barrier_x_start, barrier_y_start],
                                                                       [barrier_x_end, barrier_y_end]])    
                elif not all(all_lines_in_row):
                    raise ValueError('Barrier Coordinates in a row have been left blank.')
            except:
                raise ValueError('Session num provided is not an integer')
        self.barrier_coords_selected.emit()
        print(f'barrier_coords:{self.barrier_coords}')
    
    def get_coords(self):
        return self.barrier_coords