# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 19:51:12 2024

@author: RoomTemp
"""

from DeviceClasses.SMA100B import Signal_Generator
import matplotlib.pyplot as plt

with Signal_Generator('TCPIP::169.254.117.114::INSTR') as SG:
    SG.turn_mw("On")
    SG.set_mw_power(10)
    SG.set_mw_frequency(3.68394131e9)
    plt.pause(60*10)