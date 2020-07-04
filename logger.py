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
from time import localtime, time, mktime
from machine import RTC
import os

"""logs = ('events','errors')

for i in logs:
  try:
    if os.stat(i+'.log')[6]>10000:
      os.rename(i+'.log',i+'.old.log')
  except OSError:
    print('IO error during init logs')
rtc=RTC()"""

def maketimestamp(time):
  """convert time tuple to string"""
  timestamp='{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(time[0],time[1],time[2],time[3],time[4],time[5])
  return timestamp

def localtimestamp():
  """returns timestamp as a string"""
  timestamp=maketimestamp(localtime())
  return timestamp

def log(logname,message):

  try:
    f=open(logname+'.log','a')
    timestamp=localtimestamp()
    f.write(timestamp+" "+message+'\n')
    f.close()
  except OSError as e:
    f.close()
    print('IO error during log write')
    sys.print_exception(e)

def logexception(exception):
  """log exception to error file"""
  try:
    with open("error.log", "a") as f:
      timestamp=localtimestamp()
      f.write(timestamp+'\n')
      sys.print_exception(exception, f)
      sys.print_exception(exception)
  except:
    print('IO error during exception log write')

def updatetotals(energy):
  """Updates the charge totals and averages, call at the end of each charge cycle"""
  global dayenergy
  with open("EnergyStats",'+') as f:
    lines=[]
    for i in range(10):
      lines.append(f.readline())
    lasttime=eval(lines[0][17:-1])
    gtotal=float(lines[1][13:-4])
    lastyear=float(lines[2][13:-4])
    last30days=float(lines[3][13:-4])
    last5days=float(lines[4][13:-4])
    currentday=float(lines[5][13:-4])
    lastsession=float(lines[6][13:-4])
    dayav90days=float(lines[7][31:-4])
    dayav30days=float(lines[8][31:-4])
    dayav5days=float(lines[9][31:-4])
    currenttime=time()
    deltaday=(time()-mktime(lasttime))/86400
    currenttime=localtime(currenttime)
    lastsession=energy
    if lasttime[2]==currenttime[2] and lasttime[1]==currenttime[1] and lasttime[0]==currenttime[0]:
      currentday+=lastsession
    else:
      dayav90days=(dayav90days*89+currentday)/90
      dayav30days=(dayav30days*29+currentday)/30
      dayav5days=(dayav5days*4+currentday)/5
      currentday=lastsession
      dayenergy=0.0
    if deltaday>5:
      last5days=lastsession
    else:
      last5days+=lastsession
    if deltaday>30:
      last30days=lastsession
    else:
      last30days+=lastsession
    if deltaday>365:
      lastyear=lastsession
    else:
      lastyear+=lastsession
    gtotal+=lastsession

    line1="Last Update Time {}".format(currenttime)
    line2="Grand Total  {:>7.1f}kWh".format(gtotal)
    line3="Last Year    {:>7.1f}kWh".format(lastyear)
    line4="Last 30 Days {:>7.1f}kWh".format(last30days)
    line5="Last 5 Days  {:>7.1f}kWh".format(last5days)
    line6="Current Day  {:>7.1f}kWh".format(currentday)
    line7="Last Session {:>7.1f}kWh".format(lastsession)
    line8="Running daily Av. over 90 days {:>4.4f}kWh".format(dayav90days)
    line9="Running daily Av. over 30 days {:>4.4f}kWh".format(dayav30days)
    line10="Running daily Av. over 5 days  {:>4.4f}kWh".format(dayav5days)
    f.seek(0)
    f.write("{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n{6}\n{7}\n{8}\n{9}\n".format(line1,line2,line3,line4,line5,line6,line7,line8,line9,line10))
