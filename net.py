import socket
from select import poll,POLLIN

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
    cl, addr = s.accept()
#    print('client connected from', addr)
    cl_file = cl.makefile('rwb', 0)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(message)
    cl.close()

lasttime =0
numerrors =0
nexttime =0

def deltapwr():
  """returns delta power level from net"""

  global lasttime, numerrors, nexttime

  try:
    s=socket.socket()
    s.connect(('192.168.2.117',8080))
    s.send(bytes('GET /excesspwr.php \r\nHost: 192.168.2.117\r\n\r\n', 'utf8'))
    data = str(s.recv(400), 'utf8')
    s.close()
  except OSError as err:
    print("OS error: {0}".format(err))
    s.close()
  try:
    index=data.index('Current Time')
    currenttime=int(data[index+13:index+27])
    data=data[index+29:-1]
    index=data.index('Timestamp')
    timestamp=int(data[index+10:index+24])
    nexttime=max(min(timestamp-currenttime+61,65),10)
    data=data[index+25:-1]
    data=data.split('</p>\n')
    line1=int(data[1][31:data[1].index('W')])
    line2=int(data[2][31:data[2].index('W')])
  except:
    pass
  print (currenttime, timestamp, nexttime, data[1])
  if line1!=line2 or timestamp==lasttime:
    numerrors =+1
    if numerrors > 10:
      delta=-30000 # shut down charging
    else:
      delta= 0 # don't change charging current
  else:
    numerrors = 0
    lasttime=timestamp
    delta=line1

  return delta, nexttime
