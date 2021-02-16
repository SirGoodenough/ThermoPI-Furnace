# ThermoPI
Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server.
## USAGE:
Install the program into opt/ThermoPI-Furnace or any suitable location. (Some people like /usr/local/bin instead of /opt)

You will need to rename the file ***MYsecretsSample.py*** to ***MYsecrets.py***.
Edit the contents of the new ***MYsecrets.py*** to match your MQTT installation.

You will need to edit the list of sensors to match your set-up.  
This depends on which pins, which spi ports, and the s/n of the 2 wire sensors you have installed.  
> This line will need to be edited to match your situation: 
 ``` list = [999, 4, 17, "60d70d1864ff", "0ad50d1864ff", 0, 1, 999, 999]```

The list here is my setup as it is currently running.  The 999 numbers are place holders, they sit as the first and the last 2 items in the list.  In my case I have a sensor on GPIO4, GPIO17, then 2 2-wire sensors with the s/n listed, then the 2 thermocouples are set up in the spi 0 and 1 slot as stated in the documentation in the furnace.py file .
If you have more or less sensors, you will need to adjust the loop and the list so that it will pick up the correct variable on the correct loop thru the program.

The furnace.py program itself is well documented.
Follow the comments there to change the necessary information.
## AUTO-Start:
Here is a good reference on setting up a program to run from systemd. Use it to get familiar with the process.
        [How-To Geek on 'Startup With Systemd'](https://www.howtogeek.com/687970/how-to-run-a-linux-program-at-startup-with-systemd/)

> Here is what my '/lib/systemd/system/thermoPIFurnace.service' file looks like: 
```
[Unit]
 Description=Grab Furnace Temperatures
 After=multi-user.target

 [Service]
 Type=idle
 ExecStart=/usr/bin/python opt/ThermoPI-Furnace/furnace.py
 Restart=on-failure

 [Install]
 WantedBy=multi-user.target
```

The furnRestart.sh is the script to quickly restart the process if needed during troubleshooting.  I found it helpful.
## Requirements:
Program requirements (as written):  (feel free to fork it and convert to Python 3.x...)
+ Python 2.7 
+ pigpio            For reading the Thermocouples (MAX6675)
+ paho-mqtt         For MQTT broker connection
+ W1ThermSensor     For 2 wire temp sensors (DS18B20)
+ Adafruit_DHT      For temp / humid sensors (AM2302)

**If you have any questions, comments or additions be sure to add an issue and bring them up on my Discord Server:** 

### Contact Links:
* [What are we Fixing Today Homepage](https://www.WhatAreWeFixing.Today/)
* [YouYube Channel Link](https://bit.ly/WhatAreWeFixingTodaysYT)
* [What are we Fixing Today Facebook page](https://bit.ly/WhatAreWeFixingTodayFB)
* [What are we Fixing Today Twitter](https://bit.ly/WhatAreWeFixingTodayTW)
* [Discord WhatAreWeFixingToday](https://discord.gg/Uhmhu3B)

### Please help support the channel:
* [Patreon Membership](https://www.patreon.com/WhatAreWeFixingToday)

* [Buy me Coffee](https://www.buymeacoffee.com/SirGoodenough)
* [PayPal one-off donation link](https://www.paypal.me/SirGoodenough)
* [Cash App \$CASHTAG](https://cash.me/$SirGoodenough)
* [Venmo cash link](https://venmo.com/SirGoodenough)
