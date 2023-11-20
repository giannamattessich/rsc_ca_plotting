import os 
import re
import pandas as pd
import numpy as np
import plot_utils as plt_util
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from subplot import Subplot


# class to represent the functions of longitudinal plotting
# day_and_sessions_data is an array that contains all the data needed for plots 
# length of outer list represents number of days -> ex. [day_1, day_2, day_3]
# each item in that list (representing days) is a 2-item array -> 
# ex. [[[dlc1, dlc1], [spike1,spike1]], [[dlc2, dlc2], [spike2, spike2]]] (represents 2 days with 2 sessions each)
# Every 2-item array contains the DLC files for all sessions on the that day as the first element (index 0),
# and the aligned longitudinal spike files for all sessions on that day as the second element (index 1)
class LongitudinalPlot(object):

    def __init__(self, main_dir, two_dim_arena_coords):
        self.framerate = 30
        self.main_dir = main_dir
        self.directory = sorted(os.listdir(self.main_dir))
        self.subplt = Subplot(self.framerate, two_dim_arena_coords)
        # coordinates provided as 2-dim array
        self.arena_x_length = two_dim_arena_coords[0]
        self.arena_y_length = two_dim_arena_coords[1]
        self.day_and_sessions_data = self.get_files()
        self.cell_names = self.get_cell_names_from_max()
        # get max amount of row specs needed for plot using day with most sessions 
        self.max_row_num = np.max(self.sessions_in_each_day)
        # get number of cols needed based on number of days
        self.num_days = len(self.sessions_in_each_day)
        # create grid size
        self.gs = GridSpec(nrows=self.max_row_num, ncols=self.num_days)

    # using file string to get day label 
    def get_day_digit(self, file_string):
        found_digit = False
        result = "day_"
        for char in file_string:
            if char.isdigit():
                found_digit = True
                result += char
            elif found_digit:
                break
        return result
    
    ##** sessions-data => [[dlc_data, dpike_data], [dlc_dict, spike_data...]]
    def get_files(self):
        dlc_dict = {}
        spike_dict = {}
        date_regex = re.compile(pattern=r'^[0-9]{8}')
        sessions_data = []
        sessions_in_each_day = []

        for file in self.directory:
            if (('longitudinal_spikes'.lower() in file.lower()) & ('.csv' in file.lower())):
                day = self.get_day_digit(file)
                if day not in spike_dict:
                    spike_dict[day]= [pd.read_csv(os.path.join(self.main_dir ,file))]
                else:
                    day_list = spike_dict[day]
                    spike_dict[day]= day_list + [pd.read_csv(os.path.join(self.main_dir,file))]

            if (bool(date_regex.search(file))):
                m = date_regex.search(file)
                if m:
                    date = m.group()
                    if (('DLC'.lower() in file.lower()) & ('.csv' in file)):
                        if date not in dlc_dict:
                            #create new date and add new dlc csv to date key value
                            dlc_dict[date] = [pd.read_csv(os.path.join(self.main_dir,file), header=[1,2])]
                        else:
                            dlc_list = dlc_dict[date]
                            dlc_dict[date] = dlc_list + [pd.read_csv(os.path.join(self.main_dir,file), header=[1,2])]
        for day in spike_dict.keys():
            day_label = day
            sessions_data.append([[], spike_dict[day_label]])

        idx = 0
        for day in dlc_dict.keys():
            day_num = day
            sessions_data[idx][0] += dlc_dict[day_num]
            sessions_in_each_day.append(len(dlc_dict[day_num]))
            idx += 1
        self.sessions_in_each_day = sessions_in_each_day
        return sessions_data

    # use regex to find the digits in cell name
    # timeseries automatically outputs cells with a trailing white space and a prefix of ' C'
    def get_cell_num_from_name(self, cell_name):
        match = re.search(r'C(\d+)', cell_name.strip())
        if match:
            cell_num = int(match.group(1))
            return cell_num
        
    # check the spike files for all days to find the max cell value using its number
    def find_max_cell_day(self):
        max = 0
        for day in self.day_and_sessions_data:
            cells = day[1][0][' Cell Name']
            cell_numbers = cells.apply(lambda x: self.get_cell_num_from_name(x))
            day_max = np.max(cell_numbers)
            if day_max > max:
                max = day_max
        return max
    
    # find the number of digits in the maximum cell value and name all cells according to the number of digits in max 
    def get_cell_names_from_max(self):
        max_cell = self.find_max_cell_day()
        num_digits = len(str(self.get_cell_num_from_name(' C' + str(max_cell))))
        # use z fill to rename cells 
        cells = [' C' + str(i).zfill(num_digits) for i in range(0, max_cell+1)]    
        return cells
    

    def get_timestamps(self, day, session):
        frames = [i for i in range(0, len(self.day_and_sessions_data[day][0][session]))]
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
    
    # use calculations from plt utils and subplot class to make trajectory/spike plots
    def get_lr_spike_plots(self, spike_sizes, line_sizes):
        output_path = os.path.join(self.main_dir, 'Longitudinal Spike Plots - all days')

        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for cell in self.cell_names:
            print(cell)
            figure= plt.figure(figsize=(5,5))
            plt.rcParams.update({'figure.max_open_warning': 0})
            axes = [figure.add_subplot(self.gs[i, j]) for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
            ax_indices = [[i, j] for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
            axes = [ax.axis('off') for ax in axes]

            for day_idx in range(0, len(self.day_and_sessions_data)): 
                for session in range(0, len(self.day_and_sessions_data[day_idx][1])):

                    timestamps = self.get_timestamps(day_idx, session)
                    cell_df = self.day_and_sessions_data[day_idx][1][session]
                    cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
                    spike_train = np.zeros_like(timestamps)

                if cell_event_timestamps is not None:
                    for event_ts in cell_event_timestamps:
                        abs_diffs= abs(timestamps - event_ts)
                        min_idx = np.argmin(abs_diffs, axis=0)
                        spike_train[min_idx] = 1

                head_x, head_y, angles = self.get_head_and_angles(day_idx, session)
                ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session, day_idx]), None)
                ax_to_plot_spike = axes[ax_to_plot_index]
                self.subplt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, spike_sizes = spike_sizes, line_size= line_sizes, axis = ax_to_plot_spike)
            destination = os.path.join(output_path, f'{cell}')
            figure.tight_layout(pad=1)
            figure.savefig(destination,dpi=300)
            plt.close()
            


    # get spike plots but only for cells that have spiking on every day 
    def get_spike_plots_all_cells_only(self, spike_sizes, line_sizes):
        output_path = os.path.join(self.main_dir, 'Longitudinal Spike Plots - all days have cell')
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for cell in self.cell_names:
            print(cell)
            figure= plt.figure(figsize=(5,5))
            plt.rcParams.update({'figure.max_open_warning': 0})

            axes = [figure.add_subplot(self.gs[i, j]) for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
            ax_indices = [[i, j] for j in range(0, self.num_days) for i in range(0, self.max_row_num)]
            #axes = [ax.axis('off') for ax in axes]
            day_has_cell = True

            for day_idx in range(0, len(self.day_and_sessions_data)): 
                for session in range(0, len(self.day_and_sessions_data[day_idx][1])):

                    timestamps = plt_util.get_timestamps(day_idx, session)
                    cell_df = self.day_and_sessions_data[day_idx][1][session]
                    cell_event_timestamps = cell_df['Time (s)'][cell_df[' Cell Name']==cell]
                    if len(cell_event_timestamps) == 0:
                        day_has_cell = False
                        break
                    spike_train = np.zeros_like(timestamps)

                    if cell_event_timestamps is not None:

                        for event_ts in cell_event_timestamps:
                            abs_diffs= abs(timestamps - event_ts)
                            spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    head_x, head_y, angles = self.get_head_and_angles(day_idx, session)
                    ax_to_plot_index = next((i for i, sublist in enumerate(ax_indices) if sublist == [session, day_idx]), None)
                    ax_to_plot_spike = axes[ax_to_plot_index].axis('off')
                    self.subplt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, spike_sizes = spike_sizes, line_size=line_sizes, axis = ax_to_plot_spike)

            if day_has_cell:
                destination = os.path.join(output_path, f'{cell}')
                figure.tight_layout(pad=1)
                figure.savefig(destination,dpi=300)
                plt.close()

if __name__ == '__main__':
    l = LongitudinalPlot(r'C:\Users\Gianna\Desktop\Analysis\lr_trajectories_test', [61, 70])
    l.get_lr_spike_plots(4, 1.25)