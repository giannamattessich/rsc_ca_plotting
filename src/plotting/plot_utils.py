import numpy as np
from scipy.stats import zscore

##** utility functions to use in plots-> includes calculations for spike/ebc plots **##

#compute head and angles from ear posititions and remove outliers 
def calc_positions(tracking_data):
    #grab tracking data for left and right ear 
    left_ear_x = np.array(tracking_data['Left Ear','x'])
    left_ear_y = np.array(tracking_data['Left Ear','y'])
    
    right_ear_x = np.array(tracking_data['Right Ear','x'])
    right_ear_y = np.array(tracking_data['Right Ear','y'])
    
    #remove nondetects (defined as likelihood < .1)
    left_ear_x[tracking_data['Left Ear','likelihood'] < .1] = 0
    left_ear_y[tracking_data['Left Ear','likelihood'] < .1] = 0
    right_ear_x[tracking_data['Right Ear','likelihood'] < .1] = 0
    right_ear_y[tracking_data['Right Ear','likelihood'] < .1] = 0
           
    #stack position data into one array
    positions = np.stack((left_ear_x,left_ear_y,right_ear_x,right_ear_y)).T
    
    #try to detect and remove outliers
    for i in range(4):
        zscores = np.abs(zscore(positions[:,i]))
        for j in np.where(zscores>2)[0]:
            positions[j,i] = 0 
    
    #linear interpolation of nondetects
    for i in range(len(positions)):
        for j in range(4):
            if positions[i][j] == 0:
                x = 0
                count = 1
                while x == 0:
                    if i+count < len(positions):
                        if positions[i+count][j] == 0:
                            count +=1
                        elif positions[i+count][j] > 0:
                            if i>0:
                                positions[i][j] = positions[i-1][j] + (positions[i+count][j] - positions[i-1][j])/count
                                x=1
                            else:
                                positions[i][j] = positions[i+count][j]
                                x=1
                    else:
                        positions[i][j] = positions[i-1][j]
                        x=1
    
    #compute head direction from ear positions (then add 90 so hd = 0deg when animal faces East)
    angles = np.rad2deg(np.arctan2(positions[:,3] - positions[:,1], positions[:,2] - positions[:,0]))
    angles = -(angles - 360)
    angles = angles%360
    
    head_x = (positions[:,0] + positions[:,2]) / 2.
    head_y = (positions[:,1] + positions[:,3]) / 2.
    
    return head_x, head_y, angles


def ego_boundary_measurements(head_x,head_y,angles):
    ''' compute the ego bearings and distances of points along the walls '''
    
    #how many points to break the walls into along x and y dimensions
    x_bins = 30
    y_bins = 30
    
    #linear interpolate "wall points" between each corner
    #walls are defined as 1cm beyond the animal's min and max x and y positions
    xcoords = np.linspace(np.min(head_x)-1.,np.max(head_x)+1.,x_bins+1,endpoint=True)
    ycoords = np.linspace(np.min(head_y)-1.,np.max(head_y)+1.,y_bins+1,endpoint=True)
    
    #stack coords all together
    w1 = np.stack((xcoords,np.repeat(np.max(ycoords)+1.,x_bins+1)))
    w3 = np.stack((xcoords,np.repeat(np.min(ycoords)-1.,x_bins+1)))
    w2 = np.stack((np.repeat(np.max(xcoords)+1.,y_bins+1),ycoords))
    w4 = np.stack((np.repeat(np.min(xcoords)-1.,y_bins+1),ycoords))
    all_walls = np.concatenate((w1,w2,w3,w4),axis=1)
    
    #vectors for distance from animal along x and y dimensions
    wall_x = np.zeros((len(all_walls[0]),len(head_x)))
    wall_y = np.zeros((len(all_walls[1]),len(head_y)))
    
    #calculate the distances
    for i in range(len(head_x)):
        wall_x[:,i] = all_walls[0] - head_x[i]
        wall_y[:,i] = all_walls[1] - head_y[i]
        
    #compute egocentric bearings and distances
    wall_bearings = (np.rad2deg(np.arctan2(wall_y,wall_x))%360 - angles)%360
    wall_dists = np.sqrt(wall_x**2 + wall_y**2)
    
    return wall_bearings.T, wall_dists.T

def inserted_barrier_measurements(head_x,head_y,angles,barrier_coord_1,barrier_coord_2):
    ''' similar to ego_boundary_measurements but for a single inserted barrier with endpoints specified
    barrier_coord_1 = [x,y]
    barrier_coord_2 = [x,y] '''
    
    #how many points to break the barrier into
    barrier_bins = 10
    
    #linear interpolate "barrier points" between the ends of the barrier
    barrier_xcoords = np.linspace(barrier_coord_1[0],barrier_coord_2[0],barrier_bins+1,endpoint=True)
    barrier_ycoords = np.linspace(barrier_coord_1[1],barrier_coord_2[1],barrier_bins+1,endpoint=True)


    #vectors for distance from animal along x and y dimensions
    barrier_x = np.zeros((len(barrier_xcoords),len(head_x)))
    barrier_y = np.zeros((len(barrier_ycoords),len(head_y)))
    
    #calculate the distances
    for i in range(len(head_x)):
        barrier_x[:,i] = barrier_xcoords - head_x[i]
        barrier_y[:,i] = barrier_ycoords - head_y[i]
        
    #compute egocentric bearings and distances
    barrier_bearings = (np.rad2deg(np.arctan2(barrier_y,barrier_x))%360 - angles)%360
    barrier_dists = np.sqrt(barrier_x**2 + barrier_y**2)
    
    return barrier_bearings.T, barrier_dists.T


#scale head and angle pixel positions to arena by taking the minimum x and y values and 
def get_head_and_angles(dlc_file, arena_x_length, arena_y_length):
    head_x, head_y, angles = calc_positions(dlc_file)
    head_x -= np.min(head_x)
    head_x *= (arena_x_length/np.max(head_x))
    head_y -= np.min(head_y)
    head_y *= (arena_y_length/np.max(head_y))
    return head_x, head_y, angles

# convert frames to seconds
def frame_num_to_seconds(framerate, frame_num):
    return frame_num / framerate

# create array of timestamps to use 
def get_timestamps(sessions_data, session_idx, framerate):
    dlc_file = sessions_data[session_idx][0]
    length = len(dlc_file)
#     #get number of frames from length of DLC file
    frames = [frame for frame in range(0, length)]
    #convert frames to timestamps
    timestamp_data = [float(frame_num_to_seconds(framerate, frame)) for frame in frames]

#     #start the session at time 0
    timestamp_data = timestamp_data - np.min(timestamp_data)
#     #make an array 
    timestamps = np.array(timestamp_data).flatten()

    return timestamps
