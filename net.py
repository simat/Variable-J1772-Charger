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

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
poller=poll()
poller.register(s, POLLIN)

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
def deltapwr():
  """returns delta power level from net"""

  global lasttime, numerrors, nexttime, lasttime
#  for tries in range(3):
  try:
    s=socket.socket()
    s.connect(('192.168.2.117',8080))
    s.send(bytes('GET /excesspwr.php \r\nHost: 192.168.2.117\r\n\r\n', 'utf8'))
    data = str(s.recv(400), 'utf8')
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
    data=data[index+29:-1]
    index=data.index('Timestamp')
    timestamp=data[index+10:index+24]
    nexttime=max(min(int(timestamp)-currenttime+62,65),10)
    data=data[index+25:-1]
    data=data.split('</p>\n')
    line1=float(data[1][31:data[1].index('W')])
    line2=float(data[2][31:data[2].index('W')])
    print (currenttime, timestamp, nexttime, data[1])
    if line1!=line2 or timestamp==lasttime:
      raise Exception('Invalid or Stale Data')
  except (Exception,OSError,ValueError) as err:
    numerrors +=1
    nexttime=60
    timestamp=localtimestamp()
    logexception(err)
    if numerrors > 10:
      delta=-30000 # shut down charging
    else:
      delta= 0 # don't change charging current
  else:
    numerrors = 0
    lasttime=timestamp
    delta=line1
  finally:
    s.close()

  return delta, nexttime, timestamp
