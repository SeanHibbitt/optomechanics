"""
Created July 2024

@author: Hagen Thompson 

The code to save each measurement to an Excel file and the 
plotting function is credited to: 
    Sean Hibbit. (See RoomTemp.py)

"""
#%%

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QLabel, QHBoxLayout, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QAction, QMenuBar, QSlider, QMessageBox, QInputDialog, QFormLayout
)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import datetime
import sys
import json
import threading
import time
import datetime
import numpy as np
import pandas as pd

from optomechanics.device_control.KeithleyDMM6500 import DMM6500
# from optomechanics.device_control.SPD3303XE import SPD  # disabled: power supply control
from optomechanics.data_management.data_logger import dated_logger
from simple_pid import PID

from PyQt5.QtWidgets import (
    QFormLayout, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QInputDialog, QMenuBar, 
    QAction, QWidget, QMainWindow, QSlider
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush, QLinearGradient, QPainter
import json
import threading

import traceback
import pyvisa


#%%

# Thermometer definitions
T_0 = 0
R_0 = 1000   # y-intercept
alpha = 3.85 # ohms/K (ohms/C)

def temperature(res):
    """
    Converts resistance measurement to temperature.

    Args:
        res (float): Resistance value to convert.

    Returns:
        float: Temperature calculated from the resistance.
    """
    res = float(res)
    T = (res - R_0) / alpha
    return T

def Control_PID(pid_settings):
    """
    Controls the pid settings by:
    opening and editing the 'Remote_Control.json' file

    """
    try:
        with open('remote_control.json', 'w') as f:
            all_settings = json.load(f)
            all_settings['Remote_Control']
            for key, item in pid_settings.items():
                all_settings['Remote_Control'][key] = item
                
            all_settings['Remote_Control']["update"] = True
            print(f"updated PID settings: {pid_settings.items()}")

        with open('remote_control.json', "w") as f:
            json.dump(all_settings, f)
            

    except FileNotFoundError:
        print("PID settings file not found.")
    except KeyError as e:
        print(f"Missing key in PID settings file: {e}. Please add:\n {e} entry")
        
    except Exception as e:
        print("unknown exception 1")
        if hasattr(e, 'message'):
            print(e.message)
            print(traceback.format_exc())
        else:
            print(e)
            print(traceback.format_exc())

             

#%%




class Worker(QObject):
    """
    A worker class that handles background tasks including PID control,
    data collection, and interaction with hardware devices.
    """
    finished = pyqtSignal()
    plot_data_updated = pyqtSignal(list)
    temperature_updated = pyqtSignal(float)
    setpoint_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.data = []
        self.running = True

        self.load_pid_settings()

    def load_pid_settings(self):
        """
        Loads PID settings from a JSON file. If the file does not exist or has missing keys,
        default settings are used.
        """
        try:    
            with open('pid_settings.json', 'r') as f:
                settings = json.load(f)
                pid_settings = {
                    "Kp": settings['Kp'],
                    "Ki": settings['Ki'],
                    "Kd": settings['Kd'],
                    "setpoint": settings['setpoint'],
                    "sample_time": settings.get('sample_time', 1),
                    "output_limits": settings.get('output_limits', (0, 32)),
                    "proportional_on_measurement": settings.get('proportional_on_measurement', False)
                }
                self.pid = PID(**pid_settings)
                print(f"Loaded PID settings: {pid_settings}")
        except FileNotFoundError as e:
            self.pid = PID(Kp=0, Ki=0.0, Kd=0.0, setpoint=20.0, sample_time=1, output_limits=(0, 32),
                           proportional_on_measurement=False)
            print("PID settings file not found. Using default settings.")
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())
        except KeyError as e:
            print(f"Missing key in PID settings file: {e}. Using default settings.")
            self.pid = PID(Kp=0, Ki=0, Kd=0, setpoint=20.0, sample_time=1, output_limits=(0, 32),
                           proportional_on_measurement=False)
            
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())
        except Exception as e:
            print("unknown exception 2")
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())
            
    def check_remote_update(self):
        """
        Checks the 'pid_settings.json' file for "Remote_Control", if "change" == True, 
        then it will update the pid with the current settigns.
https://www.google.com/search?sca_esv=c0b955b0d7f1ad2c&sxsrf=ADLYWIJY9jEEVpSxiZp_PCS4ZH315lNafA:1722850871741&q=machine+learning+projects+code+github&udm=2&fbs=AEQNm0Aa4sjWe7Rqy32pFwRj0UkWfbQph1uib-VfD_izZO2Y5sC3UdQE5x8XNnxUO1qJLaQR2rwhLa89xym2ORbEZb-gGo_IXijutx5oSlX2RQV8K1vx6nXRwukUebeFcBSjz3fmwlpEfhMBTLkuLWBBRKzfj6k0EqvXoIlGs_7u0Ym_SCKuyAy60BMntWdrdrHT9XlwMGV2&sa=X&ved=2ahUKEwj_79fRx92HAxXUXEEAHRSpD7YQtKgLegQIEBAB
        """
        try:
            with open('remote_control.json', 'r') as f:
                try:
                    all_settings = json.load(f)
                    remote_control_settings = all_settings['Remote_Control']
                    if remote_control_settings['update'] == True:
                        self.pid.Kp = remote_control_settings['Kp']
                        self.pid.Ki = remote_control_settings['Ki']
                        self.pid.Kd = remote_control_settings['Kd']
                        self.pid.setpoint = remote_control_settings['setpoint']
                        self.pid.sample_time = remote_control_settings['sample_time']
    
                        print(f"Loaded PID settings: {remote_control_settings.items()}")
                
                except json.JSONDecodeError as e:
                    print("json decoding error")
                    if hasattr(e, 'message'):
                        print(e.message)
                        print(traceback.format_exc())
                    else:
                        print(e)
                        print(traceback.format_exc())
 
    
            with open('remote_control.json', "w") as f:

                remote_control_settings = {}
                remote_control_settings['Remote_Control'] = {}
                
                remote_control_settings['Remote_Control']["Kp"] = float(self.pid.Kp)
                remote_control_settings['Remote_Control']["Ki"] = float(self.pid.Ki)
                remote_control_settings['Remote_Control']["Kd"] = float(self.pid.Kd)
                remote_control_settings['Remote_Control']["setpoint"] = float(self.pid.setpoint)
                remote_control_settings['Remote_Control']["sample_time"] =  self.pid.sample_time
                remote_control_settings['Remote_Control']["output_limits"] = self.pid.output_limits
                remote_control_settings['Remote_Control']["proportional_on_measurement"] = self.pid.proportional_on_measurement
                remote_control_settings['Remote_Control']["temp"] = float(self.temp)
                remote_control_settings["Remote_Control"]["update"] = False
       
                #save files back to empty json
                json.dump(remote_control_settings, f)
            
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
            print("un-handled exception 3 ")
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())


        




    def save_pid_settings(self, name):
        """
        Saves the current PID settings to a JSON file with a given name.

        Args:
            name (str): The name under which the settings are saved.
        """
        try:
            settings = {
                "Kp": float(self.pid.Kp),
                "Ki": float(self.pid.Ki),
                "Kd": float(self.pid.Kd),
                "setpoint": float(self.pid.setpoint),
                "sample_time": self.pid.sample_time,
                "output_limits": self.pid.output_limits,
                "proportional_on_measurement": self.pid.proportional_on_measurement
            }
            try:
                with open('pid_settings.json', 'r') as f:
                    all_settings = json.load(f)
            except FileNotFoundError:
                all_settings = {}
                
            
    
            all_settings[name] = settings
    
            with open('pid_settings.json', 'w') as f:
                json.dump(all_settings, f)
                print(f"PID settings '{name}' saved.")
                
        except Exception as e:
            print("unknown exception 4.1")
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())

    def run(self):
        print("Starting program:")
        print(f"Connected devices:\n~{DMM6500.connected_devices()}")
        
        while self.running:
            try:
                instrument_address = 'GPIB0::12::INSTR'
                rm = pyvisa.ResourceManager()
                instrument = rm.open_resource(instrument_address)
                trigger_command_MC = 'KRDG?4'
                trigger_command_T1 = 'KRDG?3'
                
                
    
                try:
                

                    current_day = datetime.datetime.now().day
                    base_path = r"D:\\Experiment Data"
                    file_name = "Temp_data.csv"
                    headers = ["Time[s]", "Temperature_1K[K]", "Temperature_MC[K]", "null"]
                    temp_logger = dated_logger(base_path=base_path, file_name=file_name, headings=headers)
                    dataframe = temp_logger.data
                    if isinstance(dataframe, pd.DataFrame):
                        self.data = dataframe.values.tolist()
                    
                    while self.running:
                        
                        current_time = time.time()
                        if current_day != datetime.datetime.now().day:
                            self.data = []
                            current_day = datetime.datetime.now().day
                            
                             
                        self.TMC_value=float(instrument.query(trigger_command_MC))
                        self.T1K_value=float(instrument.query(trigger_command_T1))


                        self.temperature_updated.emit(self.TMC_value )
                        
                        

                        
                        self.data.append([current_time, self.T1K_value , self.TMC_value, 0])
                        temp_logger([current_time, self.T1K_value , self.TMC_value, 0])

                         
                        
                        self.plot_data_updated.emit(self.data)
                        # self.check_remote_update()  # disabled: do not write to remote_control.json
                        time.sleep(0.5)

                except KeyboardInterrupt as e:
                    print("Program ended by user \nshowing plot")
                    if hasattr(e, 'message'):
                        print(e.message)
                        print(traceback.format_exc())
                    else:
                        print(e)
                        print(traceback.format_exc())

                finally:
                    
                    self.running = False
                    # Save lastused settings upon program end
                    self.finished.emit()
                    #plt.show()
                    
                
            except Exception as e:
                print("unknown exception 4")
                print(f"\n\n-------------------\nself.data = {self.data}\n-------------------\n")
                if hasattr(e, 'message'):
                    print(e.message)
                    print(traceback.format_exc())
                else:
                    print(e)
                    print(traceback.format_exc())


                    
#%%

def date_formatter(val, pos):
    return None#datetime.datetime.fromtimestamp(val).strftime('%H:%M:%S')

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=20, height=10, dpi=100):
        try:
            fig, (self.ax1, self.ax2) = plt.subplots(2, figsize=(20, 10))
            super(MplCanvas, self).__init__(fig)
            self.setParent(parent)
            self.ax1.set_ylabel('Temperature [C]')
            self.ax1.set_xlabel('Time')
            self.ax2.set(ylabel='Voltage [V]', xlabel='Time')
            self.line1, = self.ax1.plot([], [], 'x-',  color='r', alpha=0.8, label='Temperature (Sample Plate) [C]')
            self.line21, = self.ax2.plot([], [], 'o-', color='r', alpha=0.8, label='Set Voltage [V]')
            self.line22, = self.ax2.plot([], [], 'x-', color='blue', alpha=0.4, label='Measured Voltage [V]')
            self.ax1.legend()
            self.ax2.legend()
    
            # Set the date format for the x-axis
            self.ax1.xaxis.set_major_formatter(plt.FuncFormatter(date_formatter))
            self.ax2.xaxis.set_major_formatter(plt.FuncFormatter(date_formatter))
        except Exception as e:
            print("unknown exception 4.1")
            if hasattr(e, 'message'):
                print(e.message)
                print(traceback.format_exc())
            else:
                print(e)
                print(traceback.format_exc())



    def update_plot(self, data, last_n_hours=None):
        """
       Updates the plot with new data.

       Args:
           data (list): The data to plot.
           last_n_hours (int, optional): Filter data to show only the last N hours.
       """
        if len(data) == 0:
            return

        plotable_data = np.array(data).T

        if last_n_hours:
            current_time = datetime.datetime.now().timestamp() 
            selected_time = current_time - last_n_hours * 3600
            data = [d for d in data if d[0] >= selected_time]
            plotable_data = np.array(data).T
            
        time_data = plotable_data[0]  # Time data as timestamps
        temp_data = plotable_data[1]  # Tempeprature data 
        set_v_data = plotable_data[2] # Voltage data
        mea_v_data = plotable_data[3] #Voltage data

        self.line1.set_data(time_data, temp_data)
        self.line21.set_data(time_data, set_v_data)
        self.line22.set_data(time_data, mea_v_data)

        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        self.draw()

    def update_temperature_label(self, temp):
        
        self.line1.set_label(f'Temperature (Sample Plate) [{temp:.2f} C]')
        self.ax1.legend()
        self.draw()
        
#%%

class StepTemperatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step Temperature Settings")

        layout = QVBoxLayout(self)

        self.iterations_input = QLineEdit(self)
        self.iterations_input.setPlaceholderText("Number of Iterations")
        layout.addWidget(self.iterations_input)

        self.interval_input = QLineEdit(self)
        self.interval_input.setPlaceholderText("Time Interval (seconds)")
        layout.addWidget(self.interval_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_values(self):
        """
        Retrieves the values from the dialog inputs.

        Returns:
            tuple: A tuple containing the number of iterations and time interval.
        """
        iterations = self.iterations_input.text()
        interval = self.interval_input.text()
        return iterations, interval

#%%

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Temperature Control System") # Set the window title
        self.setGeometry(100, 100, 1200, 800) # Set the window size and position

        central_widget = QWidget() # Create a central widget to hold the main layout
        self.setCentralWidget(central_widget)

        # Create main layout for central widget
        main_layout = QHBoxLayout(central_widget)

        # Left layout for temperature info and settings
        self.left_layout = QVBoxLayout()
        self.left_layout_widget = QWidget()  # Widget to hold the left layout
        self.left_layout_widget.setLayout(self.left_layout) # Set the left layout to the widget
        main_layout.addWidget(self.left_layout_widget) # Add the widget to the main layout

        # Label to display the current temperature
        self.temperature_label = QLabel("Temperature: N/A") 
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.temperature_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.left_layout.addWidget(self.temperature_label) # Add label to the left layout

        # Label to display the setpoint temperature
        self.setpoint_label = QLabel("Set Temperature: N/A")
        self.setpoint_label.setAlignment(Qt.AlignCenter)
        self.setpoint_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.left_layout.addWidget(self.setpoint_label) # Add label to the left layout

        # Create a group box for Step Size and control buttons
        step_size_group_box = QGroupBox("Step Size Control")
        step_size_layout = QVBoxLayout()

        # Step size input
        self.step_size_input = QLineEdit(self)
        self.step_size_input.setPlaceholderText("Step Size (°C)")
        step_size_layout.addWidget(self.step_size_input)

        # Step Up and Step Down buttons
        button_layout = QHBoxLayout()
        self.step_up_button = QPushButton("Step Up", self)
        self.step_down_button = QPushButton("Step Down", self)
        button_layout.addWidget(self.step_up_button) # Add Step Up button
        button_layout.addWidget(self.step_down_button) # Add Step Down button

        step_size_layout.addLayout(button_layout) # Add button layout to step size layout
        step_size_group_box.setLayout(step_size_layout) # Set the layout to the group box
        self.left_layout.addWidget(step_size_group_box) # Add group box to the left layout

        # Create a group box for PID settings
        pid_group_box = QGroupBox("PID Controller Settings")
        form_layout = QFormLayout()

        # PID inputs
        self.kp_input = QLineEdit(self)
        self.kp_input.setPlaceholderText("Kp")
        form_layout.addRow("Kp:", self.kp_input)

        self.ki_input = QLineEdit(self)
        self.ki_input.setPlaceholderText("Ki")
        form_layout.addRow("Ki:", self.ki_input)

        self.kd_input = QLineEdit(self)
        self.kd_input.setPlaceholderText("Kd")
        form_layout.addRow("Kd:", self.kd_input)

        # Temperature Setpoint and Sample Time settings
        self.setpoint_input = QLineEdit(self)
        self.setpoint_input.setPlaceholderText("Setpoint (°C)")
        form_layout.addRow("Setpoint (°C):", self.setpoint_input)

        self.sample_time_input = QLineEdit(self)
        self.sample_time_input.setPlaceholderText("Sample Time (s)")
        form_layout.addRow("Sample Time (s):", self.sample_time_input)

        pid_group_box.setLayout(form_layout) # Set the form layout to the group box
        self.left_layout.addWidget(pid_group_box) # Add group box to the left layout

        # Add buttons for saving, loading, initializing, and removing PID settings
        self.load_pid_settings_button = QPushButton("Load PID Settings", self)
        self.save_pid_settings_button = QPushButton("Save PID Settings", self)
        self.initialize_settings_button = QPushButton("Initialize Settings", self)
        self.remove_pid_settings_button = QPushButton("Remove PID Settings", self)
        self.left_layout.addWidget(self.load_pid_settings_button) # Add button to the left layout
        self.left_layout.addWidget(self.save_pid_settings_button) # Add button to the left layout
        self.left_layout.addWidget(self.initialize_settings_button) # Add button to the left layout
        self.left_layout.addWidget(self.remove_pid_settings_button) # Add button to the left layout

        # Connect button actions to their respective slots
        self.step_up_button.clicked.connect(self.step_up_dialog)
        self.step_down_button.clicked.connect(self.step_down_dialog)
        self.load_pid_settings_button.clicked.connect(self.load_settings)
        self.save_pid_settings_button.clicked.connect(self.save_settings)
        self.initialize_settings_button.clicked.connect(self.initialize_settings)
        self.remove_pid_settings_button.clicked.connect(self.remove_settings)

        # Disabled: prevent any changes to temperature controller settings
        self.step_up_button.setEnabled(False)
        self.step_down_button.setEnabled(False)
        self.load_pid_settings_button.setEnabled(False)
        self.save_pid_settings_button.setEnabled(False)
        self.initialize_settings_button.setEnabled(False)
        self.remove_pid_settings_button.setEnabled(False)

        # Toggle button to expand/minimize left layout
        self.expand_button = QPushButton("Expand/Minimize", self)
        main_layout.addWidget(self.expand_button) # Add button to the main layout   
        self.expand_button.clicked.connect(self.toggle_expand) # Connect button click to toggle function

        # Create a vertical layout for the right side, including the slider and canvas
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()  # Widget to hold the right layout
        self.right_layout_widget.setLayout(self.right_layout) # Set the right layout to the widget
        main_layout.addWidget(self.right_layout_widget) # Add the widget to the main layout

        # Create a canvas for plotting and add a toolbar
        self.canvas = MplCanvas(self, width=20, height=10, dpi=100) 
        toolbar = NavigationToolbar(self.canvas, self)

        self.right_layout.addWidget(toolbar) # Add toolbar to the right layout
        self.right_layout.addWidget(self.canvas) # Add canvas to the right layout

        # Create a slider for selecting the number of hours to display
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(1, 24)  # Set range from 1 to 24 hours
        self.slider.setValue(1) # Default value
        self.slider.setTickPosition(QSlider.TicksBelow) # Set tick position
        self.slider.setTickInterval(1) # Set tick interval
        self.right_layout.addWidget(self.slider) # Add slider to the right layout

        # Label to display the selected number of hours
        self.slider_label = QLabel("Show Last N Hours: 1", self)
        self.slider_label.setAlignment(Qt.AlignCenter)
        self.slider_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.right_layout.addWidget(self.slider_label) # Add label to the right layout

        # Connect slider value changes to update functions
        self.slider.valueChanged.connect(self.update_slider_label)
        self.slider.valueChanged.connect(self.update_plot_with_slider)

        # Initialize worker and start worker thread
        self.worker = Worker()
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker_thread.start()

        # Connect worker signals to update the GUI
        self.worker.plot_data_updated.connect(self.update_plot)
        self.worker.temperature_updated.connect(self.update_temperature_label)
        self.worker.setpoint_updated.connect(self.update_setpoint_label)

        # Setup the menu bar for file operations
        self.setup_menubar()
        self.show() # Show the main window
        
#%%

    def toggle_expand(self):
        """
        Toggles the visibility of the left layout.
        """
        if self.left_layout_widget.isHidden():
            self.left_layout_widget.show()
            self.expand_button.setText("Minimize")
        else:
            self.left_layout_widget.hide()
            self.expand_button.setText("Expand")

    def setup_menubar(self):
        """
        Sets up the menu bar with file operations like saving, loading settings, and exiting the application.
        """
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save Settings", self)
        save_action.triggered.connect(self.save_settings)
        file_menu.addAction(save_action)

        load_action = QAction("Load Settings", self)
        load_action.triggered.connect(self.load_settings)
        file_menu.addAction(load_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def save_settings(self):
        """
        Opens a dialog to save the current PID settings under a specified name.
        """
        name, ok = QInputDialog.getText(self, "Save Settings", "Enter name for settings:")
        if ok and name:
            # Update worker PID settings from GUI input fields
            self.worker.pid.Kp = float(self.kp_input.text())
            self.worker.pid.Ki = float(self.ki_input.text())
            self.worker.pid.Kd = float(self.kd_input.text())
            self.worker.pid.setpoint = float(self.setpoint_input.text())
            self.worker.pid.sample_time = float(self.sample_time_input.text())
            
            print(f"settings changed:\nKp:{self.worker.pid.Kp}\nKi:{self.worker.pid.Ki}\nKp{self.worker.pid.Kd}\nsetpoint:{self.worker.pid.setpoint}\nsample time:{self.worker.pid.sample_time}")

            # Save settings
            self.worker.save_pid_settings(name)

    def load_settings(self):
        """
    
        Opens a dialog to select and load PID settings from a saved file.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Settings")

        layout = QVBoxLayout(dialog)
        settings_list = QListWidget(dialog)
        layout.addWidget(settings_list)

        with open('pid_settings.json', 'r') as f:
            all_settings = json.load(f)
            for name in all_settings.keys():
                settings_list.addItem(QListWidgetItem(name))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(lambda: self.load_selected_setting(settings_list, dialog))
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()

    def load_selected_setting(self, settings_list, dialog):
        """
        Loads the PID settings by name and updates the GUI and worker.
        """
        selected_item = settings_list.currentItem()
        if selected_item:
            name = selected_item.text()
            with open('pid_settings.json', 'r') as f:
                all_settings = json.load(f)
                settings = all_settings[name]
                self.worker.pid.Kp = settings['Kp']
                self.worker.pid.Ki = settings['Ki']
                self.worker.pid.Kd = settings['Kd']
                self.worker.pid.setpoint = settings['setpoint']
                self.worker.pid.sample_time = settings['sample_time']
                
                print(f"settings changed:\nKp:{self.worker.pid.Kp}\nKi:{self.worker.pid.Ki}\nKp{self.worker.pid.Kd}\nsetpoint:{self.worker.pid.setpoint}\nsample time:{self.worker.pid.sample_time}")

                # Update GUI input fields
                self.kp_input.setText(str(self.worker.pid.Kp)) #
                self.ki_input.setText(str(self.worker.pid.Ki))
                self.kd_input.setText(str(self.worker.pid.Kd))
                self.setpoint_input.setText(str(self.worker.pid.setpoint))
                self.sample_time_input.setText(str(self.worker.pid.sample_time))

                print(f"Loaded PID settings '{name}'")
        dialog.accept()

    def remove_settings(self):
        """
        Removes the selected PID settings.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Remove Settings")

        layout = QVBoxLayout(dialog)
        settings_list = QListWidget(dialog)
        layout.addWidget(settings_list)

        with open('pid_settings.json', 'r') as f:
            all_settings = json.load(f)
            for name in all_settings.keys():
                settings_list.addItem(QListWidgetItem(name))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        layout.addWidget(button_box)

        button_box.accepted.connect(lambda: self.remove_selected_setting(settings_list, dialog))
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()

    def remove_selected_setting(self, settings_list, dialog):
        selected_item = settings_list.currentItem()
        if selected_item:
            name = selected_item.text()
            with open('pid_settings.json', 'r') as f:
                all_settings = json.load(f)
                del all_settings[name]

            with open('pid_settings.json', 'w') as f:
                json.dump(all_settings, f, indent=4)

            print(f"Removed PID settings '{name}'")
        dialog.accept()

    def initialize_settings(self):
        # Initialize settings based on current user input
        try:
            self.worker.pid.Kp = float(self.kp_input.text())
            self.worker.pid.Ki = float(self.ki_input.text())
            self.worker.pid.Kd = float(self.kd_input.text())
            self.worker.pid.setpoint = float(self.setpoint_input.text())
            self.worker.pid.sample_time = float(self.sample_time_input.text())
            
            print(f"settings changed:\nKp:{self.worker.pid.Kp}\nKi:{self.worker.pid.Ki}\nKp{self.worker.pid.Kd}\nsetpoint:{self.worker.pid.setpoint}\nsample time:{self.worker.pid.sample_time}")

            # Update the GUI to reflect changes
            #change: hashtaged out below line as it was causing an error and can't understand what its supposed to do
            #self.temperature_label.setText(f"Temperature: {self.worker.get_current_temperature()}")
            self.setpoint_label.setText(f"Set Temperature: {self.worker.pid.setpoint}")

            print("Settings initialized based on user input.")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers in all fields.")


    def step_up_dialog(self):
        """
        Opens a dialog for setting the step size to increase temperature.
        """
        dialog = StepTemperatureDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            iterations, interval = dialog.get_values()
            self.step_up(iterations=int(iterations), interval=float(interval))

    def step_down_dialog(self):
        """
        Opens a dialog for setting the step size to decrease temperature.
        """
        dialog = StepTemperatureDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            iterations, interval = dialog.get_values()
            self.step_down(iterations=int(iterations), interval=float(interval))

    def step_up(self, iterations=1, interval=1.0):
        step_size = self.get_step_size()
        if step_size is not None:
            for _ in range(iterations):
                self.worker.pid.setpoint += step_size
                self.worker.setpoint_updated.emit(self.worker.pid.setpoint)  # Emit signal to update GUI
                time.sleep(interval)
                QApplication.processEvents()  # Process events to update GUI immediately

    def step_down(self, iterations=1, interval=1.0):
        step_size = self.get_step_size()
        if step_size is not None:
            for _ in range(iterations):
                self.worker.pid.setpoint -= step_size
                self.worker.setpoint_updated.emit(self.worker.pid.setpoint)  # Emit signal to update GUI
                time.sleep(interval)
                QApplication.processEvents()  # Process events to update GUI immediately

    def get_step_size(self):
        try:
            return float(self.step_size_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid step size.")
            return None

    def update_plot(self, data):
        """
        Updates the plot with new data.

        Args:
            plot_data (list): Data to plot.
        """
        last_n_hours = self.slider.value()
        self.canvas.update_plot(data, last_n_hours=last_n_hours)

    def update_temperature_label(self, temp):
        """
        Updates the temperature display label with the current temperature value.

        Args:
            temperature (float): The current temperature to display.
        """
        self.temperature_label.setText(f"Temperature: {temp:.4f} °C")
        #self.canvas.update_temperature_label(temp) #sets the label of the graph

    def update_setpoint_label(self, setpoint):
        """
        Updates the setpoint temperature display label.

        Args:
            setpoint (float): The setpoint temperature to display.
        """
        self.setpoint_label.setText(f"Set Temperature: {setpoint:.4f} °C")

    def update_slider_label(self, value):
        """
        Updates the label that shows the number of hours selected by the slider.

        Args:
            value (int): The current value of the slider.
        """
        self.slider_label.setText(f"Show Last N Hours: {value}")

    def update_plot_with_slider(self):
        """
        Updates the plot based on the slider value to show data for the selected number of hours.
        """
    
        self.update_plot(self.worker.data)

    def closeEvent(self, event):
        self.worker.running = False
        self.worker_thread.join()
        event.accept()
        
#%%

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())