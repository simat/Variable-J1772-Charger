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

energyrecsize=50  # size of charge session log entry in energy.log

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

def updatetotals(energy,stopday):
  """Updates the charge totals and averages, call at the end of each charge cycle"""
  global dayenergy
  totyear=0.0
  cntyear=1
  tot90day=0.0
  cnt90day=1
  tot30day=0.0
  cnt30day=1
  tot5day=0.0
  cnt5day=1
  tot1day=0.0
  cnt1day=1
  try:
    with open("energy.log",'r') as f:
      f.seek(-energyrecsize,2) # point to last entry
      entry=f.read(energyrecsize)
#      print (entry,entry[15:19])
      lastsession=float(entry[20:27])
      cursession=int(entry[15:19])
      prevsession=cursession
      deltaday=stopday-cursession

      try:
        while deltaday<365:
          energy=float(entry[20:27])
          sameday= cursession-prevsession
          totyear+=energy
          if sameday != 0:
            cntyear+=1
          if deltaday<90:
            tot90day+=energy
            if sameday != 0:
              cnt90day+=1
          if deltaday<30:
            tot30day+=energy
            if sameday != 0:
              cnt30day+=1
          if deltaday<5:
            tot5day+=energy
            if sameday != 0:
              cnt5day+=1
          if deltaday==0:
            tot1day+=energy
            cnt1day+=1
          prevsession=cursession
          f.seek(-2*energyrecsize,1)
          entry=f.read(energyrecsize)
#          print(entry,entry[15:19])
          cursession=int(entry[15:19]) # date of next charge session
          deltaday=stopday-cursession
      except (Exception,OSError,ValueError) as err:
        logexception(err)

  except (Exception,OSError,ValueError) as err:
    logexception(err)
  else:
    dayav90days=tot90day/cnt90day
    dayav30days=tot30day/cnt30day
    dayav5days=tot5day/cnt5day

    line1="Last Update Time {}".format(localtime())
    line2="Last Year    {:>7.1f}kWh".format(totyear)
    line3="Last 30 Days {:>7.1f}kWh".format(tot30day)
    line4="Last 5 Days  {:>7.1f}kWh".format(tot5day)
    line5="Current Day  {:>7.1f}kWh".format(tot1day)
    line6="Last Session {:>7.1f}kWh".format(lastsession)
    line7="Av. per day charging occurs over 90 days {:>4.4f}kWh".format(dayav90days)
    line8="Av. per day charging occurs over 30 days {:>4.4f}kWh".format(dayav30days)
    line9="Av. per day charging occurs over 5 days  {:>4.4f}kWh".format(dayav5days)
    try:
      with open("EnergyStats",'w') as f:
        f.write("{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n{6}\n{7}\n{8}\n".format(line1,line2,line3,line4,line5,line6,line7,line8,line9))
    except (Exception,OSError,ValueError) as err:
      logexception(err)
