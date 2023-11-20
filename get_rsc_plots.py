import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import src.plotting.plot_utils as plt_util
from src.plotting.subplot import Subplot

# class to plot single day recordings 

####** Input main working directory that contains session files(dlc, cell event) in main_dir variable**####
    # script will find files in directory by name automatically, so files in directory should be named in the common scheme 
    #tracking file: contains 'session' followed by its number and 'DLC' in name (ex. dlc...session1 or dlc..session_1)
    #event file: contains 'run' followed by session num. (ex. ..._timeseries_run1)
####** Input lengths of arena and coordinates of barriers as an array**####
class TimeSeriesPlots(object):
        def __init__(self, main_dir, framerate, two_dim_arena_coords):
            self.framerate = framerate #Hz
            self.bearing_bin_size = 3 #degrees
            self.dist_bin_size = 2.5 #cm
            self.main_dir = main_dir
            self.directory = sorted(os.listdir(main_dir))
            self.files = []
            self.session_numbers = self.find_num_sessions()
            self.num_sessions = len(self.session_numbers)
            self.sessions_data = self.get_files()
            self.two_dim_arena_coords = two_dim_arena_coords
            self.arena_x_length = self.two_dim_arena_coords[0] 
            self.arena_y_length = self.two_dim_arena_coords[1]
            #instantiate a subplot object
            self.splt = Subplot(self.framerate, self.two_dim_arena_coords)
            print(f'Number of sessions: {self.num_sessions}')

        # find the first sequential numbers after the input string to be searched 
        # use to find which files belong to which session
        # ex. timeseries spikes spike files naming scheme is yyyymmdd-timeseries_spikes_run{run number}, so use 'run' keyword to find the sequential run number 
        def get_session_number(self, file, string_to_search):
            if string_to_search in file:
                start_idx = file.index(string_to_search)
                found_session_num = False
                result = ""
                # begin searching for session num in all chars after the input string
                for char in file[(start_idx + len(string_to_search)):]:
                    if char.isdigit():
                        found_session_num = True
                        result += char
                    elif found_session_num:
                        break
                return int(result)

       
        #find number of unique sessions in directory using their file names
        def find_num_sessions(self):
            session_numbers = set()
            for file in self.directory:
                if (('session' in file) & (file.endswith(".csv"))):
                    num_session = self.get_session_number(file, 'session')
                    session_numbers.add(num_session)
            session_numbers = sorted(list(session_numbers))
            # return an array that includes the number of every session -> (ex. [1, 2, 3] for 3 sessions)
            return session_numbers
        
        ####*** create nested array of sessions and files for each session ***####
        # each array within represents a session and inner arrays contain tracking file and event file dataframes in the sessions_data variable
        # ex. sessions_data = [[session1_dlc, session1_event], [session2_dlc, session2_event], [session3_dlc, session3_event]]
        def get_files(self):
            dlc_dict = {}
            spike_dict = {}
            for file in self.directory:
                if (('DLC' in file) & (file.endswith('.csv'))):
                    session_to_add = self.get_session_number(file, 'session')
                    session_to_add = f'session{session_to_add}'
                    if session_to_add not in dlc_dict:
                        dlc_dict[session_to_add] = file
                elif (('run' in file) & (file.endswith('.csv'))):
                    session_to_add = self.get_session_number(file, 'run')
                    session_to_add = f'session{session_to_add}'
                    if session_to_add not in spike_dict:
                        spike_dict[session_to_add] = file
            sessions_data = []
            for num in self.session_numbers:
                name = f'session{num}'
                sessions_data.append([pd.read_csv(os.path.join(self.main_dir, dlc_dict[name]), header=[1,2]),
                                        pd.read_csv(os.path.join(self.main_dir, spike_dict[name]))])
            return sessions_data

        # creating an axs for each session/array of axes and number of sessions as an argument to plt.subplots()
        # outputs single row of trajectory plots for each session
        def get_spike_plots(self, destination, line_color, spike_sizes, line_sizes,  output_folder_name):
            spike_plot_dir = os.path.join(self.main_dir, output_folder_name)
            if not os.path.exists(spike_plot_dir):
                os.mkdir(spike_plot_dir)
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                figure, axes = plt.subplots(1,self.num_sessions,figsize=(10,5))
                plt.rcParams.update({'figure.max_open_warning': 0})
                session_idx = 0
                for session in self.sessions_data: 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0])
                    ax_to_plot = axes[session_idx]
                    ax_to_plot.axis('off')
                    self.splt.path_spike_plot_subplot(head_x,head_y,angles,spike_train, destination=None,spike_sizes=spike_sizes, line_size = line_sizes, axis=ax_to_plot)
                    session_idx += 1
                destination = os.path.join(spike_plot_dir, f'{cell}')
                #plt.tight_layout()
                figure.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
                figure.savefig(destination,dpi=300)
                plt.close()

        # create figure with both trajectory and EBCs tuned to boundary plots
        def get_combined_spike_ebc_boundary(self, output_folder_name):
            spike_ebc_bound_dir = os.path.join(self.main_dir, output_folder_name)
            if not os.path.exists(spike_ebc_bound_dir):
                os.mkdir(spike_ebc_bound_dir)
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                figure= plt.figure()
                plt.rcParams.update({'figure.max_open_warning': 0})
                #figure, axes = plt.subplots(2, num_sessions,figsize=(10,15))
                axes= []
                for i in range(1, (self.num_sessions * 2 + 1)):
                    if i > self.num_sessions:
                        axes.append(figure.add_subplot(2, self.num_sessions, i, projection='polar'))
                    else:
                        axes.append(figure.add_subplot(2, self.num_sessions, i))
                session_idx = 0
                for session in self.sessions_data: 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0])
                    boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                    ax_to_plot_spike = axes[session_idx]
                    ax_to_plot_ebc = axes[session_idx + self.num_sessions]
                    self.splt.path_spike_plot_subplot(head_x,head_y,angles,spike_train, destination=None,spike_sizes=4,line_size = 0.75, axis=ax_to_plot_spike)
                    self.splt.ebc_subplot(boundary_bearings, boundary_distances, spike_train, destination= None,axis=ax_to_plot_ebc)
                    session_idx += 1
                destination = os.path.join(spike_ebc_bound_dir, f'{cell}')
                figure.tight_layout(pad=1)
                figure.savefig(destination,dpi=300)
                plt.close()

        # create figure with trajectory, EBCs tuned to boundaries, EBCs tuned to barriers, and EBCs tuned to both boundaries and barriers plots
        def get_spike_ebc_boundary_and_barrier(self, barriers_coords, output_folder_name):
            #create directory to put plots in 
            spike_ebc_bound_dir = os.path.join(self.main_dir, output_folder_name)
            if not os.path.exists(spike_ebc_bound_dir):
                os.mkdir(spike_ebc_bound_dir)
                #iterate through cells and create figure for each
            height_ratios=[3,2,1.85,1.85]
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                #create plot and axes for subplots
                figure= plt.figure(figsize=(5,5))
                plt.rcParams.update({'figure.max_open_warning': 0})
                axes= []
                gs = GridSpec(4, self.num_sessions, height_ratios=height_ratios, hspace=0.25, wspace=0.25)

                for i in range(0, 4):
                    for j in range(0, self.num_sessions):
                        if i == 0:
                            axes.append(figure.add_subplot(gs[0, j])) 
                        else:
                            axes.append(figure.add_subplot(gs[i, j], projection='polar'))
                session_idx = 0
                for session in self.sessions_data: 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, 30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0])

                    boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                    
                    #calculate distance and bearings of inserted barrier
                    if ((barriers_coords[session_idx][0][0] is not None) & (barriers_coords[session_idx][1][0] is not None)):
                        barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles, barriers_coords[session_idx][0], barriers_coords[session_idx][1])
                    
                    ax_to_plot_spike = axes[session_idx]
                    ax_to_plot_bound = axes[session_idx + self.num_sessions]
                    ax_to_plot_barrier = axes[session_idx + (self.num_sessions * 2)]
                    ax_to_plot_bound_barrier = axes[session_idx + (self.num_sessions * 3)]

                    self.splt.path_spike_plot_subplot(head_x,head_y,angles,spike_train, destination=None,spike_sizes=0.1, line_size = 0.4,axis=ax_to_plot_spike)
                    
                    self.splt.ebc_subplot(boundary_bearings, boundary_distances, spike_train, destination= None, axis=ax_to_plot_bound)

                    if ((barriers_coords[session_idx][0][0] is not None) & (barriers_coords[session_idx][1][0] is not None)):
                        self.splt.ebc_subplot(barrier_bearings, barrier_distances, spike_train, destination=None, axis=ax_to_plot_barrier)
                        all_bearings = np.concatenate([boundary_bearings, barrier_bearings],axis=1)
                        all_dists = np.concatenate([boundary_distances, barrier_distances],axis=1)
                        self.splt.ebc_subplot(all_bearings, all_dists, spike_train, destination=None, axis=ax_to_plot_bound_barrier)
                    else:
                        ax_to_plot_barrier.set_axis_off()
                        ax_to_plot_bound_barrier.set_axis_off()
                    session_idx += 1
                    destination = os.path.join(spike_ebc_bound_dir, f'{cell}')
                figure.tight_layout()
                figure.savefig(destination,dpi=300)
                plt.close()

        # create single row heatmaps for one or multiple sessions
        def get_heatmaps(self, output_folder_name):
            heatmap_dir = os.path.join(self.main_dir, output_folder_name)
            if not os.path.exists(heatmap_dir):
                os.mkdir(heatmap_dir)
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                figure= plt.figure()
                axes= []
                for i in range(1, (self.num_sessions + 1)):
                    axes.append(figure.add_subplot(1, self.num_sessions, i))
                session_idx = 0
                for session in self.sessions_data: 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0])
                    ax_to_plot_heat = axes[session_idx]
                    self.splt.heatmap_subplot(head_x, head_y, spike_train, destination=None, axis=ax_to_plot_heat)
                    session_idx += 1
                destination = os.path.join(heatmap_dir, f'{cell}')
                figure.tight_layout()
                figure.savefig(destination,dpi=300)
                plt.close()

        # create single row of head direction curves 
        def get_hd_curves(self, output_folder_name):
            hdc_dir = os.path.join(self.main_dir, output_folder_name)
            if not os.path.exists(hdc_dir):
                os.mkdir(hdc_dir)
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                figure= plt.figure(figsize=(20,20))
                axes= []
                for i in range(1, (self.num_sessions + 1)):
                    axes.append(figure.add_subplot(1, self.num_sessions, i,  projection='polar'))
                session_idx = 0
                for session in self.sessions_data: 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0])
                    ax_to_plot_hdc = axes[session_idx]
                    self.splt.hd_curve_subplot(angles, spike_train, destination=None, axis=ax_to_plot_hdc)
                    session_idx += 1
                destination = os.path.join(hdc_dir + f'{cell}')
                figure.tight_layout()
                figure.savefig(destination,dpi=300)
                plt.close()
                

if __name__ == '__main__':
    plots = TimeSeriesPlots(r"C:\Users\Gianna\Desktop\Analysis\20230214_kimchi\New data", 30, [60, 71])
    
    ####**** USER INPUT ****####

    # trajectory plots -> input line size, spike size, and name of output folder 
    #plots.get_spike_plots(line_sizes=1.5, spike_sizes=8, output_folder_name='Spike Plots')


    # trajectory / ebc boundary plots -> provide output folder name
    #plots.get_combined_spike_ebc_boundary('Spike + EBC Boundary Plots')
 
    
    # trajectory / ebc boundary / ebc barrier -> input barrier coordinates and output folder name

        # barrier coords should be provided as nested array
        # each session requires both a start and end point in the array
        # if session does not include barrier, then provide None as the coord arguments for both start and end
        # EXAMPLE:
        #       session 1 coords = [[21, 30], [30, 36]] ( start point (21, 30) and end point (30, 36) )
        #       session 2 coords = [[20, 36], [45, 30]]
        #       session 3 coords = [[None, None], [None, None]]
        #       barriers coords input for these sessions would be [[[21, 30], [30, 36]], [[20,36], [45, 30]], [[None, None], [None, None]]]


    ####**** COORDS FOR KIMCHI 20230214 -> [[[None, None], [None, None]], [[15,30], [36,30]], [[31,30], [31,51]], [[35,27], [20,40]], [[None, None], [None, None]]]

    # plots.get_spike_ebc_boundary_and_barrier([[[None, None], [None, None]], 
    #                                            [[15,30], [36,30]], 
    #                                              [[31,30], [31,51]],
    #                                                [[35,27], [20,40]],
    #                                                  [[None, None], [None, None]]], output_folder_name = 'Spike + EBC Boundary+Barrier Plots')

    # heatmaps -> provide output folder name
    #plots.get_heatmaps(output_folder_name = 'Heatmaps')

    # head direction curves -> provide output folder name
    #plots.get_hd_curves(output_folder_name = 'Head Direction Curves)











#### to be added to file later => dynamically create any plots together on one figure by specifying their names
    
        # options ->
        # 1) 'trajectory'
        # 2) 'ebc boundary'
        # 3) 'ebc barrier'
        # 4) 'ebc boundary/barrier
        # 4) 'heatmap'
        # 5) 'hd curve'

        # def get_plots(self, *args, output_folder_name, fig_size, spike_sizes=None, line_sizes=None, barrier_coords= None):
        #     output_dir = os.path.join(self.main_dir, output_folder_name)
        #     if not os.path.exists(output_dir):
        #         os.mkdir(output_dir)
        #     for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
        #         print(cell)
        #         figure = plt.figure(figsize=fig_size)
        #         if not args:
        #             raise ValueError('No plot type provided')
        #         num_rows = len(args)
        #         axes = []
        #         gs = GridSpec(num_rows, self.num_sessions)
        #         cases
