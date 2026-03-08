"""
Made by Claude. GUI control utilities for live optomechanics measurements.

Provides lightweight control interfaces and configuration helpers for
interactive data acquisition sessions.
"""
import traceback
import json



def Control_PID(pid_settings = {}, file = r"C:\Users\RoomTemp\Documents\Python\remote_control.json", update = True):
    """
    Made by Claude. Update PID controller settings via a shared JSON configuration file.

    Opens ``file``, merges the key-value pairs in ``pid_settings`` into the
    ``Remote_Control`` section, optionally sets the ``update`` flag to
    ``True``, and writes the modified JSON back to disk.  Prints the previous
    and new settings and returns the current temperature read from the file.

    Parameters
    ----------
    pid_settings : dict, optional
        Mapping of PID setting keys to their new values.  Each key-value pair
        is written into ``all_settings['Remote_Control']``.  Default is
        ``{}`` (no changes).
    file : str, optional
        Path to the remote-control JSON file.
        Default is ``r"C:\\Users\\RoomTemp\\Documents\\Python\\remote_control.json"``.
    update : bool, optional
        If ``True``, sets ``all_settings['Remote_Control']['update']`` to
        ``True`` after applying ``pid_settings``.  Default is ``True``.

    Returns
    -------
    float or None
        The current temperature value read from
        ``all_settings['Remote_Control']['temp']``, or ``None`` if an
        exception is caught.

    Raises
    ------
    FileNotFoundError
        Caught internally — prints a message and traceback; returns ``None``.
    KeyError
        Caught internally — prints a message and traceback; returns ``None``.
    Exception
        All other exceptions are caught internally — prints traceback; returns
        ``None``.
    """
    try:
        with open(file, 'r') as f:
            all_settings = json.load(f)
            print(f"previous settings: {all_settings}")
            for key, item in pid_settings.items():
                all_settings['Remote_Control'][key] = item
                
            if update:    
                all_settings['Remote_Control']["update"] = True
            temp = all_settings['Remote_Control']['temp']
            
            

        with open(file, "w") as f:
            json.dump(all_settings, f)
            print(f"updated PID settings: {pid_settings.items()}")
            print("file_updated")
        print(f" current temperature = {temp}")
        return temp
    
    except FileNotFoundError as e:
        print("PID settings file not found.")
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())
            
    except KeyError as e:
        print(f"Missing key in PID settings file: {e}. Please add:\n {e} entry")
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())
        
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())
    