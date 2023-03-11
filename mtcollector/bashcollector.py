#!/usr/bin/env python

import json
import argparse
import sys
from __init__ import MTCollector


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
        try:
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
        except IndexError:
            print('FILE PROVIDED WITH NO EXTENSION')
            sys.exit(1)
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
    """Wrapper for bash execution 

    Raises:
        AttributeError: If missing key arguments (Device/shows/user & password)
    """

    # accepted arguments
    parser = argparse.ArgumentParser(description='Multi Thread connector, standalone running')
    parser.add_argument('-d', '-device', help='Set device to get outputs from')
    parser.add_argument('-f', '-filedevice', help='Set intput file for devices. Support TXT')
    parser.add_argument('-s', '-show', help='Set show command to get from device')
    parser.add_argument('-l', '-listshow', help='Set input file for shows. Support TXT')
    parser.add_argument('-o', '-output', help='Set output to file. NOTE: takes current working directoy as default')
    parser.add_argument('-c', '-combuserpass', help='Username:password to login. NOTE: if password contains ":" use -u -p arguments')
    parser.add_argument('-u', '-username', help='Set username to login. Note: prefer metod is -up')
    parser.add_argument('-p', '-password', help='Set password to login. Note: prefer metod is -up')
    parser.add_argument('-t', '-typeos', help='Set OS type for end devices. Default: XR')
    #parser.add_argument('-loglvl', help='Set the logging level for the script. Default ERROR')
    #parser.add_argument('')
    args = parser.parse_args()
    
    # check arguments values
    if args.d != None: # device (d) or filedevice (fd) must be present
        device = args.d
    elif args.f != None:
        filedevice = args.f
        device = file_manager(filedevice)
    else:
        #logging.error('Argument Missing: use -d (device) or -fd (filedevice) to set destination device(s)')
        raise AttributeError('Argument Missing: device/filedevice')
    if args.s != None: # show (s) or fileshow (fs) must be present
        show = args.s
    elif args.l != None:
        fileshow = args.l
        show = file_manager(fileshow)
    else:
        #logging.error('Argument Missing: use -s (show) or -fs (fileshow) to set shows commands to extract from device(s)')
        raise AttributeError('Argument Missing: show/fileshow')
    if args.c != None: # userpass (up) or username (u)/password (p) must be present
        userpass = args.c.split(':')
        username = userpass[0]
        password = userpass[1]
    else:
        if args.u != None and args.p != None:
            username = args['username']
            password = args['password']
        else:
            #logging.error(f'Missing Argument username/password')
            raise AttributeError
    if args.o != None:  # if no output file is specified, result will be printed
        output_file = args.o
    else:
        output_file = 'output_print'
    if args.t != None: # set the end device operating system.
        ostype = args.t
    else:
        ostype = 'cisco_xr'
    
    # Runs multithread collection with input arguments
    result_collector = MTCollector(device, show, user=username, paswd=password, os_type=ostype)
    if output_file == 'output_print':   # print output or send to file
        print(f'Results for output Job:\n\n')
        for device,output in result_collector.items():
            print(f'-------------\n{device}\n-------------\n')
            if device == 'not_connected':
                for devices in output:
                    print(f'\t{devices}\n')
            else:
                for shows in output:
                    for show in shows.keys():
                        print(f'\tcmd: {show}\n\t\t{shows[show]}\n\n')
    else:
        file_manager(output_file, result_collector, operation='write')
        print(f'Output collector Finished')
    