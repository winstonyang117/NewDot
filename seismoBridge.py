import socket as s
import time
import sys, os
import subprocess
import datetime
import serial
import serial.tools.list_ports
import netifaces

def mac_address():
   macEth = "unit.name"
   data = netifaces.interfaces()
   for i in data:
      if i == 'eth0': #'en0': # 'eth0':
         interface = netifaces.ifaddresses(i)
         info = interface[netifaces.AF_LINK]
         if info:
            macEth = interface[netifaces.AF_LINK][0]["addr"]
   return macEth

def parse(data, fs):
   length = len(data)
   try:
       result = list(map(lambda x: int(x) - 2**23 ,data.decode('utf-8').split('\r\n')[:-1]))
       return result
   except:
       try:
           result = [ int(x.decode('utf-8').split('\r\n')[:-1][0])-2**23 for x in data]
         #   print(result)
           return result
       except:
           result = [0]
         #   print("barf")
         #   print(data)  
           return result

def write_influx(influx, unit, table_name, data_name, data, start_timestamp, fs):
    """
    This function writes an array of data to influxdb. It assumes the samp
    interval is 1/fs.
        influx - the InfluxDB info including ip, db, user, pass.
            -> Example influx = {'ip': 'https://sensorweb.us', 'db': 'algtest',
                                'user':'test', 'passw':'sensorweb'}
        dataname - the dataname such as temperature, heartrate, etc
        timestamp - the epoch time (in second) of the first element in the data
                    array, such as datetime.now().timestamp()
        fs - the sampling interval of readings in data
        unit - the unit location name tag
    """
    max_size = 100
    count = 0
    total = len(data)
    prefix_post  = "curl -s -POST \'"+ influx['ip']+":8086/write?db="+influx['db']+"\' -u "+ influx['user']+":"+ influx['passw']+" --data-binary \' "
    http_post = prefix_post
    for value in data:
        count += 1
        http_post += "\n" + table_name +",location=" + unit + " "
        http_post += data_name + "=" + str(value) + " " + str(int(start_timestamp*10e8))
        start_timestamp +=  1/fs
        if(count >= max_size):
            http_post += "\'  &"
            # print("Write to influx: ", table_name, data_name, count)
            subprocess.call(http_post, shell=True)
            total = total - count
            count = 0
            http_post = prefix_post
    if count != 0:
        http_post += "\'  &"
      #   print("Write to influx: ", table_name, data_name, count, data)
        subprocess.call(http_post, shell=True)

if __name__ == '__main__':
   macEthCust = ''
   if(len(sys.argv) > 1):
      port = sys.argv[1]
   else:
      port = "/dev/ttyUSB0" # default
      print(f"Usage: python3 {sys.argv[0]} port")
      print(f"\t Examples: \n\t\tpython3 {sys.argv[0]} /dev/ttyUSB0 (read from USB-serial) \n\t\tpython3 {sys.argv[0]} /dev/ttyS0 (for UART-serial) \n\t\tpython3 {sys.argv[0]} none (for simulation mode)\n")

      exit()
   if(len(sys.argv) > 2):
       macEthCust = sys.argv[2]

   print("Read:", port)
   has_serial = False
   ser = 0
   if port != "none":
      ser = serial.Serial(port, baudrate=115200, timeout=5)
      has_serial = True
   fs = 100
   macEth = mac_address()
   if(macEthCust != ''):
       macEth=macEthCust
   print("My ethernet MAC is: ", macEth)
   print(f'open browser with user/password:guest/sensorweb_guest to see waveform at grafana: \n\thttps://www.sensorweb.us:3000/d/VgfUaF3Gz/bdotv2-plot?orgId=1&var-mac1={macEth}&from=now-1m&to=now&refresh=5s')


   dest = {'ip':'https://sensorweb.us', 'db':'shake', 'user':'test', 'passw':'sensorweb'}
   # subprocess.call("/opt/belt/beltWrite.py", shell=True)

   ser.flush()
   while(True):
      if has_serial:
         count = ser.inWaiting()
      else:
         count = fs # 
      # print('inWaiting:', count)
      while(ser.inWaiting()<729):
          time.sleep(0.01)
      if count > 0:
         if has_serial:
            # receive = ser.read(ser.inWaiting()) 
            receive = []
            for x in range(99):
               receive += [ser.readline()] 
         else:
            receive = [10, 20, 30, 40, 50]*int(fs/5) # np.random.randint(10, 200, size=fs)  #       

         count = len(receive)
         each = float(count)
         start_timestamp = datetime.datetime.now().timestamp() - ((each)/fs) 
         # print(receive)
         data = parse(receive, fs)
         write_influx(dest, macEth, "Z", "value", data, start_timestamp, fs)

         # print(start_timestamp, " count:" + str(count) + " each:" + str(each) + " verify each:" + str(len(data)))
      # some serial ports require a write operation to start sending data out, then uncomment below and replace with a serial write program
      # else: 
      #    subprocess.call("/opt/belt/beltWrite.py", shell=True)
      # print('inWaiting:', ser.inWaiting())