import os
import traceback
import shutil
import pandas as pd

# functions for finding directories with calcium/DLC files and creating directories for files 

#check if provided path can be created 
def can_create_directory(directory_path):
    parent_directory = os.path.dirname(directory_path)
    if os.path.isabs(directory_path) & os.access(parent_directory, os.W_OK):
        os.makedirs(directory_path, exist_ok=True)
        return True 
    else:
        return False

# find the first sequential numbers after the input string to be searched 
# use to find which files belong to which session
# ex. timeseries spikes spike files naming scheme is yyyymmdd-timeseries_spikes_run{run number}, so use 'run' keyword to find the sequential run number 
def get_session_number(file, string_to_search):
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

# get file in DLC naming scheme -> with 'session' or 'session' followed by session number and 'DLC' somewhere in name 
def get_dlc_files(dlc_directory):
        dlc_dict = {}
        for file in os.listdir(dlc_directory):
            if (('DLC' in file) & (file.endswith('.csv'))):
                session_to_add = get_session_number(file, 'session')
                session_to_add = f'session{session_to_add}'
                if session_to_add not in dlc_dict:
                    dlc_dict[session_to_add] = file
        if len(dlc_dict) == 0:
            raise Exception('Could not find any DLC files in the provided directory.')
        return dlc_dict

def get_spike_files(spike_directory):
    spike_dict = {}
    for file in os.listdir(spike_directory):
        if (('run' in file) & (file.endswith('.csv'))):
            session_to_add = get_session_number(file, 'run')
            session_to_add = f'session{session_to_add}'
            if session_to_add not in spike_dict:
                spike_dict[session_to_add] = file
    if len(spike_dict) == 0:
            raise Exception('Could not find any DLC files in the provided directory.')
    return spike_dict

def move_files(files, destination):
    if not os.path.exists(destination) & can_create_directory(destination):
        os.makedirs(os.path.normpath(destination))

    try:
        # Move each file to the destination directory
        for file_path in list(set(files)):
            file_name = os.path.basename(file_path)
            destination_path = os.path.normpath(os.path.join(destination, file_name))
            if not os.path.exists(destination_path):
                shutil.copy(file_path, destination_path)
    except IOError:
        print(fr'Could not move files to {destination}.')
        traceback.print_exc()


####*** create nested array of sessions and files for each session and find number of sessions for timeseries plots***####
# each array within represents a session, inner arrays contain tracking file and event file dataframes for that session in the sessions_data variable
# ex. sessions_data = [[session1_dlc, session1_event], [session2_dlc, session2_event], [session3_dlc, session3_event]]
# return sessions_data and create directory if spike and dlc dir are not the same 
def combine_files_get_num_sessions(spike_dir, dlc_dir, output_folder):
    sessions_data= []
    num_sessions = 0
    spike_dict = get_spike_files(spike_dir)
    dlc_dict = get_dlc_files(dlc_dir)
    if ((spike_dict.keys() != dlc_dict.keys()) | (len(spike_dict) != len(dlc_dict))):
        raise Exception('The spike files and DLC files provided do not include the same dates or session numbers. Please try again with a different directory or renaming files to match the scheme.')
    elif (spike_dict.keys() == dlc_dict.keys()):
        num_sessions = len(spike_dict.keys())
        for session_num in spike_dict.keys():
            dlc_file = os.path.join(dlc_dir, dlc_dict[session_num])
            spike_file = os.path.join(spike_dir, spike_dict[session_num])
            #check if data frames contain data and are not empty
            dlc_empty = os.path.getsize(dlc_file) == 0
            spike_empty = os.path.getsize(spike_file) == 0
            if ((spike_dir == dlc_dir) & ((not dlc_empty) & (not spike_empty))):
                sessions_data.append([pd.read_csv(dlc_file, header=[1,2]), pd.read_csv(spike_file)])
            elif ((not dlc_empty) & (not spike_empty) & can_create_directory(output_folder)):
                move_files([dlc_file, spike_file], output_folder)
                new_dlc_path = os.path.join(output_folder, os.path.basename(dlc_file))
                new_spike_path = os.path.join(output_folder, os.path.basename(spike_file))
                sessions_data.append([pd.read_csv(new_dlc_path, header=[1,2]), pd.read_csv(new_spike_path)])
            elif ((not dlc_empty) & (not spike_empty) & (not can_create_directory(output_folder))):
                raise Exception(f'The output folder {output_folder} could not be created. Please check that it is a valid file path.')
            elif (dlc_empty):
                raise Exception(f'The file {dlc_file} is empty.')
            elif (spike_empty):
                raise Exception(f'The file{spike_file} is empty.')
    return num_sessions, sessions_data

