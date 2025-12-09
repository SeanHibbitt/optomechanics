
import traceback
import json



def Control_PID(pid_settings = {}, file = r"C:\Users\RoomTemp\Documents\Python\remote_control.json", update = True):
    """
    Controls the pid settings by:
    opening and editing the 'Remote_Control.json' file

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
    