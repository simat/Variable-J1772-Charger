from machine import Pin, PWM, ADC, SPI, WDT
from time import sleep_ms, sleep_us
import tinypico as TinyPICO
from dotstar import DotStar
from net import deltapwr,sendhtml

# watchdog=WDT(timeout=600000) # timeout 10 minutes
spi = SPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) )
dotstar = DotStar(spi, 1, brightness = 0.8 ) # Just one DotStar, half brightness
TinyPICO.set_dotstar_power( True )
# dotstar[0] = ( r, g, b, 0.5)
dotstar[0] = ( 0, 0, 0)

CPidle=1023
EVnoconnect= 237 # 12V on CP line
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
  global ChargeI,duty, delta, nexttime
  delta, nexttime=deltapwr()
  ChargeI=min(max(ChargeI+delta/(1.5*VMains),0.0),ChargeIMax)
  if ChargeI == 0.0 and delta < -3000:
    duty=1023
  elif ChargeI > 6.0:
    duty=int(511*ChargeI/30)
  else:
    if duty != 1023:
      duty = 100


def main():
  try:
    global duty, nexttime
    duty =1023
    CPvalue = 0
    CPerror  = False
    relayoff()
    ControlPilot.duty(CPidle)
    sleep_ms(100)
    while True:
      calcduty()
      message='CP value={} CP duty={} ChargeI={} Delta={}'.format(CPvalue,ControlPilot.duty(),ChargeI,delta)
      print (message)
      for i in range(nexttime*2):
        CPvalue=readCP()
        message='CP value={} CP duty={} ChargeI={} Delta={}'.format(CPvalue,ControlPilot.duty(),ChargeI,delta)
        sendhtml(message)
        print(CPvalue,end='\r')
        if checkCPstate(EVnoconnect,CPvalue):
          relayoff()
          ControlPilot.duty(1023)
          CPerror = False
          dotstar[0] =(100, 100, 150)
        elif checkCPstate(EVready,CPvalue):
          relayoff()
          ControlPilot.duty(duty)
          CPerror = False
          dotstar[0] =(0, 0, 150)
        elif checkCPstate(EVcharging,CPvalue):
          relayon()

          ControlPilot.duty(duty)
    #      ControlPilot.duty(100)
          dotstar[0] =(0, 150, 0)
        else:  #error
          if CPerror == True:
            relayoff()
            ControlPilot.duty(1023)
            dotstar[0] = (150, 0, 0)

          CPerror = True

        sleep_ms(500)
  except Exception as e:
    from sys import open
    with open("error.log", "a") as f:
      sys.print_exception(e, f)

main()
