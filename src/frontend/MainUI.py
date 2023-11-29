from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QColorDialog
from PyQt5.QtGui import QFont
from src.handle_dirs import can_create_directory
from src.plotting.timeseries_plot import TimeSeriesPlots
from src.frontend.BarrierDialog import BarrierDialog
from colour import Color


class MainUI(QMainWindow):

    def __init__(self):
        super(MainUI, self).__init__()
        loadUi(r"src\frontend\plotting_gui.ui", self)
        # set up buttons to open file explorer and selector
        self.calcium_spike_input_button.clicked.connect(self.open_calcium_dir_dialog)
        self.dlc_files_input_button.clicked.connect(self.open_dlc_dir_dialog)
        # set directories when line edit text is changed 
        self.calcium_spike_input_line_edit.textChanged.connect(self.set_calcium_dir)
        self.dlc_input_line_edit.textChanged.connect(self.set_dlc_dir)
        self.output_path_line_edit.textChanged.connect(self.set_output_path)
        # disable line edit from being written to unless button is clicked
        self.calcium_spike_input_line_edit.setReadOnly(True)
        self.dlc_input_line_edit.setReadOnly(True)
        #self.ebc_barrier_checkbox.setReadOnly(True)
        #self.ebc_boundary_barrier_checkbox.setReadOnly(True)

        self.same_folder_dlc_checkbox.stateChanged.connect(self.on_same_dir_check)
        self.single_day_rec_radio.toggled.connect(self.on_single_rec_click)
        self.multi_day_rec_radio.toggled.connect(self.on_multi_day_click)
        self.framerate_line_edit.textChanged.connect(self.set_framerate)
        self.arena_x_line_edit.textChanged.connect(self.set_arena_x)
        self.arena_y_line_edit.textChanged.connect(self.set_arena_y)
        self.spike_plot_checkbox.stateChanged.connect(self.set_spike_plot)
        self.ebc_boundary_checkbox.stateChanged.connect(self.set_ebc_boundary_plot)
        self.ebc_barrier_checkbox.stateChanged.connect(self.set_ebc_barrier_plot)
        self.ebc_boundary_barrier_checkbox.stateChanged.connect(self.set_ebc_boundary_barrier_plot)
        self.heatmap_checkbox.stateChanged.connect(self.set_heatmap_plot)
        self.hd_curve_checkbox.stateChanged.connect(self.set_hd_curve_plot)
        self.plot_it_button.clicked.connect(self.on_plot_click)
        self.trajectory_color_select_button.clicked.connect(self.show_color_dialog_trajectory)
        self.hd_color_select_button.clicked.connect(self.show_color_dialog_hd_color)
        # state of input data
        self.files_set = False
        self.calcium_dir_selected = False
        self.dlc_dir_selected = False
        self.output_path_selected = False
        self.calcium_dlc_same_dir = False
        self.output_folder_named = False
        self.single_day_selected = False
        self.multi_day_selected = False
        self.spike_plot_selected = False
        self.ebc_boundary_selected = False
        self.ebc_barrier_selected = False
        self.ebc_boundary_barrier_selected = False
        self.heatmap_selected = False
        self.hd_curve_selected = False

        self.plot_dict = {'spike_plot': False, 'ebc_boundary': False,
                           'ebc_barrier': False, 'ebc_boundary_barrier': False, 'heatmap': False, 'hd_curve': False}

        self.plot_attributes = {}
        self.spike_line_color = self.trajectory_color_line_edit.text()
        self.line_size = self.trajectory_width_spinbox.value()
        self.trajectory_width_spinbox.setValue(1.25)
        self.spike_size = self.spike_sizes_spinbox.value()
        self.spike_sizes_spinbox.setValue(6)
        self.hd_line_color = self.hd_color_line_edit.text()
        self.output_folder_name = self.output_folder_name_line_edit.text()


    def check_color(self, color):
        try:
            #remove spaces
            color = color.replace(" ", "")
            Color(color)
            return True
        except Exception: 
            return False

#create tuple of arguments to be provided to plotting function based on what checkboxes 
# are clicked at the time of clicking plot button
    def get_plot_args(self):
        plot_list = []
        for key, value in self.plot_dict.items():
            if value:
                plot_list.append(key)
        return (tuple(plot_list))
    
    # get attributes needed for making plots
    def get_plot_kwargs(self, *args):
        if 'spike_plot' in args:
            if (len(self.trajectory_color_line_edit.text())) > 0 & (self.check_color(self.trajectory_color_line_edit.text())):
                self.plot_attributes['spike_line_color'] = self.trajectory_color_line_edit.text()
            else:
                self.show_error_message('Trajectory line color has not been selected.')
                return
            if self.trajectory_width_spinbox.value() > 0:
                self.plot_attributes['line_size'] = self.trajectory_width_spinbox.value()
            else:
                self.show_error_message('Trajectory width cannot be 0.')
            if self.spike_sizes_spinbox.value() > 0:
                self.plot_attributes['spike_size'] = self.spike_sizes_spinbox.value()
            else:
                self.show_error_message('Spike sizes cannot be 0.')
        if 'hd_curve' in args:
            if (len(self.hd_color_line_edit.text()) > 0) & (self.check_color(self.hd_color_line_edit.text())):
                self.plot_attributes['hd_line_color'] = self.hd_color_line_edit.text()
        return self.plot_attributes

    
    def on_plot_click(self):
        if ((self.calcium_dir_selected )& (self.dlc_dir_selected) & (self.output_path_selected) &
             (len(self.output_folder_name_line_edit.text()) > 0) & (self.single_day_rec_radio.isChecked())):
            # get args for plotting function-> plot type
            plots_to_make = self.get_plot_args()
            plot_attributes = self.get_plot_kwargs(*plots_to_make)
            
            if len(plots_to_make) > 0:
                self.timeseries_plots = TimeSeriesPlots(self.calcium_input_dir, 
                                                        self.dlc_input_dir,
                                                         self.output_path_line_edit.text(),
                                                           framerate= int(self.framerate_line_edit.text()),
                                                             two_dim_arena_coords= [int(self.arena_x_line_edit.text()),
                                                                                     int(self.arena_y_line_edit.text())])
                
                if (('ebc_barrier' in plots_to_make) or ('ebc_boundary_barrier' in plots_to_make)):
                    self.show_barrier_dialog(self.timeseries_plots)
                else:
                    self.show_complete_dialog('Plotting begun!')

                self.timeseries_plots.plot_figures(self.output_folder_name_line_edit.text(), *plots_to_make, **plot_attributes)
                return
        elif (not self.calcium_dir_selected):
              self.show_error_message('Calcium directory has not been selected')
              return
        elif (not self.dlc_dir_selected):
            self.show_error_message('DLC directory has not been selected ')
            return 
        elif (not self.output_path_selected):
            self.show_error_message('Output path has not been selected')
        else:
            self.show_error_message('No plot type has been selected. Please try checking one of the boxes to make plots.')


# check if the plotting can start based on whether dirs are selected and output folder specified 


    def on_same_dir_check(self, state):
        # check if checkbox is clicked 
        if (state==2):
            self.calcium_dlc_same_dir = True
            if (self.calcium_dir_selected) & (not self.dlc_dir_selected):
                self.dlc_input_line_edit.setText(self.calcium_input_dir)
                self.output_path_line_edit.setText(self.calcium_input_dir)
                self.dlc_dir_selected = True
                self.output_path_selected = True
            elif (not self.calcium_dir_selected) & (self.dlc_dir_selected):
                self.calcium_spike_input_line_edit.setText(self.dlc_input_dir)
                self.output_path_line_edit.setText(self.dlc_input_dir)
                self.calcium_dir_selected = True
                self.output_path_selected = True
            elif (not self.calcium_dir_selected) & (not self.dlc_dir_selected):
                self.show_error_message('No directories have been selected for calcium files or DLC files. Please provide an input folder first.')
                self.calcium_dlc_same_dir = False
                self.same_folder_dlc_checkbox.setCheckState(0)
                #self.same_folder_dlc_checkbox.setChecked(False)
            elif (self.dlc_dir_selected & self.calcium_dir_selected):
                if (self.dlc_input_dir != self.calcium_input_dir):
                    self.show_error_message('Selected directories for DLC files and calcium spike files are not the same. Please try reselecting the directory with both files.')
                    self.calcium_dlc_same_dir = False
                    self.calcium_spike_input_line_edit.setText('')
                    self.dlc_input_line_edit.setText('')
                    self.output_path_line_edit.setText('')
        else:
            self.calcium_dlc_same_dir = False
            if ((self.dlc_dir_selected) | (self.calcium_dir_selected)):
                self.show_complete_dialog('Calcium and DLC files will not be set to the same input folder.')
                self.calcium_spike_input_line_edit.setText('')
                self.dlc_input_line_edit.setText('')
                self.output_path_line_edit.setText('')

    #get the name of plots and return a tuple of args to provide to the plotting function 

    
    
    @Slot()
    def set_output_path(self):
        if (len(self.output_path_line_edit.text()) > 0 & can_create_directory(self.output_path_line_edit.text())):
            self.output_path_selected = True
            self.output_path = self.output_path_line_edit.text()
        else:
            self.output_path_selected = False

            
    @Slot()
    def set_calcium_dir(self):
        if len(self.calcium_spike_input_line_edit.text()) > 0:
            self.calcium_dir_selected = True
            self.calcium_input_dir = self.calcium_spike_input_line_edit.text()
        else:
            self.calcium_dir_selected = False

    @Slot()
    def set_dlc_dir(self):
        if len(self.dlc_input_line_edit.text()) > 0:
            self.dlc_dir_selected = True
            self.dlc_input_dir = self.dlc_input_line_edit.text()
        else:
            self.dlc_dir_selected = False      
    
    def on_single_rec_click(self, checked):
        if checked:
            self.single_day_selected = True
        else:
            self.single_day_selected = False
    
    def on_multi_day_click(self, checked):
        if checked:
            self.multi_day_selected = True

        else:
            self.multi_day_selected = False  
    @Slot()
    def set_framerate(self):
        if (len(self.framerate_line_edit.text()) > 0):
            try:
                fps = int(self.framerate_line_edit.text())
                self.framerate = fps
            except ValueError:
                self.show_error_message('Input framerate is not a valid float value.')
                self.framerate_line_edit.setText('')
                return
    
    @Slot()
    def set_arena_x(self):
        if (len(self.arena_x_line_edit.text()) > 0):
            try: 
                arena_x = float(self.arena_x_line_edit.text())
                self.arena_x_len = arena_x
            except ValueError:
                self.show_error_message('Arena x coordinate is not a valid value.')
                self.arena_x_line_edit.setText('')

    @Slot()
    def set_arena_y(self):
        if (len(self.arena_y_line_edit.text()) > 0):
            try:
                arena_y = float(self.arena_y_line_edit.text())
                self.arena_y_len = arena_y
            except ValueError:
                self.show_error_message('Arena y coordinate is not a valid value.')
                self.arena_y_line_edit.setText('')
    
    def set_spike_plot(self, state):
        if (state == 2):
            self.spike_plot_selected = True
            self.plot_dict['spike_plot'] = True
        else:
            self.spike_plot_selected = False
            self.plot_dict['spike_plot'] = False

    def set_ebc_boundary_plot(self, state):
        if (state == 2):
            self.ebc_boundary_selected = True
            self.plot_dict['ebc_boundary'] = True
        else:
            self.ebc_boundary_selected = False
            self.plot_dict['ebc_boundary'] = False

    def set_ebc_barrier_plot(self, state):
        if (state == 2):
            self.ebc_barrier_selected = True
            self.plot_dict['ebc_barrier'] = True
        else:
            self.ebc_barrier_selected = False
            self.plot_dict['ebc_barrier'] = False

    def set_ebc_boundary_barrier_plot(self, state):
        if (state == 2):
            self.ebc_boundary_barrier_selected = True
            self.plot_dict['ebc_boundary_barrier'] = True
        else:
            self.ebc_boundary_barrier_selected = False
            self.plot_dict['ebc_boundary_barrier'] = False

    def set_heatmap_plot(self, state):
        if (state == 2):
            self.heatmap_selected = True
            self.plot_dict['heatmap'] = True
        else:
            self.heatmap_selected = False
            self.plot_dict['heatmap'] = False

    def set_hd_curve_plot(self, state):
        if (state == 2):
            self.hd_curve_selected = True
            self.plot_dict['hd_curve'] = True
        else:
            self.hd_curve_selected = False
            self.plot_dict['hd_curve'] = False



    #use to open file explorer to select input dir file
    def open_calcium_dir_dialog(self):
        options = QFileDialog.Options() 
        options |= QFileDialog.ReadOnly
        #set F drive as default, this 3rd argument can be changed to open the default directory
        calcium_dir_path= QFileDialog.getExistingDirectory(self, "Open Dictionary", r"C:\Users\Gianna\Desktop\Analysis - Plots", options=options)
        if calcium_dir_path:
            if not self.calcium_dlc_same_dir:
                self.calcium_spike_input_line_edit.setText(calcium_dir_path)
                self.calcium_input_dir = self.calcium_spike_input_line_edit.text()
                self.calcium_dir_selected = True
            # else:
            #     self.show_error_message('Cannot select input folder because the DLC file input directory has been set to be the same input as the calcium spike files. Please uncheck the checkbox to continue with a different directory.')
            #     return 


        #use to open file explorer to select input dir file
    def open_dlc_dir_dialog(self):
        options = QFileDialog.Options() 
        options |= QFileDialog.ReadOnly
        #set F drive as default, this 3rd argument can be changed to open the default directory
        dlc_dir_path= QFileDialog.getExistingDirectory(self, "Open Dictionary", r"C:\Users\Gianna\Desktop\Analysis - Plots", options=options)
        if dlc_dir_path:
            if not self.calcium_dlc_same_dir:
                self.dlc_input_line_edit.setText(dlc_dir_path)
                self.dlc_input_dir = self.dlc_input_line_edit.text()
                self.dlc_dir_selected = True

            # elif self.calcium_dir_selected:
            #     self.show_error_message('Cannot select input folder because the DLC file input directory has been set to be the same input as the calcium spike files. Please uncheck the checkbox to continue with a different directory.')
            #     return 

    
        #display error
    def show_error_message(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle('Error')
        error_dialog.setText(message)
        font = QFont("Dubai", 12)
        error_dialog.setFont(font)
        error_dialog.setStyleSheet('background-color: #7d1010')
        error_dialog.exec_()

    #show pop-up dialog boxes
    def show_complete_dialog(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('Message')
        msg_box.setText(message)
        msg_box.setStyleSheet('background-color: #666161')
        font = QFont("Dubai", 12)
        msg_box.setFont(font)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.exec_()


    def show_barrier_dialog(self, process_obj):
        self.barrier_dialog = BarrierDialog(process_obj)
        self.barrier_dialog.barrier_coords_selected.connect(self.barrier_selected)
        self.barrier_dialog.exec_()

    @Slot()
    def barrier_selected(self):
        self.plot_attributes['barrier_coords'] = self.barrier_dialog.get_coords()
        self.barrier_dialog.accept()
        self.show_complete_dialog('Plotting begun!')
        self.barrier_dialog.barrier_coords_selected.disconnect(self.barrier_selected)




    def show_color_dialog_trajectory(self):
        color = QColorDialog.getColor()

        if color.isValid():
            # Set the selected color to the line edit
            color_string = color.name()  # Returns color in hexadecimal format
            self.trajectory_color_line_edit.setText(color_string)
            self.trajectory_color_line_edit.setStyleSheet(f'background-color: {color_string};')
    
    def show_color_dialog_hd_color(self):
        color = QColorDialog.getColor()

        if color.isValid():
            # Set the selected color to the line edit
            color_string = color.name()  # Returns color in hexadecimal format
            self.hd_color_line_edit.setText(color_string)
            self.hd_color_line_edit.setStyleSheet(f'background-color: {color_string};')
    

