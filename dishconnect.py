#!/usr/bin/env python
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoAuthenticationException as authException
from netmiko.exceptions import NetMikoTimeoutException as timeOut
from multiprocessing.dummy import Pool
import logging
import ipaddress
import argparse
import json
import csv


class MultiThreadConnector:

    def __init__(self) -> None:
        self.Device = self.Device

    class Device:

        def __init__(self, 
                    hostname: str = '', 
                    ip: str = '', 
                    os_type: str = 'cisco_xr'):
            self.hostname = hostname
            self.ipaddress = ip
            self.os_type = os_type
        
        def get_hostname(self):
            if self.hostname == '':
                return self.ipaddress
            else:
                return self.hostname
        
        def get_ipaddress(self):
            return self.ipaddress

        def get_type(self):
            return self.os_type
    
    @classmethod
    def not_connected(self, hostname):
            self.non_connected.append(hostname)

    @classmethod
    def __connect_to(self, 
                    device, 
                    jumpserver: dict = {}
                    ):
        conn_device = {
            'device_type': device.get_type(),
            'ip': device.get_ipaddress(),
            'username': self.username,
            'password': self.password
        }
        try:
            connection_to = ConnectHandler(**conn_device)
            logging.info(f'connected to {device.get_hostname()}')
            return connection_to
        except authException:
            logging.error(f'Failed to Authenticate to {device.get_hostname()} first attempt - Retrying')
            try:
                connection_to = ConnectHandler(**conn_device)
                logging.info(f'connected to {device.get_hostname()}')
                return connection_to
            except authException:
                self.not_connected(device.get_hostname())
                logging.error(f'Credentials failed for device {device.get_hostname()}')
                return False
        except timeOut:
            self.not_connected(device.get_hostname())
            logging.error(f'Connection to {device.get_hostname()} timed out, is {device.get_ipaddress()} the rigth address?')
            return False
        except Exception as error:
            self.not_connected(device.get_hostname())
            logging.error(f'An Exception occured - f{error}')
            return False

    @classmethod
    def __get_outputs(self,
                     connection, 
                     timeout: int = 30
                     ):
        outputs = []
        logging.info(f'Running show commands')
        for show in self.show_list:
            output = connection.send_command(show, read_timeout=timeout)
            logging.debug(f'Gather information for {show} command')
            logging.debug(f'{output}')
            outputs.append({show: output})
        logging.info(f'Finished collecting outputs')
        return outputs

    def check_ipaddress(ip):
        try:
            ip_object = ipaddress.ip_address(ip)
        except ValueError:
            logging.error(f'Value provided is not an IP address - Value: {ip}')

    @classmethod
    def __wrapper_output(self, device):
        device_ip = device.get_ipaddress()
        connected = self.__connect_to(device)
        if connected:
            output = self.__get_outputs(connected)
            self.main_dict[device_ip] = output
            

    
    @classmethod
    def pool_connection(self, max_threads, device):
        pool = Pool(max_threads)
        try:
            logging.debug('Starting with multithread mapping')
            pool.map(self.__wrapper_output, device)
        except UnboundLocalError:
            logging.error('Error mapping threads to routine')

        pool.close()
        pool.join()

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
        self.username = user
        self.password = paswd
        self.show_list = shows
        self.main_dict = {}
        self.non_connected = []
        log_level = getattr(logging, loglevel.upper())
        logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',
                            level=log_level, filename=log_filename)
        device_list = []
        if type(devices) == dict:
            for hostname in devices.keys():
                self.check_ipaddress(devices[hostname])
                a = self.Device(hostname, devices[hostname], os_type)
                device_list.append(a)
        elif type(devices) == list:
            for i in devices:
                self.check_ipaddress(i)
                a = self.Device('', i, os_type)
                device_list.append(a)
        elif type(devices) == str:
            self.check_ipaddress(devices)
            max_threads = 1
        else:
            logging.error(f'Argument provided not a List or Dict --')
            logging.error(f'Argument type: {str(type(devices))}. Content: {devices}')
            raise TypeError('Argument provided not list or Dict')
        logging.info('Starting Pool mapping')
        if max_threads > 1:
            self.pool_connection(max_threads, device_list)
        else:
            a = self.Device('', devices, os_type)
            #print(a)
            self.__wrapper_output(a)
        logging.info('Ended pool mapping')
        if len(self.non_connected) > 0:
            self.main_dict['Not Connected'] = self.non_connected
        logging.debug(f'Returning data: \n{self.main_dict}')
        return self.main_dict

def file_manager(file, output = None, operation: str = 'read'):
    if operation == 'read':
        if file.split('.')[1] == 'csv':
            raise ValueError('Type Not supported')
        else:
            with open(file, 'r') as read_file:
                temp_list = read_file.readlines()
                content = []
                for lines in temp_list:
                    content.append(lines.strip('\n'))
                read_file.close()
                return content
    elif operation == 'write':
        with open(file, 'w+') as write_file:
            if file.split('.')[1] == 'json':
                write_file.write(json.dump(output, indent=4))
                write_file.close()
            else:
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
    parser = argparse.ArgumentParser(description='Multi Thread connector, standalone running')
    parser.add_argument('-d', '-device', help='Set device to get outputs from')
    parser.add_argument('-fd', '-filedevice', help='Set intput file for devices. Support TXT')
    parser.add_argument('-s', '-show', help='Set show command to get from device')
    parser.add_argument('-fs', '-fileshow', help='Set input file for shows. Support TXT')
    parser.add_argument('-o', '-output', help='Set output to file. NOTE: takes current working directoy as default')
    parser.add_argument('-up', '-userpass', help='Username:password to login')
    parser.add_argument('-u', '-username', help='Set username to login. Note: prefer metod is -up')
    parser.add_argument('-p', '-password', help='Set password to login. Note: prefer metod is -up')
    parser.add_argument('-os', '-ostype', help='Set OS type for end devices. Default: XR')
    args = parser.parse_args()

    device = ''
    filedevice = ''
    show_list = []
    fileshow = ''
    ostype = 'xr'
    if args.d != None:
        device = args.d
    elif args.fd != None:
        filedevice = args.fd
        device = file_manager(filedevice)
    else:
        logging.error('Argument Missing: use -d (device) or -fd (filedevice) to set destination device(s)')
        raise AttributeError('Argument Missing: device/filedevice')
    if args.s != None:
        show_list.append(args.s)
    elif args.fs != None:
        fileshow = args.fs
        show = file_manager(fileshow)
    else:
        logging.error('Argument Missing: use -s (show) or -fs (fileshow) to set shows commands to extract from device(s)')
        raise AttributeError('Argument Missing: show/fileshow')
    if args.up != None:
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
    if args.o != None:
        output_file = args.o
    else:
        output_file = 'pprint'
    if args.os != None:
        ostype = args.os
    else:
        ostype = 'cisco_xr'
    
    result_collector = MultiThreadConnector.output_collector(device, show_list, user=username, paswd=password, os_type=ostype)
    if output_file == 'pprint':
        print(f'Results for output Job:\n\n')
        for device,output in result_collector.items():
            print(f'-------------\n{device}\n-------------\n\n')
            if device == 'Not Connected':
                for devices in device:
                    print(f'\t{devices}\n')
            else:
                for shows in output:
                    for show in shows.keys():
                        print(f'\tcmd: {show}\n\t\t{shows[show]}\n\n')
    else:
        file_manager(output_file, result_collector, operation='write')
        print(f'Output collector Finished')
    


