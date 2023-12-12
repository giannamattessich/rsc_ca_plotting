import numpy as np
import re

# using file string to get day label 
def get_day_digit(file_string):
    found_digit = False
    result = "day_"
    for char in file_string:
        if char.isdigit():
            found_digit = True
            result += char
        elif found_digit:
            break
    return result

# use regex to find the digits in cell name
# timeseries automatically outputs cells with a trailing white space and a prefix of ' C'
def get_cell_num_from_name(cell_name):
    match = re.search(r'C(\d+)', cell_name.strip())
    if match:
        cell_num = int(match.group(1))
        return cell_num
    
# check the spike files for all days to find the max cell value using its number
def find_max_cell_day(day_session_data):
    max = 0
    for day in day_session_data:
        cells = day[1][0][' Cell Name']
        # strip string to get cell number
        cell_numbers = cells.apply(lambda x: get_cell_num_from_name(x))
        day_max = np.max(cell_numbers)
        if day_max > max:
            max = day_max
    return max

    # find the number of digits in the maximum cell value and name all cells according to the number of digits in max 
def get_cell_names_from_max(day_session_data):
    max_cell = find_max_cell_day(day_session_data)
    num_digits = len(str(get_cell_num_from_name(' C' + str(max_cell))))
    # use z fill to rename cells 
    cells = [' C' + str(i).zfill(num_digits) for i in range(0, max_cell+1)]    
    return cells

