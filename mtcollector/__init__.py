#!/usr/bin/env python

"""
|   Multi thread connector and output collector for network devices.    |
|   Developed by L. Repetto @2023 under GPL license v3.0                |
|   https://github.com/LeanRepe/conn_handler                                                                  |
|   Based on Netmiko by K. Byers @ https://github.com/ktbyers/netmiko   |
"""

from mtcollector import MultiThreadConnector

def MTCollector(devices, 
                shows, 
                loglevel: str = 'error', 
                max_threads: int = 12, 
                user: str = '', 
                paswd: str = '', 
                os_type: str = 'cisco_xr', 
                log_filename: str = None
                ) -> MultiThreadConnector:
    """Connect in parallel to multiple devices and returns strucutred outputs

        Args:
            devices (str/dict/list): device(s) to connect to. Supports str for single device and list/dict for multiple devices
                                     list: list of ipaddress
                                     dict: {hostname: ipadress}
            shows (str/list): show commands to execute in each device. Supports str for single show or list for multiple commands
            loglevel (str, optional): sets the logging level. Defaults to 'error'.
            max_threads (int, optional): max number of working threads. Defaults to 12.
            user (str, optional): username to access devices. Defaults to ''.
            paswd (str, optional): password for username. Defaults to ''.
            os_type (str, optional): netmiko device_type. Defaults to 'cisco_xr'.
            log_filename (str, optional): set a file to save logs. Defaults to None.

        Returns:
            dict: dict of devices and outputs = {device1: [{cmd1: ouput1}, {cmd2: output2}]}
    """
    output_collected = MultiThreadConnector.output_collector(devices, 
                                                            shows, 
                                                            loglevel, 
                                                            max_threads, 
                                                            user,
                                                            paswd,
                                                            os_type,
                                                            log_filename)
    
    return output_collected
