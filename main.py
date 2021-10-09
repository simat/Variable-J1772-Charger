# This example requires the micropython_dotstar library
# https://github.com/mattytrentini/micropython-dotstar

from machine import SPI, Pin
import tinypico as TinyPICO
from dotstar import DotStar
import time, random, micropython, gc

# Configure SPI for controlling the DotStar
# Internally we are using software SPI for this as the pins being used are not hardware SPI pins
spi = SPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) )
# Create a DotStar instance
dotstar = DotStar(spi, 1, brightness = 0.5 ) # Just one DotStar, half brightness
# Turn on the power to the DotStar
TinyPICO.set_dotstar_power( True )

# Say hello
print("\nHello from TinyPICO!")
print("--------------------\n")

# Show available memory
print("Memory Info - micropython.mem_info()")
print("------------------------------------")
micropython.mem_info()

# Get the amount of RAM and if it's correct, flash green 3 times before rainbow, otherwise flash red three times
def check_ram():
    gc.collect()
    ram = gc.mem_free()
    col = ( 255, 0, 0, 1 )
    if ram > 4000000:
        col = ( 0, 255, 0, 1 )

    for i in range (3):
        dotstar[0] = col
        time.sleep_ms(200)
        dotstar[0] = ( 0, 0, 0, 10 )
        time.sleep_ms(50)

    time.sleep_ms(250)

# Check the RAM
check_ram()

#from microWebSrv import MicroWebSrv
#mws = MicroWebSrv(webPath='/')      # TCP port 80 and files in /
#mws.Start(threaded=True) # Starts server in a new thread

import evcharge
evcharge.main()
