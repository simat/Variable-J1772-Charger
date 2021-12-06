# *****J1772 EV charge controller network routines net.py*****
# Copyright (C) 2020 Simon Richard Matthews
# Project loaction https://github.com/simat/Variable-J1772-Charger
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import socket
from select import poll,POLLIN
from logger import log, logexception, localtimestamp
import network
from _thread import start_new_thread as start
import config
from time import sleep_ms

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
poller=poll()
poller.register(s, POLLIN)
connectssid=''
wlan=''
def startwifi():
  """Starts WiFi"""

  global connectssid,wlan

  numtries=3
  while numtries > 0:
    numtries-=1
    try:
      wlan = network.WLAN(network.STA_IF)
      wlan.active(False)
    #  wlan.disconnect()
      sleep_ms(10)
      wlan.active(True)
      sleep_ms(10)
      stations=wlan.scan()
      print ('scan',stations)
      found=False
      for i in stations:
        for j in config.networks:
          print('station:{} config:{}'.format(i[0].decode(),j))
          if i[0].decode()==j:
            found=True
            break
        if found:
          break
        numloops=30
        while numloops >0:
          numloops-=1
          if wlan.isconnected:
            break
          sleep_ms(100)
        if numloops ==0:
          raise IOError("Didn't connect to wlan")

    except KeyboardInterrupt:
      raise
    except Exception as err:
      print (err)
      sleep_ms(1000)
    if found:
      break
  if found:
    connectssid=j
    print(connectssid)
    print(config.networks[connectssid],config.networks[connectssid]['passwrd'])
    wlan.connect(connectssid,config.networks[connectssid]['passwrd'])
    sleep_ms(5000)
  else:
    wlan.active(False)
    sleep_ms(10)
    wlan = network.WLAN(network.AP_IF)
    wlan.active(True)


def sendhtml(message):
  """sends status via HTMP to any device making a request on port 80"""

  res = poller.poll(1)
  if res:
    try:
      cl, addr = s.accept()
#      print('client info', cl.recv(100))
      cl_file = cl.makefile('rwb', 0)
      cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
      cl.send(message)
    except OSError as err:
      logexception(err)
    finally:
      try:
        cl.close()
      except:
        pass

numerrors =0
nexttime =0
lasttime = ''
minmaxpwr=[0,0]
delta=0
timestamp =0
def deltapwr():
  """returns delta power and minimum power level from net"""

  global lasttime, numerrors, nexttime, lasttime, minmaxpwr, delta, timestamp
#  for tries in range(3):
  try:
    s=socket.socket()
    s.connect((config.networks[connectssid]['excesspwrIPAdr'],config.networks[connectssid]['excesspwrIPPort']))
    s.send(bytes('GET /excesspwr.php \r\nHost: 192.168.2.117\r\n\r\n', 'utf8'))
    data = str(s.recv(600), 'utf8')
#      s.close()
#      break
#    except OSError as err:
#      s.close()
#      log('error',str(err))
#      if tries==2:
#        raise

#  try:
    currenttime=0

    index=data.index('Current Time')
    currenttime=int(data[index+13:index+27])
    cutimestr=data[index+13:index+27]
    data=data[index+29:-1]
    index=data.index('Timestamp')
    timestamp=data[index+10:index+24]
    nexttime=max(min(int(timestamp)-currenttime+62,65),10)
    print ("webtime {} datatime {} time {} nexttime {}".format(cutimestr[-4:],timestamp[-4:],localtimestamp()[-4:],nexttime))
    data=data[index+29:-1]
    data=data.split('</p>\n')
#    print (currenttime, timestamp, nexttime, data)
    line1=float(data[0][32:data[0].index('W')])
    line2=float(data[1][32:data[1].index('W')])
    line3=float(data[2][24:data[2].index('W')])
    line4=float(data[3][24:data[3].index('W')])
    line5=float(data[4][24:data[4].index('W')])
    line6=float(data[5][24:data[5].index('W')])
    if line1!=line2 or timestamp==lasttime or line3!=line4 or line5!=line6:
      raise Exception('Invalid or Stale Data')
  except (Exception,OSError,ValueError) as err:
    numerrors +=1
    nexttime=60
    timestamp=localtimestamp()
    logexception(err)
    if numerrors >= 10:
      minmaxpwr = [0,0] # shut down charging
    else:
      delta= 0 # don't change charging current
  else:
    numerrors = 0
    lasttime=timestamp
    delta=line1
    minmaxpwr[0]=line3
    minmaxpwr[1]=line5
  finally:
    s.close()

  return delta, nexttime, timestamp, minmaxpwr
