import serial 
import time
ser = serial.Serial('/dev/ttyS0', 115200)
if ser.isOpen == False:
   ser.Open()
try:
  ser.flushInput()
  while True:
           response = ser.read(10)
           response = response.replace(b'\n',b'').replace(b'\r',b'')
           print (str(response))
           time.sleep(0.5)
except KeyboardInterrupt: 
       ser.close()
