# Variable-J1772-Charger
J1772 charge controller. Charge rate determined by feedback via the internet 

This project can be used to make a J1772 Electic Vehicle charger that will vary the vehicles charge rate detendant on feedback from say a demand management controller on an off-grid or grid-connect power system which could limit the amount of charge that the car is drawing to the amount of excess power available from say solar panels.

I am using this in an off-grid power system where my Beaglebone Black demand management controller running software in this project https://github.com/simat/BatteryMonitor sends information via an HTML file specififying the amount of excess energy available from my solar panels when the battery has reached a set SOC.

The format of the HTML file is fairly simple

Current Time 20201121105845  
Timestamp 20201121105801
Excess solar power available -105W  
Excess solar power available -105W  
Minimum demand energy 0W  
Minimum demand energy 0W  
Maximum demand energy 5000W  
Maximum demand energy 5000W  

The software uses this information to vary the duty cycle of the Control Pilot signal being sent to the EV as per the J1772 Standard https://en.wikipedia.org/wiki/SAE_J1772 which will vary the amount of power that the car will draw from the power supply.

"Minimum demand energy" is the minumum power that the controller should be supplying to the car  
"Maximum demand energy" is the maximum power that the controller should be supplying to the car, 0W means no charging

The software returns status information about the charging to any request sent to port 80 (e.g.http://[IP address of TinyPICO]/)  
**Timestamp 20201009125244 CP value=83 CP duty=158 ChargeI=9.4 Power=2.2 Delta=19 State=3 Energy=9.648 DayEnergy=11.5**

There are a number of log files  
**EnergyStats** gives summary of charge session averages and charge totals  
**energy.log** is a log of all the individual charge sessions  
**events.log** gives a list of charging events  
**errors.log** gives a list of all errors  
**log.log** gives a detailed log since the software was started

The circuit supplied as part of the documentation and the software will not make a device that fully complies with the SAE J1772 standard. In particular it does not check for any faults in the AC supply. In Australia AC supply faults like ground faults are checked and handled at the power distribution panel. If you want a fully complient DIY controller I suggest you look here https://www.openevse.com/ They have some excellent documentation on their products and the J1772 standard here https://openev.freshdesk.com/support/home

My project uses the Tini Pico microcontroller https://www.tinypico.com/ but you could use a Raspberry PI, Beaglebone Black or any other microcontroller that runs Python 3.

If you have any questions or comments please use the Git messaging system https://github.com/simat/Variable-J1772-Charger/issues
