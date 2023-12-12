import sys
sys.path.append(r'C:\Users\Gianna\Documents\Python Scripts\rsc_ca_plotting')
import os 
import re
import pandas as pd
import numpy as np
import src.plotting.plot_utils as plt_util
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from src.plotting.subplot import Subplot
from src.workutils.PlotEmitterSignals import EmittedPlotSignals
from src.workutils.longitudinal_utils import get_cell_names_from_max, get_day_digit


# class to represent the functions of longitudinal plotting
# day_and_sessions_data is an array that contains all the data needed for plots 
# length of outer list represents number of days -> ex. [day_1, day_2, day_3]
# each item in that list (representing days) is a 2-item array -> 
# ex. [[[dlc1, dlc1], [spike1,spike1]], [[dlc2, dlc2], [spike2, spike2]]] (represents 2 days with 2 sessions each)
# Every 2-item array contains the DLC files for all sessions on the that day as the first element (index 0),
# and the aligned longitudinal spike files for all sessions on that day as the second element (index 1)
class LongitudinalPlot(object):

    def __init__(self, spike_directory, dlc_directory, output_folder_path, framerate, two_dim_arena_coords):
        self.framerate = framerate
        self.spike_dir = spike_directory
        self.dlc_dir = dlc_directory
        self.output_folder_path = output_folder_path
        if not os.path.exists(self.output_folder_path):
            os.mkdir(output_folder_path)
        #self.main_dir = main_dir
        #self.directory = sorted(os.listdir(self.main_dir))
        self.splt = Subplot(self.framerate, two_dim_arena_coords)
        # coordinates provided as 2-dim array
        self.arena_x_length = two_dim_arena_coords[0]
        self.arena_y_length = two_dim_arena_coords[1]
        self.day_and_sessions_data = self.get_files()
        self.cell_names = get_cell_names_from_max(self.day_and_sessions_data)
        # get max amount of row specs needed for plot using day with most sessions 
        self.max_row_num = np.max(self.sessions_in_each_day)
        # get number of cols needed based on number of days
        self.num_days = len(self.sessions_in_each_day)
        self.num_sessions = np.sum(self.sessions_in_each_day)
        self.signals = EmittedPlotSignals()
    
    ## 
    def get_files(self):
        dlc_dict = {}
        spike_dict = {}
        date_regex = re.compile(pattern=r'^[0-9]{8}')
        sessions_data = []
        sessions_in_each_day = []
        self.dlc_files = os.listdir(self.dlc_dir)
        self.spike_files = os.listdir(self.spike_dir)
        if self.dlc_dir != self.spike_dir:
            self.directory = set(self.dlc_files + self.spike_files)
        else:
            self.directory = os.listdir(self.spike_dir)
        # for every file in directory, check if it is a spike file or a DLC file
        # when found -> get the day of recording from file and add it to the 'spike_dict' or 'dlc_dict' dictionary, respectively
        for file in self.directory:
            if (('longitudinal_spikes'.lower() in file.lower()) & ('.csv' in file.lower())):
                day = get_day_digit(file)
                # case if date hasnt bee added to dictionary yet
                if day not in spike_dict:
                    spike_dict[day]= [pd.read_csv(os.path.join(self.spike_dir ,file))]
                else:
                    day_list = spike_dict[day]
                    spike_dict[day]= day_list + [pd.read_csv(os.path.join(self.spike_dir,file))]

            if (bool(date_regex.search(file))):
                m = date_regex.search(file)
                if m:
                    date = m.group()
                    if (('DLC'.lower() in file.lower()) & ('.csv' in file)):
                        if date not in dlc_dict:
                            #create new date and add new dlc csv to date key value
                            dlc_dict[date] = [pd.read_csv(os.path.join(self.dlc_dir,file), header=[1,2])]
                        else:
                            dlc_list = dlc_dict[date]
                            dlc_dict[date] = dlc_list + [pd.read_csv(os.path.join(self.dlc_dir,file), header=[1,2])]
        
        # add a nested list for every day -> end result will be list equal to the length of days, and inner lists contain dlc files as 
        # the first list and spike files as the second list 
        for day in spike_dict.keys():
            day_label = day
            sessions_data.append([[], spike_dict[day_label]])

        # iterate through dlc dictionary to add to sessions data info
        idx = 0
        for day in dlc_dict.keys():
            day_num = day
            sessions_data[idx][0] += dlc_dict[day_num]
            # add num of sessions to list with num sessions for each day
            sessions_in_each_day.append(len(dlc_dict[day_num]))
            idx += 1
        self.sessions_in_each_day = sessions_in_each_day
        return sessions_data
    
    

    def get_timestamps(self, day, session):
        frames = [i for i in range(len(self.day_and_sessions_data[day][0][session]))]
        timestamp_data = [float(frame / self.framerate) for frame in frames]
        #start the session at time 0
        timestamp_data = timestamp_data - np.min(timestamp_data)
        #make an array for easy use
        timestamps = np.array(timestamp_data).flatten()
        return timestamps

    #scale head and angle pixel positions to arena by taking the minimum x and y values and 

    def get_head_and_angles(self, day, session):
        head_x, head_y, angles = plt_util.calc_positions(self.day_and_sessions_data[day][0][session])
        head_x -= np.min(head_x)
        head_x *= (self.arena_x_length/np.max(head_x))
        head_y -= np.min(head_y)
        head_y *= (self.arena_y_length/np.max(head_y))
        return head_x, head_y, angles

    # input the types of subplots to be created as strings on one figure
    # output to desination
    # *args provided should be the name of plots provided, **kwargs should be the arguments to the plots
    # **kwargs will include:
    #                       + for spike plots: {"spike_line_color": #XXXXXX, "line_size": xx, "spike_size": xx}
    #                       + for barrier plots: {"barrier_coord1": [[x1,y1], [x2, y2]], "barrier_coord2": [[x3, y3], [x4, y4], 'barrier_coord3' = [[None, None], [None, None]]]
    #                       + for HD plots: {"hd_line_color": xx}
    def plot_LR_figures(self, output_folder_name, plot_type_arg, **kwargs):
        output_path = os.path.join(self.output_folder_path, output_folder_name)
        num_rows = self.max_row_num
        num_cols = self.num_days
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for cell in self.cell_names:
            print(cell)
            figure = plt.figure()
            plt.rcParams.update({'figure.max_open_warning': 0})
            axes = []
            ax_indices = []
            gs = GridSpec(nrows=num_rows, ncols=num_cols, wspace=0.75, hspace=0.75)
            polar_plots = ['ebc_boundary', 'ebc_barrier', 'ebc_boundary_barrier', 'hd_curve']
            for row_idx in range(num_rows):
                for col_idx in range(num_cols):
                    if plot_type_arg in polar_plots:
                        axes.append(figure.add_subplot(gs[row_idx, col_idx], projection="polar"))
                    else:
                        axes.append(figure.add_subplot(gs[row_idx, col_idx]))
                    ax_indices.append([row_idx, col_idx])
                    
            for day_idx in range(self.num_days):

                num_sessions_for_day = len(self.day_and_sessions_data[day_idx][1])
                if num_sessions_for_day < num_rows:
                    # exclude the indices of axis that will not be plotted for that day 
                    ax_indices_to_turn_off = range(self.max_row_num)[num_sessions_for_day:]
                    for index in ax_indices_to_turn_off:
                        idx_in_axes = next((i for i, sublist in enumerate(ax_indices) if sublist == [index, day_idx]), None)
                        axes[idx_in_axes].axis('off')

                for session_idx in range(num_sessions_for_day):

                    ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session_idx, day_idx]), None)
                    axis_to_plot = axes[ax_to_plot_index]
                    axis_to_plot.axis('off')

                    timestamps = self.get_timestamps(day_idx, session_idx)
                    cell_df = self.day_and_sessions_data[day_idx][1][session_idx]
                    cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
                    spike_train = np.zeros_like(timestamps)

                    if cell_event_timestamps is not None:
                        for event_ts in cell_event_timestamps:
                            abs_diffs= abs(timestamps - event_ts)
                            min_idx = np.argmin(abs_diffs, axis=0)
                            spike_train[min_idx] = 1

                    head_x, head_y, angles = self.get_head_and_angles(day_idx, session_idx)
                    head_x, head_y, angles = head_x[:-1], head_y[:-1], angles[:-1]
                    spike_train = spike_train[:-1]
                    # find index in indices list to find the axis to plot on
                    # ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session_idx, day_idx]), None)
                    # print(ax_to_plot_index)
                    # axis_to_plot = axes[ax_to_plot_index]
                    # axis_to_plot.axis('off')
                    # plot based on provided arg type -> LR plots cant be made with barriers yet
                    if (plot_type_arg == 'spike_plot')  & ('spike_line_color' in kwargs) & ('spike_size' in kwargs) & ('line_size' in kwargs):
                        self.splt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, line_color = kwargs['spike_line_color'],
                        spike_sizes = kwargs['spike_size'], line_size=kwargs['line_size'], axis = axis_to_plot)
                    
                    elif (plot_type_arg == 'hd_curve') & ('hd_line_color' in kwargs):
                        self.splt.hd_curve_subplot(angles, spike_train, line_color= kwargs['hd_line_color'], destination=None, axis=axis_to_plot)
                        
                    elif (plot_type_arg == 'heatmap'):
                        self.splt.heatmap_subplot(head_x, head_y, spike_train, destination=None, axis= axis_to_plot)
                    
                    elif (plot_type_arg == 'ebc_boundary'):
                        boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                        boundary_bearings, boundary_distances = boundary_bearings[:-1], boundary_distances[:-1]
                        self.splt.ebc_subplot(boundary_bearings, boundary_distances, spike_train, destination= None, axis= axis_to_plot)
                

                
                # elif ((plot_type_arg == 'ebc_barrier') & ('barrier_coords' in kwargs)):
                #     if ((kwargs['barrier_coords'][session_idx][0][0] is not None) & (kwargs['barrier_coords'][session_idx][1][0] is not None)):

                #         barrier_start = kwargs['barrier_coords'][session_idx][0]
                #         barrier_end = kwargs['barrier_coords'][session_idx][1]

                #         barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles, barrier_start, barrier_end)
                #         barrier_bearings, barrier_distances = barrier_bearings[:-1], barrier_distances[:-1]
                #         self.splt.ebc_subplot(barrier_bearings, barrier_distances, spike_train, destination=None, axis= axis_to_plot)

                # elif ((plot_type_arg == 'ebc_boundary_barrier')):

                #     if ((kwargs['barrier_coords'][session_idx][0][0] is not None) &
                #             (kwargs['barrier_coords'][session_idx][1][0] is not None)):
                #         barrier_start = kwargs['barrier_coords'][session_idx][0]
                #         barrier_end = kwargs['barrier_coords'][session_idx][1]
                #         boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                #         boundary_bearings, boundary_distances = boundary_bearings[:-1], boundary_distances[:-1]
                #         barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles, barrier_start, barrier_end)
                #         barrier_bearings, barrier_distances = barrier_bearings[:-1], barrier_distances[:-1]
                #         all_bearings = np.concatenate([boundary_bearings, barrier_bearings],axis=1)
                #         all_dists = np.concatenate([boundary_distances, barrier_distances],axis=1)
                #         all_bearings, all_dists = all_bearings[:-1], all_dists[:-1]
                #         self.splt.ebc_subplot(all_bearings, all_dists,
                #                                 spike_train, destination=None, axis=axis_to_plot)    
            destination = os.path.join(output_path, f'{cell}')
            self.signals.figure_closed.emit()
            self.signals.figure_plotted.emit(figure)
            self.signals.cell_plotted.emit(cell)
            figure.tight_layout(pad=1)
            figure.savefig(destination,dpi=300)
            plt.close()


    def get_LR_plots_all_days_have_cell(self, output_folder_name, plot_type_arg, **kwargs):
        output_path = os.path.join(self.main_dir, output_folder_name)
        num_rows = self.max_row_num
        num_cols = self.num_days
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for cell in self.cell_names:
            print(cell)
            figure = plt.figure(figsize=(5,5))
            plt.rcParams.update({'figure.max_open_warning': 0})
            axes = []
            ax_indices = []
            gs = GridSpec(nrows=num_rows, ncols=num_cols, wspace=0.75, hspace=0.75)
            polar_plots = ['ebc_boundary', 'ebc_barrier', 'ebc_boundary_barrier', 'hd_curve']
            for row_idx in range(num_rows):
                for col_idx in range(num_cols):
                    if plot_type_arg in polar_plots:
                        axes.append(figure.add_subplot(gs[row_idx, col_idx], projection="polar"))
                    else:
                        axes.append(figure.add_subplot(gs[row_idx, col_idx]))
                    ax_indices.append([row_idx, col_idx])
            day_has_cell = True

            for day_idx in range(0, len(self.day_and_sessions_data)): 
                for session in range(0, len(self.day_and_sessions_data[day_idx][1])):

                    timestamps = self.get_timestamps(day_idx, session)
                    cell_df = self.day_and_sessions_data[day_idx][1][session]
                    cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
                    spike_train = np.zeros_like(timestamps)

                    #exclude cell from being plotted if not all days contain a spike
                    if len(cell_event_timestamps) == 0:
                        day_has_cell = False
                        break

                    if cell_event_timestamps is not None:
                        for event_ts in cell_event_timestamps:
                            abs_diffs= abs(timestamps - event_ts)
                            min_idx = np.argmin(abs_diffs, axis=0)
                            spike_train[min_idx] = 1

                    head_x, head_y, angles = self.get_head_and_angles(day_idx, session)
                    head_x, head_y, angles = head_x[:-1], head_y[:-1], angles[:-1]
                    # find index in indices list to find the axis to plot on
                    ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session, day_idx]), None)
                    axis_to_plot = axes[ax_to_plot_index]
                    axis_to_plot.axis('off')
                    # plot based on provided arg type -> LR plots cant be made with barriers yet
                    if (plot_type_arg == 'spike_plot')  & ('spike_line_color' in kwargs) & ('spike_size' in kwargs) & ('line_size' in kwargs):
                        self.splt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, line_color = kwargs['spike_line_color'],
                        spike_sizes = kwargs['spike_size'], line_size=kwargs['line_size'], axis = axis_to_plot)
                    
                    elif (plot_type_arg == 'hd_curve') & ('hd_line_color' in kwargs):
                        axis_to_plot.axis('on')
                        self.splt.hd_curve_subplot(angles, spike_train, line_color= kwargs['hd_line_color'], destination=None, axis=axis_to_plot)

                    elif (plot_type_arg == 'heatmap'):
                        self.splt.heatmap_subplot(head_x, head_y, spike_train, destination=None, axis= axis_to_plot)
                    
                    elif (plot_type_arg == 'ebc_boundary'):
                        boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                        boundary_bearings, boundary_distances = boundary_bearings[:-1], boundary_distances[:-1]
                        self.splt.ebc_subplot(boundary_bearings, boundary_distances, spike_train, destination= None, axis= axis_to_plot)
            if day_has_cell:
                destination = os.path.join(output_path, f'{cell}')
                figure.tight_layout(pad=1)
                figure.savefig(destination,dpi=300)
                self.signals.figure_closed.emit()
                self.signals.figure_plotted.emit(figure)
                self.signals.cell_plotted.emit(cell)
                plt.close()



    # # use calculations from plt utils and subplot class to make trajectory/spike plots
    # def get_lr_spike_plots(self, spike_sizes, line_sizes):
    #     output_path = os.path.join(self.main_dir, 'Longitudinal Spike Plots - all days')

    #     if not os.path.exists(output_path):
    #         os.mkdir(output_path)
    #     for cell in self.cell_names:
    #         print(cell)
    #         figure= plt.figure(figsize=(5,5))
    #         plt.rcParams.update({'figure.max_open_warning': 0})
    #         axes = [figure.add_subplot(self.gs[i, j]) for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
    #         ax_indices = [[i, j] for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
    #         axes = [ax.axis('off') for ax in axes]

    #         for day_idx in range(0, len(self.day_and_sessions_data)): 
    #             for session in range(0, len(self.day_and_sessions_data[day_idx][1])):

    #                 timestamps = self.get_timestamps(day_idx, session)
    #                 cell_df = self.day_and_sessions_data[day_idx][1][session]
    #                 cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
    #                 spike_train = np.zeros_like(timestamps)

    #             if cell_event_timestamps is not None:
    #                 for event_ts in cell_event_timestamps:
    #                     abs_diffs= abs(timestamps - event_ts)
    #                     min_idx = np.argmin(abs_diffs, axis=0)
    #                     spike_train[min_idx] = 1

    #             head_x, head_y, angles = self.get_head_and_angles(day_idx, session)
    #             ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session, day_idx]), None)
    #             ax_to_plot_spike = axes[ax_to_plot_index]
    #             self.subplt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, spike_sizes = spike_sizes, line_size= line_sizes, axis = ax_to_plot_spike)
    #         destination = os.path.join(output_path, f'{cell}')
    #         figure.tight_layout(pad=1)
    #         figure.savefig(destination,dpi=300)
    #         plt.close()
            


    # # get spike plots but only for cells that have spiking on every day 
    # def get_spike_plots_all_cells_only(self, spike_sizes, line_sizes):
    #     output_path = os.path.join(self.main_dir, 'Longitudinal Spike Plots - all days have cell')
    #     if not os.path.exists(output_path):
    #         os.mkdir(output_path)
    #     for cell in self.cell_names:
    #         print(cell)
    #         figure= plt.figure(figsize=(5,5))
    #         plt.rcParams.update({'figure.max_open_warning': 0})

    #         axes = [figure.add_subplot(self.gs[i, j]) for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
    #         ax_indices = [[i, j] for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
    #         #axes = [ax.axis('off') for ax in axes]
    #         day_has_cell = True

    #         for day_idx in range(0, len(self.day_and_sessions_data)): 
    #             for session in range(0, len(self.day_and_sessions_data[day_idx][1])):

    #                 timestamps = plt_util.get_timestamps(day_idx, session)
    #                 cell_df = self.day_and_sessions_data[day_idx][1][session]
    #                 cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
    #                 #exclude cell from being plotted if not all days contain a spike
    #                 if len(cell_event_timestamps) == 0:
    #                     day_has_cell = False
    #                     break
    #                 spike_train = np.zeros_like(timestamps)

    #                 if cell_event_timestamps is not None:

    #                     for event_ts in cell_event_timestamps:
    #                         abs_diffs= abs(timestamps - event_ts)
    #                         spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
    #                 head_x, head_y, angles = self.get_head_and_angles(day_idx, session)
    #                 ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session, day_idx]), None)
    #                 ax_to_plot_spike = axes[ax_to_plot_index].axis('off')
    #                 self.subplt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, spike_sizes = spike_sizes, line_size=line_sizes, axis = ax_to_plot_spike)

    #         if day_has_cell:
    #             destination = os.path.join(output_path, f'{cell}')
    #             figure.tight_layout(pad=1)
    #             figure.savefig(destination,dpi=300)
    #             plt.close()
