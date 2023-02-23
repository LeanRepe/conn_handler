#!/usr/bin/env python

"""
|   Multi thread connector and output collector for network devices.    |
|   Developed by L. Repetto @2023 under GPL license v3.0                |
|   https://github.com/LeanRepe/conn_handler                                                                  |
|   Based on Netmiko by K. Byers @ https://github.com/ktbyers/netmiko   |
"""
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoAuthenticationException as authException
from netmiko.exceptions import NetMikoTimeoutException as timeOut
from multiprocessing.dummy import Pool
import logging
import ipaddress
import argparse
import json

__author__ = "Leandro Repetto"
__copyright__ = "Copyright 2023"
__credits__ = ["Leandro Repetto"]
__license__ = "GPL"
__version__ = "3.0"
__maintainer__ = "Leandro Repetto"
__email__ = "lrepetto@gmail.com"
__status__ = "Testing"

class MultiThreadConnector:
    """Main wrapper class for connection and multithreading
    """
    def __init__(self) -> None:
        self.Device = self.Device

    class Device:
        """Device subclass represents a device to connect to
        """
        def __init__(self, 
                    hostname: str = '', 
                    ip: str = '', 
                    os_type: str = 'cisco_xr') -> None:
            """main init for device class

            Args:
                hostname (str, optional): hostname of device. Defaults to ''.
                ip (str, required): ip address of a device. Defaults to ''.
                os_type (str, optional): Netmiko OS valid device_type. Defaults to 'cisco_xr'.
            """
            self.hostname = hostname
            self.ipaddress = ip
            self.os_type = os_type
        
        def get_hostname(self) -> str:
            """get hostname of device, if empty returns ipaddress

            Returns:
                str: hostname or ipaddress
            """
            if self.hostname == '':
                return self.ipaddress
            else:
                return self.hostname
        
        def get_ipaddress(self) -> str:
            """get ip address of device

            Returns:
                str: ip address
            """
            return self.ipaddress

        def get_type(self) -> str:
            """get configured device_type (os)

            Returns:
                str: os type
            """
            return self.os_type

    @classmethod
    def __connect_to(self, 
                    device, 
                    jumpserver: dict = {}
                    ):
        """Handles conection to a single device

        Args:
            device (class object): Device object
            jumpserver (dict, optional): Future support for proxy/jumpserver. Defaults to {}.
        
        Returns:
            if connected:
            netmiko object: a connection to device
            if not connected:
            bool: False
        """
        conn_device = {
            'device_type': device.get_type(),
            'ip': device.get_ipaddress(),
            'username': self.username,  # main class attribute
            'password': self.password   # main class attribute
        }
        try:
            connection_to = ConnectHandler(**conn_device)
            logging.info(f'connected to {device.get_hostname()}')
            return connection_to
        except authException: # max authentication failure supported 2
            logging.error(f'Failed to Authenticate to {device.get_hostname()} first attempt - Retrying')
            try:
                connection_to = ConnectHandler(**conn_device)
                logging.info(f'connected to {device.get_hostname()}')
                return connection_to
            except authException:   # avoid user lockout
                logging.error(f'Credentials failed for device {device.get_hostname()}')
                return False
        except timeOut:
            logging.error(f'Connection to {device.get_hostname()} timed out, is {device.get_ipaddress()} the rigth address?')
            return False
        except Exception as error:
            logging.error(f'An Exception occured - f{error}')
            return False

    @classmethod
    def __get_outputs(self,
                     connection, 
                     timeout: int = 30
                     ):
        """Handles output(s) collection for a single device

        Args:
            connection (netmiko object): established connection to device
            timeout (int, optional): extend cli timeout in case of larger outputs. Defaults to 30.

        Returns:
            list: list of {key: value} pairs for each output to get
        """
        outputs = []
        logging.info(f'Running show commands')
        for show in self.show_list: # main class attribute show_list
            output = connection.send_command(show, read_timeout=timeout) # send show waits for output
            logging.debug(f'Gather information for {show} command')
            logging.debug(f'{output}')
            outputs.append({show: output}) # uses show command as key, show must be unique
        logging.info(f'Finished collecting outputs')
        return outputs

    def __check_ipaddress(ip):
        """Check if value is an ip address

        Args:
            ip (str): input value passed as "device.ipaddress"
        
        Return:
            bool: if ip is not the right format (IPv4/IPv6) return false
        
        """
        try:
            ip_object = ipaddress.ip_address(ip)
            return True
        except ValueError:
            logging.error(f'Value provided is not an IP address - Value: {ip}')
            return False

    @classmethod
    def __wrapper_output(self, device):
        """wrapper function to connect and get output from device

        Args:
            device (class object): Device subclass object
        """
        connected = self.__connect_to(device)
        if connected:
            output = self.__get_outputs(connected)
            self.main_dict[device.get_hostname()] = output # add output(s) to device dict
        else:
            self.non_connected.append(device.get_hostname())
            

    
    @classmethod
    def __pool_connection(self, max_threads, device):
        """Handles multithreading operations

        Args:
            max_threads (int): max amount of working threads
            device (list): list of Device class object
        """
        pool = Pool(max_threads)
        try:
            logging.info('Starting Multithread operations')
            pool.map(self.__wrapper_output, device)
        except UnboundLocalError:
            logging.error('Error mapping threads to routine')

        pool.close()
        pool.join()

        logging.info('Finished Multithread operations')
        return

    @classmethod
    def output_collector(self, 
                        devices, 
                        shows, 
                        loglevel: str = 'error', 
                        max_threads: int = 12, 
                        user: str = '', 
                        paswd: str = '', 
                        os_type: str = 'cisco_xr', 
                        log_filename: str = None
                        ):
        """Connect in parallel to multiple devices and returns estrucutred outputs

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

        Raises:
            TypeError: if device/show VAR are not supported
            ValueError: if device ipaddress not in range

        Returns:
            dict: dict of devices and outputs = {device1: [{cmd1: ouput1}, {cmd2: output2}]}
        """
        self.username = user
        self.password = paswd
        if type(shows) == str:  # check for shows type
            self.show_list.append(shows)
        elif type(shows) == list:
            self.show_list = shows.copy()
        else:
            logging.error('VAR shows out of type, supports str or list')
            logging.debug(f'VAR shows out of type --\Value: {shows}')
            raise TypeError('VAR shows out of type, supports str or list')
        self.main_dict = {}
        self.non_connected = []
        log_level = getattr(logging, loglevel.upper())  # getting attribute based on input
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=log_level, filename=log_filename)
        device_list = []
        if type(devices) == dict:   # expected value for dict {hostname: ipaddress}
            for hostname in devices.keys():
                if self.__check_ipaddress(devices[hostname]): # check if value ipaddress
                    a = self.Device(hostname, devices[hostname], os_type)
                    device_list.append(a)
        elif type(devices) == list: #
            for i in devices:
                if self.__check_ipaddress(i):   # check if value is ipaddress
                    a = self.Device('', i, os_type)
                    device_list.append(a)
        elif type(devices) == str:  # if value not ip, Raise Value error and stop exec
            if self.__check_ipaddress(devices):
                max_threads = 1 # if single device set single working thread
            else:
                raise ValueError('provided value not an ip address')
        else:   # if device type not supported rise TypeError
            logging.error(f'Argument provided not a String, List or Dict --')
            logging.error(f'Argument type: {str(type(devices))}. Content: {devices}')
            raise TypeError('Argument provided not list or Dict')
        logging.info('Starting Pool mapping')
        if max_threads > 1: # if single thread don't use multithread function
            self.__pool_connection(max_threads, device_list)
        else:
            a = self.Device('', devices, os_type)
            self.__wrapper_output(a)
        logging.info('Ended pool mapping')
        if len(self.non_connected) > 0: # if any device in non_connected, append to dict
            self.main_dict['not_connected'] = self.non_connected
        logging.debug(f'Returning data: \n{self.main_dict}')
        return self.main_dict

def file_manager(file, output = None, operation: str = 'read'):
    """manage file read and write

    Args:
        file (str): /path/file to read/write to
        output (dict, optional): output to write to file. Defaults to None.
        operation (str, optional): type of operation to file (read/write). Defaults to 'read'.

    Raises:
        ValueError: if file extension not supported in read operations

    Returns:
        list: return list of lines in read operations 
    """
    if operation == 'read':
        if file.split('.')[1] == 'csv': # Check extension, placeholder for future csv support
            raise ValueError('Type Not supported')
        else:
            with open(file, 'r') as read_file: 
                temp_list = read_file.readlines()
                content = []
                for lines in temp_list: # loop for all lines removing newline
                    content.append(lines.strip('\n'))
                read_file.close()
                return content
    elif operation == 'write':
        with open(file, 'w+') as write_file:
            if file.split('.')[1] == 'json':    # check extension for .json
                write_file.write(json.dump(output, indent=4))
                write_file.close()
            else:   # writes to textfile
                write_file.write(f'Results for output Job:\n\n')
                for device,output in result_collector.items():
                    write_file.write(f'-------------\n{device}\n-------------\n\n')
                    if device == 'Not Connected':
                        for devices in device:
                            write_file.write(f'\t{devices}\n')
                    else:
                        for shows in output:
                            for show in shows.keys():
                                write_file.write(f'\tcmd: {show}\n\t\t{shows[show]}\n\n')
                write_file.close()
            


if __name__ == '__main__':
    """standalone exectution

    Raises:
        AttributeError: If missing key arguments (Device/shows/user & password)
    """

    # accepted arguments
    parser = argparse.ArgumentParser(description='Multi Thread connector, standalone running')
    parser.add_argument('-d', '-device', help='Set device to get outputs from')
    parser.add_argument('-fd', '-filedevice', help='Set intput file for devices. Support TXT')
    parser.add_argument('-s', '-show', help='Set show command to get from device')
    parser.add_argument('-fs', '-fileshow', help='Set input file for shows. Support TXT')
    parser.add_argument('-o', '-output', help='Set output to file. NOTE: takes current working directoy as default')
    parser.add_argument('-up', '-userpass', help='Username:password to login. NOTE: if password contains ":" use -u -p arguments')
    parser.add_argument('-u', '-username', help='Set username to login. Note: prefer metod is -up')
    parser.add_argument('-p', '-password', help='Set password to login. Note: prefer metod is -up')
    parser.add_argument('-os', '-ostype', help='Set OS type for end devices. Default: XR')
    args = parser.parse_args()

    # check arguments values
    if args.d != None: # device (d) or filedevice (fd) must be present
        device = args.d
    elif args.fd != None:
        filedevice = args.fd
        device = file_manager(filedevice)
    else:
        logging.error('Argument Missing: use -d (device) or -fd (filedevice) to set destination device(s)')
        raise AttributeError('Argument Missing: device/filedevice')
    if args.s != None: # show (s) or fileshow (fs) must be present
        show = args.s
    elif args.fs != None:
        fileshow = args.fs
        show = file_manager(fileshow)
    else:
        logging.error('Argument Missing: use -s (show) or -fs (fileshow) to set shows commands to extract from device(s)')
        raise AttributeError('Argument Missing: show/fileshow')
    if args.up != None: # userpass (up) or username (u)/password (p) must be present
        userpass = args.up.split(':')
        username = userpass[0]
        password = userpass[1]
    else:
        if args.u != None and args.p != None:
            username = args['username']
            password = args['password']
        else:
            logging.error(f'Missing Argument username/password')
            raise AttributeError
    if args.o != None:  # if no output file is specified, result will be printed
        output_file = args.o
    else:
        output_file = 'output_print'
    if args.os != None: # set the end device operating system.
        ostype = args.os
    else:
        ostype = 'cisco_xr'
    
    # Runs multithread collection with input arguments
    result_collector = MultiThreadConnector.output_collector(device, show, user=username, paswd=password, os_type=ostype)
    if output_file == 'output_print':   # print output or send to file
        print(f'Results for output Job:\n\n')
        for device,output in result_collector.items():
            print(f'-------------\n{device}\n-------------\n\n')
            if device == 'not_connected':
                for devices in device:
                    print(f'\t{devices}\n')
            else:
                for shows in output:
                    for show in shows.keys():
                        print(f'\tcmd: {show}\n\t\t{shows[show]}\n\n')
    else:
        file_manager(output_file, result_collector, operation='write')
        print(f'Output collector Finished')
    


