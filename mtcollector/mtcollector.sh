#!/bin/bash

Help()
{
    /Users/lrepetto/Documents/Dish_conn_handler/bin/python /Users/lrepetto/Documents/Dish_conn_handler/mtcollector/bashcollector.py -h
}
while getopts d:f:s:l:c:u:p:o:t::h option;
do
    case "${option}" in
        d) device=${OPTARG};;
        f) filedevice=${OPTARG};;
        s) show=${OPTARG};;
        l) listshow=${OPTARG};;
        c) userpass=${OPTARG};;
        u) username=${OPTARG};;
        p) password=${OPTARG};;
        o) output=${OPTARG};;
        t) typeos=${OPTARG};;
        h) Help;;
    esac
done

# check if flag is not empty and add to list
flags=""
if [ "$device" != "" ]; then
    flags+="-d $device "
fi
if [ "$filedevice" != "" ]; then
    flags+="-f $filedevice "
fi
if [ "$show" != "" ]; then
    flags+="-s $show "
fi 
if [ "$listshow" != "" ]; then
    flags+="-l $listshow "
fi
if [ "$userpass" != "" ]; then
    flags+="-c $userpass "
fi
if [ "$username" != "" ]; then
    flags+="-u $username "
fi
if [ "$password" != "" ]; then
    flags+="-p $password "
fi
if [ "$output" != "" ]; then
    flags+="-o $output "
fi
if [ "$typeos" != "" ]; then
    flags+="-t $typeos "
fi

#/home/lrepetto/conn_hanlder/bin/python /home/lrepetto/conn_hanlder/mtcollector/bashcollector.py $flags
if [ "$flags" != "" ]; then
    /Users/lrepetto/Documents/Dish_conn_handler/bin/python /Users/lrepetto/Documents/Dish_conn_handler/mtcollector/bashcollector.py $flags
fi