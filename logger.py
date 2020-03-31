# *****J1772 EV charge controller logging logger.py*****
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


import sys
from machine import RTC

logs = ('events','errors')

try:
  for i in logs:
    if os.stat(i+'.log')[6]>10000:
      os.rename(i+'.log'),i+'.old.log')
except OSError:
  print('IO error during init logs')

rtc=RTC()

def log(logname,message):

  try:
    f=open(logname+'log','a')
    time=rtc.now()
    timestamp=''
    for i in time:
      timestamp=timestamp+str(time(i))

    f.write(timestamp+message)
    f.close
  except:
    pass
