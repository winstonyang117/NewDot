import socket as s
import time
#import urllib3
import sys, os
#sys.path.insert(0, os.path.abspath('..'))
import subprocess
# import random
# import numpy as np
import datetime
#!pip3 install pyserial
import serial
import serial.tools.list_ports
import netifaces
import threading
import struct

def mac_address():
   macEth = "unit.name"
   data = netifaces.interfaces()
   for i in data:
      if i == 'wlan0': #'en0': # 'eth0':
         interface = netifaces.ifaddresses(i)
         info = interface[netifaces.AF_LINK]
         if info:
            macEth = interface[netifaces.AF_LINK][0]["addr"]
   return macEth
   
def calc_crc(data):
   #data = bytearray.fromhex(string)
   crc = 0xFFFF
   for pos in range(0, len(data)):
      crc ^= data[pos]
      for i in range(8):
         if ((crc & 1) != 0):
            crc >>= 1
            crc ^= 0xA001
         else:
            crc >>= 1
   return (((crc & 0xff) << 8) + (crc >> 8))
    

def parse(data):
    length = len(data)
#    print(" ".join(hex(n) for n in data))  

    data1 = []
    value = -0
    index = 0

    if length >= 5:
        for i in range(0, length - 4, 1):
            if data[i] == 0xaa and data[i+4] ==hex_xor(data[i:i+4]):
                index = i;
                break;

        for i in range(index, length-4, 5):
            #print('i is :' + str(i))
            if data[i] == 0xaa and data[i+4] == hex_xor(data[i:i+4]):
                value = (data[i+1] << 16 | data[i+2] << 8 | data[i+3])&0x00ffffff
                if value >= 0x800000:
                    tmp = bin(value).replace("0b1","0b0")
                    value = int(tmp, 2)-pow(2, len(tmp)-3)
                data1.append(-value)


    if index > 0:
        del data[0 : index]

   
   #print(" ".join(hex(n) for n in data1) 
   # this line below shall be modified based on your actual data structure
   # each element in result shalll be one sensor reading
   # result = data1 
   # size = len(result)
    return data1

# This function write an array of data to influxdb. It assumes the sample interval is 1/fs.
# influx - the InfluxDB info including ip, db, user, pass. Example influx = {'ip': 'https://sensorweb.us', 'db': 'algtest', 'user':'test', 'passw':'sensorweb'}
# dataname - the dataname such as temperature, heartrate, etc
# timestamp - the epoch time (in second) of the first element in the data array, such as datetime.now().timestamp()
# fs - the sampling frequency of readings in data
# unit - the unit location name tag
def write_influx(influx, unit, table_name, data_name, data, start_timestamp, fs):
    # print("epoch time:", timestamp) 
    timestamp = start_timestamp
    max_size = 100
    count = 0
    total = len(data)
    prefix_post  = "curl -s -POST \'"+ influx['ip']+":8086/write?db="+influx['db']+"\' -u "+ influx['user']+":"+ influx['passw']+" --data-binary \' "
    http_post = prefix_post
    for value in data:
        count += 1
        http_post += "\n" + table_name +",location=" + unit + " "
        http_post += data_name + "=" + str(value) + " " + str(int(timestamp*10e8))
        timestamp +=  1/fs
        if(count >= max_size):
            http_post += "\'  &"
            # print(http_post)
            print("Write to influx: ", table_name, data_name, count)
            subprocess.call(http_post, shell=True)
            total = total - count
            count = 0
            http_post = prefix_post
    if count != 0:
        http_post += "\'  &"
        # print(http_post)
        print("Write to influx: ", table_name, data_name, count) #, data)
        subprocess.call(http_post, shell=True)

def hex_xor(data):
    tmp = 0
    for i in range (0, len(data)):
        tmp = tmp ^ data[i];
    return tmp;



def float_to_hex(f):
    return (struct.unpack('<I', struct.pack('<f',f))[0])

def hex_to_float(h):
    return format((struct.unpack('>f', bytes.fromhex(h))[0]), '.6f')


if __name__ == '__main__':

    if(len(sys.argv) > 1):
        port = sys.argv[1]
    else:
        port = "/dev/ttyS0" # default
        print(f"Usage: python3 {sys.argv[0]} port")
        print(f"\t Examples: \n\t\tpython3 {sys.argv[0]} /dev/ttyUSB0 (read from USB-serial) \n\t\tpython3 {sys.argv[0]} /dev/ttyS0 (for UART-serial) \n\t\tpython3 {sys.argv[0]} none (for simulation mode)\n")
        exit()

    print("Read:", port)
    ser = 0
    if port != "none":
        ser = serial.Serial(port, baudrate=256000, timeout=5)
        has_serial = True
        macEth = mac_address()
    else:
        has_serial = False
        macEth = mac_address()
    fs = 100
    print("My ethernet MAC is: ", macEth)
    print(f'open browser with user/password:guest/sensorweb_guest to see waveform at grafana: \n\thttps://www.sensorweb.us:3000/d/VgfUaF3Gz/bdotv2-plot?orgId=1&var-mac1={macEth}&from=now-1m&to=now&refresh=5s')


    dest = {'ip':'https://sensorweb.us', 'db':'shake', 'user':'test', 'passw':'sensorweb'}


    data = []
    data_tmp = []
    data_send = []
    data_valid = []
    data_buf = []
    num = 0
    flag = 0
    num_add = 0
    num_del = 0

   # some serial ports require a write operation to start sending data out, then uncomment below and replace with a serial write program
#   subprocess.call("/opt/belt/beltWrite.py", shell=True)
    tmp_timestamp = datetime.datetime.now().timestamp()
    start_timestamp = round(tmp_timestamp, 3)
    print(f'start_timestamp: {start_timestamp}, tmp_timestamp: {tmp_timestamp}')
    while(True):
        time.sleep(1)
        if has_serial:
            count = ser.inWaiting()
        else:
            count = fs

        print('inWaiting:', count)
        if count >= 0:
            if has_serial:
                data_tmp = ser.read(count)
                data_buf.extend(data_tmp)
            else:
               data_buf = [10, 20, 30, 20]*int(fs/4) # np.random.randint(10, 200, size=fs)  


        #end_timestamp = datetime.datetime.now().timestamp()
        data = parse(data_buf)

        num = num + len(data)
        
        end_tmp = datetime.datetime.now().timestamp()
        end_timestamp = start_timestamp + len(data)*0.01

        if len(data) > 2:
            if (end_tmp - end_timestamp) > 0.010:
                flag = flag + 1
                if flag >= 3:
                    flag = 0
                    cnt = int((end_tmp - end_timestamp)/0.01)
                    tmp_val = int((data[len(data)-2] + data[len(data)-1])/2)
                    for i in range(0, cnt):
                        data.insert(len(data)-1, tmp_val)
                    print("add a value!!!:", tmp_val, cnt)
                    end_timestamp = end_timestamp + (0.01 * cnt)
                    num_add = num_add + 1

            elif (end_tmp - end_timestamp) < -0.010:
                flag = flag - 1
                if flag <= -3:
                    flag = 0
                    cnt = int((end_timestamp - end_tmp)/0.01)
                    end_timestamp = end_timestamp - (0.01 * cnt)
                    print("delete end_timestamp***")
                    num_del = num_del + 1

            else: 
                flag = 0


        if end_timestamp > start_timestamp:
            fd = (len(data))/(end_timestamp - start_timestamp) 
        else:
            fd = (len(data))/(end_tmp - start_timestamp)

        write_influx(dest, macEth, "Z", "value", data, start_timestamp, fd)

#        print("data: ", data)
        print(f'start: {start_timestamp}, end: {end_timestamp}, size:{len(data)}, fd:{fd}') 
        print(f'end_timestamp: {end_tmp}, end_tmp - end_timestamp: {end_tmp - end_timestamp}') 
        
        print(f'time: {end_timestamp - tmp_timestamp}, num: {num}')
        print(f'num_add: {num_add}, num_del: {num_del}')

        start_timestamp = end_timestamp

        del data_buf[0 : len(data)*5]
        #del data_valid[0 : len(data)]