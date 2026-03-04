# -*- coding: utf-8 -*-
"""
Made by Claude. Attenuation correction utilities for the optomechanics suite.

Provides helpers for compensating measured dB data for known cable or
component attenuation.  Key functions:

- :func:`account_for_attenuation` -- subtract attenuation from dB data
"""

#minus the log

def account_for_attenuation(data, attenuation_data):
    """
    Assumes all data is given in dB
    """
        
    
    