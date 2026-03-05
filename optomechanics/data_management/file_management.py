import os
import matplotlib.pyplot as plt
from datetime import datetime



def make_path(folders):
    """
    Made by Claude. Build a backslash-separated path string from an ordered list of folder names.

    Parameters
    ----------
    folders : iterable of str
        Folder names in hierarchical order (outermost first).

    Returns
    -------
    str
        Path string with a trailing backslash, e.g.
        ``'C:\\\\Data\\\\2024\\\\'``.
    """
    
    path = ""
    for folder in folders:
        path = "{a}{b}\\".format(a = path,b = folder)
    
    return path

def dated_file_maker(base_path):
    """
    Made by Claude. Create a year/month/day directory hierarchy under a base path.

    Appends the current date (``year\\month_name\\day``) to `base_path` and
    creates any missing directories in the hierarchy.  Only the day folder is
    checked first; month and year folders are created if absent.

    The expected base path format is::

        'C:\\\\Users\\\\FridgeDaddy\\\\Documents\\\\Experiment Data'

    Resulting in a dated path such as::

        'C:\\\\Users\\\\FridgeDaddy\\\\Documents\\\\Experiment Data\\\\2024\\\\February\\\\24\\\\'

    Parameters
    ----------
    base_path : str
        Root directory under which the dated folder structure is created.

    Returns
    -------
    str
        Full path to the day folder (with trailing backslash).
    """
    current_date = datetime.now()
    
    #Add the year, month, day in number format to the base_path
    base_path = base_path + f"\\{current_date.year}\\{current_date.month}\\{current_date.day}"

    date_list = ["January", "February", "March", "April", "May", "June", "July", "August",
                 "September", "October", "November", "December"]
    
    
    
    #Checks for the date folders only to see if they exist, makes them if they don't
    #could be condensed into a for loop#
    
    #print(f"base path before split = {base_path}")
    base_path_folders = base_path.split("\\")
    try:base_path_folders.remove("")
    except ValueError: None
    #print(f"base path folders list = {base_path_folders}")
    
    day = base_path_folders[-1]
    month = base_path_folders[-2]
    year = base_path_folders[-3]   

    #Added to convert number months to follow existing system of word months
    base_path = make_path(base_path_folders)
    if month in ["1","2","3","4","5","6","7","8","9","10","11","12"]:
        
        int_month = int(month)
        base_path_folders[-2] = date_list[int_month-1]
        #print(f"base path folders - after reseting month = {base_path_folders}")
        base_path = make_path(base_path_folders)


    if os.path.isdir(base_path) == 0:               #Day check
        path_to_month = make_path(base_path_folders[:-1])
        
        if os.path.isdir(path_to_month) == 0:              #month check
            path_to_year = make_path(base_path_folders[:-2])
            
            if os.path.isdir(path_to_year) == 0:          #year check
                #print(f"making directory for year: {path_to_year}")
                os.mkdir(path_to_year)#year
            #print(f"making directory for month: {path_to_month}")
            os.mkdir(path_to_month)#month
        #print(f"making directory for day: {base_path}")
        os.mkdir(base_path)# day
        
    return base_path

