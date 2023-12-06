import os
import sys
sys.path.append(r'C:\Users\Gianna\Documents\Python Scripts\rsc_ca_plotting')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from src.plotting.subplot import Subplot
import src.plotting.plot_utils as plt_util
from src.workutils.handle_dirs import combine_files_get_num_sessions

class TimeSeriesPlots(object):
        def __init__(self, spike_directory, dlc_directory, output_folder_path, framerate, two_dim_arena_coords):
            self.framerate = framerate #Hz
            self.bearing_bin_size = 3 #degrees
            self.dist_bin_size = 2.5 #cm
            self.spike_dir = spike_directory
            self.dlc_dir = dlc_directory
            self.output_folder_path = output_folder_path
            self.num_sessions, self.sessions_data = combine_files_get_num_sessions(self.spike_dir, self.dlc_dir, self.output_folder_path)
            self.two_dim_arena_coords = two_dim_arena_coords
            self.arena_x_length = self.two_dim_arena_coords[0] 
            self.arena_y_length = self.two_dim_arena_coords[1]
            #instantiate a subplot object
            self.splt = Subplot(self.framerate, self.two_dim_arena_coords)
            print(f'Number of sessions: {self.num_sessions}')


        # input the types of subplots to be created as strings on one figure
        # output to desination
        # *args provided should be the name of plots provided, **kwargs should be the arguments to the plots
        # **kwargs will include:
        #                       + for spike plots: {"spike_line_color": #XXXXXX, "line_size": xx, "spike_size": xx}
        #                       + for barrier plots: {"barrier_coord1": [[x1,y1], [x2, y2]], "barrier_coord2": [[x3, y3], [x4, y4], 'barrier_coord3' = [[None, None], [None, None]]]
        #                       + for HD plots: {"hd_line_color": xx}
        #args = # rows 
        def plot_figures(self, output_folder_name, *args, **kwargs):
            num_rows = len(args)
            num_cols = self.num_sessions
            dir_output = os.path.join(self.output_folder_path, output_folder_name)
            print(dir_output)
            if not os.path.exists(dir_output):
                os.mkdir(dir_output)
            for cell in np.unique(self.sessions_data[0][1][' Cell Name']):
                print(cell)
                figure= plt.figure()
                plt.rcParams.update({'figure.max_open_warning': 0})
                axes = []
                ax_indices = []
                gs = GridSpec(nrows=num_rows, ncols=num_cols, wspace=0.75, hspace=0.75)
                polar_plots = ['ebc_boundary', 'ebc_barrier', 'ebc_boundary_barrier', 'hd_curve']
                for plot_num, plot_name in enumerate(args):
                    # number of axes needed to make subplots
                    for j in range(0, num_cols):
                        if plot_name in polar_plots:
                            axes.append(figure.add_subplot(gs[plot_num, j], projection="polar"))
                        else:
                            axes.append(figure.add_subplot(gs[plot_num, j]))
                        ax_indices.append([plot_num, j])
                for session_idx, session in enumerate(self.sessions_data): 
                    timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    #timestamps = plt_util.get_timestamps(self.sessions_data, session_idx, framerate=30)
                    cell_event_timestamps = session[1]['Time (s)'][session[1][' Cell Name']==cell]
                    #make an empty spike train
                    spike_train = np.zeros_like(timestamps)

                    #add a 1 to the spike train for the video frame closest to each cell event
                    for event_ts in cell_event_timestamps:                
                        abs_diffs = abs(timestamps - event_ts)
                        spike_train[abs_diffs == np.min(abs_diffs, axis=0)] = 1
                    
                    head_x, head_y, angles = plt_util.get_head_and_angles(self.sessions_data[session_idx][0], self.arena_x_length, self.arena_y_length)
                    head_x, head_y, angles = head_x[:-1], head_y[:-1], angles[:-1]
                    spike_train = spike_train[:-1]
                    for arg_num, arg in enumerate(args):
                        axis_to_plot_idx = next((i for i,
                                                  sublist in enumerate(ax_indices) if sublist == [arg_num, session_idx]), None)
                        axis_to_plot = axes[axis_to_plot_idx]
                        axis_to_plot.axis('off')
                        if ((arg == 'ebc_boundary_barrier')):

                            if ((kwargs['barrier_coords'][session_idx][0][0] is not None) &
                                 (kwargs['barrier_coords'][session_idx][1][0] is not None)):
                                
                                barrier_start = kwargs['barrier_coords'][session_idx][0]
                                barrier_end = kwargs['barrier_coords'][session_idx][1]
                                boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                                boundary_bearings, boundary_distances = boundary_bearings[:-1], boundary_distances[:-1]
                                barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles, barrier_start, barrier_end)
                                barrier_bearings, barrier_distances = barrier_bearings[:-1], barrier_distances[:-1]
                                all_bearings = np.concatenate([boundary_bearings, barrier_bearings],axis=1)
                                all_dists = np.concatenate([boundary_distances, barrier_distances],axis=1)
                                all_bearings, all_dists = all_bearings[:-1], all_dists[:-1]
                                self.splt.ebc_subplot(all_bearings, all_dists,
                                                       spike_train, destination=None, axis=axis_to_plot)                        
                        
                        elif (arg == 'ebc_boundary'):
                            boundary_bearings, boundary_distances = plt_util.ego_boundary_measurements(head_x, head_y, angles)
                            boundary_bearings, boundary_distances = boundary_bearings[:-1], boundary_distances[:-1]
                            self.splt.ebc_subplot(boundary_bearings, boundary_distances, spike_train,
                                                   destination= None, axis= axis_to_plot)
                        
                        elif ((arg == 'ebc_barrier') & ('barrier_coords' in kwargs)):
                            if ((kwargs['barrier_coords'][session_idx][0][0] is not None) & (kwargs['barrier_coords'][session_idx][1][0] is not None)):
#                               barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles,
                                                                                                              #kwargs['barrier_coords'][session_idx][0], kwargs['barrier_coords'][session_idx][1])
                                barrier_start = kwargs['barrier_coords'][session_idx][0]
                                barrier_end = kwargs['barrier_coords'][session_idx][1]

                                barrier_bearings, barrier_distances = plt_util.inserted_barrier_measurements(head_x, head_y, angles, barrier_start, barrier_end)
                                barrier_bearings, barrier_distances = barrier_bearings[:-1], barrier_distances[:-1]
                                self.splt.ebc_subplot(barrier_bearings, barrier_distances, spike_train, destination=None, axis= axis_to_plot)
                        
                        elif ((arg == 'spike_plot') & ('spike_line_color' in kwargs) & ('spike_size' in kwargs) & ('line_size' in kwargs)):
                            self.splt.path_spike_plot_subplot(head_x, head_y, angles, spike_train, destination=None, line_color = kwargs['spike_line_color'], spike_sizes = kwargs['spike_size'], line_size=kwargs['line_size'], axis = axis_to_plot)
                        
                        elif (arg == 'hd_curve') & ('hd_line_color' in kwargs):
                            axis_to_plot.axis('on')
                            self.splt.hd_curve_subplot(angles, spike_train, line_color= kwargs['hd_line_color'], destination=None, axis=axis_to_plot)
                        
                        elif (arg == 'heatmap'):
                            self.splt.heatmap_subplot(head_x, head_y, spike_train, destination=None, axis= axis_to_plot)
                        
                        else:
                            raise ValueError(fr"The argument {arg} provided is not a valid plot type.")
                plt.tight_layout()
                destination = os.path.join(dir_output, fr'{cell.lstrip()}')
                figure.savefig(destination,dpi=300)
                plt.close()

