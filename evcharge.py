# *****J1772 EV charge controller main file evcharge.py*****
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


from machine import Pin, PWM, ADC, SPI, WDT, RTC, reset
from utime import sleep_ms, sleep_us, time, localtime,ticks_ms,ticks_diff
import tinypico as TinyPICO
from dotstar import DotStar
from net import deltapwr,sendhtml,wlan
from logger import log, localtimestamp, maketimestamp, updatetotals, logexception
from os import remove
from ds18x20 import DS18X20
from onewire import OneWire
import config
import sys

ds_pin = Pin(23)
ds_sensor = DS18X20(OneWire(ds_pin))
roms = ds_sensor.scan()
# watchdog=WDT(timeout=600000) # timeout 10 minutes
spi = SPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) )
dotstar = DotStar(spi, 1, brightness = 0.8 ) # Just one DotStar, half brightness
TinyPICO.set_dotstar_power( True )
# dotstar[0] = ( r, g, b, 0.5)
dotstar[0] = ( 0, 0, 0)

debug= True
CPidle=1023
EVzero=0 # value during zero PWM
EVnoconnect= 248 # 12V on CP line
EVready= 155 # EV ready for charge
EVcharging= 85
onevolt = (EVnoconnect-EVready)/3
relays= (PWM(Pin(27), freq=20000, duty=0),PWM(Pin(14), freq=20000, duty=0),PWM(Pin(4), freq=20000, duty=0))
#CPout = Pin(14, Pin.OUT, value=1)
ControlPilot = PWM(Pin(15), freq=1000, duty=CPidle)
#CPstate = Pin(15, Pin.IN)  # cant get state of CPoutput directly
#ControlPilot.duty(1023)
#ProximityPilot = Pin(4, Pin.OUT, value=0)
CPin = ADC(Pin(33))
CPin.width(ADC.WIDTH_9BIT)
TestOut = Pin(25,Pin.OUT, value=0)
ChargeI = 0.0  # vehicle charging current
ChargeIMax = 22.0  # maximum vehicle charge current
VMains = 230.0 # mains voltage
ChargePwr = 0.0
duty =100 # current CP PWM duty
delta =0.0 # current delta power from web
minmaxpwr=[0,0] # requested minimum and maximum charge power

def readTemp(): # returns temperature from DX18x20 temp ds_sensor
  ds_sensor.convert_temp()
  return ds_sensor.read_temp(roms[0])

okthreshold=5
errorthreshold=3
def readCP(numloops=100):
  """Return voltage on CP line"""

  arr=bytearray(300)
  startt=ticks_ms()

  for i in range(numloops):
   fred=CPin.read()
   arr[fred]+=1

  endt=ticks_ms()
  validvals=[EVzero,EVnoconnect,EVready,EVcharging]
  evstate=[0,0,0,0,numloops]
  for j in range(4):
   for i in range(int(validvals[j]-onevolt),int(min(validvals[j]+onevolt,255))):
     evstate[j]+=arr[i]
  for i in range(4):
   evstate[4]-=evstate[i]
  if config.debug:
    print(ticks_diff(endt,startt),evstate)
  if evstate[1]>=okthreshold and evstate[2]<errorthreshold and\
                 evstate[3]<errorthreshold and evstate[4]<errorthreshold:
    output=EVnoconnect
  elif evstate[2]>=okthreshold and evstate[1]<errorthreshold and\
                   evstate[4]<errorthreshold:
    output=EVready
  elif evstate[3]>=okthreshold and evstate[1]<errorthreshold and\
                   evstate[2]<errorthreshold:
    output=EVcharging
  else:
    output=-1

  return output


#  CPvalue = 0
#  for i in range(10):
#    CPvalue=CPvalue+CPin.read()
#    sleep_us(10)
#  CPvalue=CPvalue/10
#  if ControlPilot.duty()!=16992:
#    CPvalue=CPvalue*CPidle/ControlPilot.duty()  # compensate for PWM duty
#  return CPvalue

def checkCPstate(CPlevel, CPvalue):
  CPmatch=CPvalue > (CPlevel-onevolt) and CPvalue < (CPlevel+onevolt)
  return CPmatch

def relayson(phases=(1,0,0),start=1023,hold=700):
  """turn on relays to phases specified by (P1,P2,P3)"""
  for i in range(3):
    if relays[i].duty()==0 and phases[i]:
      relays[i].duty(start)
  sleep_ms(500)
  for i in range(3):
    if phases[i]:
      relays[i].duty(hold)

def relaysoff(phases=(1,1,1)):
  """turn off relays to phases specified by (P1,P2,P3)"""

  for i in range(3):
    relays[i].duty(0)

def calcduty():
  """calculates new duty cycle after getting change variation from web"""
  global ChargeI, ChargePwr, duty, delta, nexttime, timestamp, minmaxpwr, state
  if config.StandAlone:
    ChargeI=config.StandAloneCurrent
    delta, nexttime,timestamp,minmaxpwr =0, 60, localtimestamp(),\
    [0, ChargeI*VMains]
  else:
    delta, nexttime,timestamp,minmaxpwr =deltapwr()

  if minmaxpwr[1]==0:
    duty=1023
    ChargeI=0.0
  else:
    ChargeI=max(min(ChargeI+delta/(1.0*VMains),ChargeIMax,minmaxpwr[1]),0.0)
    if ChargeI > 6.0:
      duty=int(511*ChargeI/30.0)
    else:
      duty = 100
      ChargeI =6.0
  if state !=3:
    ChargeI=0.0
  ChargePwr=ChargeI*VMains*config.numphases/1000

def stopcharge():
  global energytotal, currenttime, chargestarttime
  """store energy sent to car for last charging session"""
  stoptime=time()
  stoptimetup=localtime(stoptime)
  stopday=max(0,stoptimetup[7]+int((stoptimetup[0]-2020)*365.25))
  log('energy',' {:3d} {:7.3f}kWh Charge Time {:4.1f}hr'.\
  format(stopday,energytotal,min((stoptime-chargestarttime)/3600,99)))
  updatetotals(energytotal,stopday)
  energytotal =0.0

def main():
  try:
    global duty, nexttime, timestamp, currenttime, energytotal, chargestarttime,\
           dayenergy, state

    dayenergy=0.0
    energytotal = 0.0
    duty =1023
    CPvalue = 0
    CPerror  = False
    state = 0 # charge state 1=Not connected, 2=EV connected, 3=EV charge, 4= Error
    lasttime=0
    endday=False
    relaysoff()
    ControlPilot.duty(CPidle)
    for i in range(50):
      if wlan.isconnected():
        break
      sleep_ms(100)
    _,_,timestamp,_=deltapwr()
    print(timestamp)
    rtc=RTC()
    rtc.init((int(timestamp[0:4]),int(timestamp[4:6]),int(timestamp[6:8]),0, \
             int(timestamp[8:10]),int(timestamp[10:12]),int(timestamp[12:14]),0))
    sleep_ms(100)
    try:
      remove('log.log')
    except:
      pass
    while True:
      del sys.modules['config']
      import config
      calcduty()
      currenttime=time()
      currt=localtime(currenttime)
      if currt[3]==23 and currt[4]==59 and endday==False:
        endday=True
        if dayenergy ==0:
          chargestarttime=currenttime
          stopcharge()
      else:
        endday=False

      for i in range(nexttime*2):
        startt=ticks_ms()
        CPvalue=readCP()
        message='Timestamp {}\nCP value={} CP duty={} ChargeI={:.1f} Power={:.1f} Delta={} State={} Temp={} Energy={:.3f} DayEnergy={:.1f}' \
                .format(localtimestamp(),CPvalue,ControlPilot.duty(),ChargeI,ChargePwr,int(delta),state,int(readTemp()),energytotal,dayenergy)
        sendhtml(message)
        if i==2:
          print (message[25:])
          log('log',message)
        print(CPvalue,end=' ')
        if checkCPstate(EVnoconnect,CPvalue):
          relaysoff()
          ControlPilot.duty(1023)
          CPerror = False
          dotstar[0] =(100, 100, 150)
          if  state != 1:
            log('events','EV not connected')
            if state == 3:
              print('at no connect')
              stopcharge()
            state = 1

        elif checkCPstate(EVready,CPvalue):
          relaysoff()
          ControlPilot.duty(duty)
          CPerror = False
          dotstar[0] =(0, 0, 150)
          if state != 2:
            log('events','EV ready')
            if state == 3:
              stopcharge()
            state =2
        elif checkCPstate(EVcharging,CPvalue):
          if state !=3:
            relayson(phases=config.phases)
          ControlPilot.duty(duty)
          CPerror = False
          dotstar[0] =(0, 150, 0)
          if state != 3:
            log('events','EV charging')
            lastt=localtime(lasttime)
            if lastt[0]!=currt[0] or lastt[1]!=currt[1] or lastt[2]!=currt[2]:
              dayenergy=0.0
            state =3
            lasttime=currenttime
            chargestarttime=lasttime

          energydelta=ChargePwr*(currenttime-lasttime)/3600
          energytotal+=energydelta
          dayenergy+=energydelta
          lasttime=currenttime

        else:  #error
          if CPerror == False:
            CPerror = True
          else:
            relaysoff()
            ControlPilot.duty(1023)
            dotstar[0] = (150, 0, 0)
            if state !=4:
              log('events',"CP error")
              if state ==3:
                print ('at error')
                stopcharge()
              state =4
        wrktime=ticks_diff(ticks_ms(),startt)
        sleep_ms(500-wrktime)
        print (wrktime,end=' \r')
  except Exception as e:
    logexception(e)
    raise
#    reset()

# main()
