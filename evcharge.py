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
from time import sleep_ms, sleep_us, time, localtime
import tinypico as TinyPICO
from dotstar import DotStar
from net import deltapwr,sendhtml
from logger import log, localtimestamp, maketimestamp, updatetotals, logexception
from os import remove
# watchdog=WDT(timeout=600000) # timeout 10 minutes
spi = SPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) )
dotstar = DotStar(spi, 1, brightness = 0.8 ) # Just one DotStar, half brightness
TinyPICO.set_dotstar_power( True )
# dotstar[0] = ( r, g, b, 0.5)
dotstar[0] = ( 0, 0, 0)

CPidle=1023
EVnoconnect= 248 # 12V on CP line
EVready= 155 # EV ready for charge
EVcharging= 85
onevolt = (EVnoconnect-EVready)/3
relay = PWM(Pin(27), freq=20000, duty=0)
#CPout = Pin(14, Pin.OUT, value=1)
ControlPilot = PWM(Pin(14), freq=1000, duty=CPidle)
CPstate = Pin(15, Pin.IN)  # cant get state of CPoutput directly
#ControlPilot.duty(1023)
ProximityPilot = Pin(4, Pin.OUT, value=0)
CPin = ADC(Pin(33))
CPin.width(ADC.WIDTH_9BIT)
TestOut = Pin(25,Pin.OUT, value=0)
ChargeI = 0.0  # vehicle charging current
ChargeIMax = 18.0  # maximum vehicle charge current
VMains = 230.0 # mains voltage
duty =100 # current CP PWM duty
delta =0.0 # current delta power from web
nexttime =0 # seconds till next HTML sample
timestamp=''
currenttime=0
energytotal =0.0
chargestarttime=0
dayenergy=0.0 #current days energy production



def readCP():
  """Return voltage on CP line
     has to wait for CP PWM output to be high"""

  for i in range(20):
    if CPstate.value() == False:
      break
    sleep_us(50)

  for i in range(100):
    if CPstate.value() == True:
      break
  sleep_us(950)

  TestOut.on()
#  sleep_us(50)
  fred=CPin.read()
  TestOut.off()
  return fred


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

def relayon(start=1023,hold=700):
  if relay.duty()==0:
    relay.duty(start)
    sleep_ms(500)
    relay.duty(hold)

def relayoff():
  relay.duty(0)

def calcduty():
  """calculates new duty cycle after getting change variation from web"""
  global ChargeI,duty, delta, nexttime, timestamp
  delta, nexttime,timestamp =deltapwr()
  ChargeI=min(max(ChargeI+delta/(1.5*VMains),0.0),ChargeIMax)
  if ChargeI == 0.0 and delta < -3000.0:
    duty=1023
  elif ChargeI > 6.0:
    duty=int(511*ChargeI/30.0)
  else:
    if duty != 1023:
      duty = 100

def stopcharge():
  global energytotal, currenttime, chargestarttime
  """store energy sent to car for last charging session"""

  updatetotals(energytotal)
  log('energy',' {:.3f}kWh Charge Start{} Charge Time {:.1f} hr'.format(energytotal,maketimestamp(localtime(chargestarttime)),(time()-chargestarttime)/3600))
  try:
    f=open('energyday.log','r')
    pos=f.seek(-100,2)
    enddata=f.read()
    pos=enddata.index('\n')
    if enddata[pos+1:pos+9]==localtimestamp()[0:8]:
      pass
  except:
    pass

  energytotal =0.0

def main():
  try:
    global duty, nexttime, timestamp, currenttime, energytotal, chargestarttime, dayenergy

    dayenergy=0.0
    energytotal = 0.0
    duty =1023
    CPvalue = 0
    CPerror  = False
    state = 0 # charge state 1=Not connected, 2=EV connected, 3=EV charge, 4= Error
    lasttime=0
    relayoff()
    ControlPilot.duty(CPidle)
    _,_,timestamp=deltapwr()
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
      calcduty()
      message='CP value={} CP duty={} ChargeI={} Delta={} State={} Energy={:.3f} DayEnergy={:.1f}' \
              .format(CPvalue,ControlPilot.duty(),ChargeI,delta,state,energytotal,dayenergy)
      print (message)
      log('log',message)
      for i in range(nexttime*2):
        CPvalue=readCP()
        message='Timestamp {}\nCP value={} CP duty={} ChargeI={} Delta={} State={} Energy={:.3f} DayEnergy={:.1f}' \
                .format(localtimestamp(),CPvalue,ControlPilot.duty(),ChargeI,delta,state,energytotal,dayenergy)
        sendhtml(message)
        print(CPvalue,end='\r')
        if checkCPstate(EVnoconnect,CPvalue):
          relayoff()
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
          relayoff()
          ControlPilot.duty(duty)
          CPerror = False
          dotstar[0] =(0, 0, 150)
          if state != 2:
            log('events','EV ready')
            if state == 3:
              stopcharge()
            state =2
        elif checkCPstate(EVcharging,CPvalue):
          relayon()
          ControlPilot.duty(duty)
          CPerror = False
          dotstar[0] =(0, 150, 0)
          currenttime=time()
          if state != 3:
            log('events','EV charging')
            lastt=localtime(lasttime)
            currt=localtime(currenttime)
            if lastt[0]!=currt[0] or lastt[1]!=currt[1] or lastt[2]!=currt[2]:
              dayenergy=0.0
            state =3
            lasttime=currenttime
            chargestarttime=lasttime

          if duty !=1023:
            charge=30*duty/511
            energydelta=min(charge,16.0)*VMains*(currenttime-lasttime)/3600000
            energytotal+=energydelta
            dayenergy+=energydelta
          lasttime=currenttime

        else:  #error
          if CPerror == False:
            CPerror = True
          else:
            relayoff()
            ControlPilot.duty(1023)
            dotstar[0] = (150, 0, 0)
            if state !=4:
              log('events',"CP error")
              if state ==3:
                print ('at error')
                stopcharge()
              state =4
        sleep_ms(500)
  except Exception as e:
    logexception(e)
    raise
#    reset()

# main()
