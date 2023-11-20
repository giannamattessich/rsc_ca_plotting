import os
import matplotlib.pyplot as plt
from matplotlib import colors as mplcolors
import numpy as np
from astropy.convolution import convolve
from astropy.convolution.kernels import Gaussian2DKernel

#  class used to create figures / matplotlib subplots
#  can also be used to make single session spike plots 

class Subplot(object):
    def __init__(self, framerate, arena_coords):
        self.framerate = framerate
        self.arena_x_length = arena_coords[0] #cm
        self.arena_y_length = arena_coords[1]  
        self.max_wall_length = np.max([self.arena_x_length, self.arena_y_length])
        self.ebc_cutoff = self.max_wall_length / 2.
        
    
    def path_spike_plot_subplot(self, head_x,head_y,angles,spike_train,destination, line_color, spike_sizes, line_size, axis):
        if destination is not None:
            savedir = os.path.dirname(destination)
            if not os.path.isdir(savedir):
                os.makedirs(savedir)


        #grab locations and head directions where events occurred
        spike_x = head_x[spike_train>0]
        spike_y = head_y[spike_train>0]
        spike_angles = angles[spike_train>0]
    
        
        #circular colormap for head direction
        colormap = plt.get_cmap('hsv')
        norm = mplcolors.Normalize(vmin=0, vmax=360)

    #plot it!
    ####** can modify to change figure size**####
        fig = plt.figure()
        #plt.rcParams['lines.linewidth'] = 5
        axis.invert_yaxis()
        axis.plot(head_x,head_y,color=line_color,linewidth=line_size, alpha=0.6,zorder=0)
        axis.scatter(spike_x,spike_y,s=spike_sizes, c=spike_angles,cmap=colormap,norm=norm,zorder=1,clip_on=False)
        axis.axis('off')
        axis.set_aspect('equal')
        fig.tight_layout()
        
        #axis.axis('equal')
        #save if you provided a destination
        if destination is not None:
            fig.savefig(destination,dpi=300)
            plt.close()
            
        else:
            return axis
            
    # create EBC plots for multiple sessions / days and return axis to be plotted on 
    def ebc_subplot(self, boundary_bearings, boundary_distances, spike_train,destination,axis):
        if destination is not None:
            savedir = os.path.dirname(destination)
            if not os.path.isdir(savedir):
                os.makedirs(savedir)

        bearing_bin_size = 3 #degrees
        dist_bin_size = 2.5 #cm
        
        #figure out how many bins we'll have in the bearing and distance domains
        bearing_bin_num = int(np.ceil(360 / bearing_bin_size))
        dist_bin_num = int(np.ceil(self.ebc_cutoff / dist_bin_size))

        
        #bin the bearings and distances according to the bin sizes specified at the top of the script
        bearing_bins = np.digitize(boundary_bearings, bins=np.arange(0,360,bearing_bin_size)).astype(float) - 1
        dist_bins = np.digitize(boundary_distances, bins=np.arange(0,np.max(boundary_distances),dist_bin_size)).astype(float) - 1
        
        #make an array for bin occupancy and event counts
        occ = np.zeros([len(bearing_bins),bearing_bin_num,dist_bin_num])
        spikes = np.zeros([len(bearing_bins),bearing_bin_num,dist_bin_num])
        
        #boundaries outside the dist cutoff are discarded
        dist_bins[boundary_distances > self.ebc_cutoff] = np.nan
        bearing_bins[boundary_distances > self.ebc_cutoff] = np.nan
        
        #for every video frame, take which bins are occupied and increment the occupancy time (occ) and event counts (spikes) for those bins
        for i in range(len(bearing_bins)):
            
            occ[i, bearing_bins[i][~np.isnan(bearing_bins[i])].astype(int), dist_bins[i][~np.isnan(dist_bins[i])].astype(int)] = 1./self.framerate
            spikes[i, bearing_bins[i][~np.isnan(bearing_bins[i])].astype(int), dist_bins[i][~np.isnan(dist_bins[i])].astype(int)] = spike_train[i]

        #sum across all time points in the session
        summed_occ = np.sum(occ,axis=0)
        summed_spikes = np.sum(spikes,axis=0)
        
        #divide events by occupancy time to get a ratemap
        raw_ratemap = summed_spikes/summed_occ
    
        #we need to smooth the ratemap, but the smoothing kernel doesn't understand that the direction
        #axis is circular, so we can stack three ratemaps next to each other, smooth across them, and then take the middle one
        hist3 = np.concatenate((raw_ratemap,raw_ratemap,raw_ratemap),axis=0)
        hist3 = convolve(hist3,Gaussian2DKernel(x_stddev=2,y_stddev=2))
        smoothed_ratemap = hist3[len(raw_ratemap):len(raw_ratemap)*2]

        #bin edges for plotting
        angle_vals = np.deg2rad(np.arange(0,361,bearing_bin_size))
        dist_vals = np.arange(0,self.ebc_cutoff,dist_bin_size)

        #append first angle bin to end of ratemap because 0deg = 360deg
        smoothed_ratemap = np.concatenate([smoothed_ratemap,smoothed_ratemap[0,np.newaxis]])
        
        fig = plt.figure() 
        #fig.tight_layout()
        fig.tight_layout()
        axis.set_theta_zero_location("N")
        axis.pcolormesh(angle_vals,dist_vals,smoothed_ratemap.T,vmin=0)
        axis.axis('off')
        
        #save if you provided a destination
        if destination is not None:
            fig.savefig(destination,dpi=300)
            plt.close()
            
        else:
            return axis 
        
    def heatmap_subplot(self, head_x, head_y, spike_train, destination=None, axis=None):
        
        binsize = 3. #cm
        stddev = 1 #for Gaussian smoothing - higher values will smooth more
        
        xbin_edges = np.arange(np.min(head_x),np.max(head_x),binsize)
        ybin_edges = np.arange(np.min(head_y),np.max(head_y),binsize)

        xbins = np.digitize(head_x, bins=xbin_edges) - 1
        ybins = np.digitize(head_y, bins=ybin_edges) - 1
        
        spikes = np.zeros((len(xbin_edges),len(ybin_edges)))
        occ = np.zeros((len(xbin_edges),len(ybin_edges)))
        
        for i in range(len(xbins)):
            spikes[xbins[i],ybins[i]] += spike_train[i]
            occ[xbins[i],ybins[i]] += 1./self.framerate
            
        raw_heatmap = spikes/occ
        smoothed_heatmap = convolve(raw_heatmap, Gaussian2DKernel(x_stddev=stddev,y_stddev=stddev))
        smoothed_heatmap = smoothed_heatmap.T

        fig = plt.figure()
        axis.imshow(smoothed_heatmap,origin='lower',cmap='viridis',vmin=0)
        axis.set_aspect('equal')
        axis.axis('off')
        
        #save if you provided a destination
        if destination is not None:
            fig.savefig(destination,dpi=300)
            plt.close()
            
        else:
            return axis

    def hd_curve_subplot(self, angles, spike_train, line_color, destination=None, axis=None):
        binsize = 12. #degrees
        
        bin_edges = np.arange(0,360,binsize)
        
        angle_bins = np.digitize(angles,bins=bin_edges) - 1
        
        spikes = np.zeros(len(bin_edges))
        occ = np.zeros(len(bin_edges))
        
        for i in range(len(angle_bins)):
            spikes[angle_bins[i]] += spike_train[i]
            occ[angle_bins[i]] += 1./self.framerate
            
        curve = spikes/occ
        
        #append first bin to end because 0 = 360deg
        curve = np.array( list(curve) + [curve[0]] )
        xvals = np.array( list(bin_edges) + [0] )
        
        fig = plt.figure()
        #ax = fig.add_subplot(111,projection='polar')
        axis.yaxis.grid(False)
        axis.xaxis.grid(linewidth=2,color='k')
        axis.spines['polar'].set_visible(False)
        axis.plot(np.deg2rad(xvals), curve, color= line_color, linestyle='-')
        axis.set_xticks([0,np.pi/2.,np.pi,3.*np.pi/2.])
        axis.set_xticklabels([0,90,180,270])
        axis.set_yticklabels([])
        axis.set_theta_offset(0)
        
        #save if you provided a destination
        if destination is not None:
            fig.savefig(destination,dpi=300)
            plt.close()
            
        else:
            return axis
