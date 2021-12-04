# ThermoPI-Furnace
Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server.
## USAGE:
Install the program into opt/ThermoPI-Furnace or any suitable location. (Some people like /usr/local/bin instead of /opt)  Make sure the username that is going to be running this script has access to the files and is able to get at python and anything else needed and used here-in.

You will need to rename the file ***MYsecretsSample.yaml*** to ***MYsecrets.yaml***.
Edit the contents of the new ***MYsecrets.yaml*** to match your MQTT & Home Assistant installation and requirements.  You will also need to supply the full path to the secrets file in the **Get the parameter file** section of this python code around line 225.

## AUTO-Start:
Here is a good reference on setting up a program to run from systemd. Use it to get familiar with the process.   

[How-To Geek on 'Startup With Systemd'](https://www.howtogeek.com/687970/how-to-run-a-linux-program-at-startup-with-systemd/)

The furnRestart.sh is the script to quickly restart the process if needed during troubleshooting.  I found it helpful.

## Requirements:
Program requirements (as written):  (Feel free to fork it & update the obsolete DHT Libraries to CircuitPython DHT Libraries and dropping me a merge request...)
+ Python 3.6 or better
+ [PyYAML](https://pypi.org/project/PyYAML/) For reading the YAML parameter file
+ [pigpio](http://abyz.co.uk/rpi/pigpio/python.html) For reading the Thermocouples (MAX6675)
+ [max6675](https://github.com/tdack/MAX6675) Thermocouple demux code
+ [W1ThermSensor](https://github.com/timofurrer/w1thermsensor) For 2 wire temp sensors (DS18B20)
+ [Adafruit_DHT](https://github.com/adafruit/Adafruit_Python_DHT) For temp / humid sensors (AM2302)
+ [paho-mqtt](https://pypi.org/project/paho-mqtt/) For MQTT broker connection

**If you have any questions, comments or additions be sure to add an issue and bring them up on my Discord Server:** 

### Contact Links:
* [Discord WhatAreWeFixingToday](https://discord.gg/Uhmhu3B)
* [What are we Fixing Today Homepage](https://www.WhatAreWeFixing.Today/)
* [YouYube Channel Link](https://bit.ly/WhatAreWeFixingTodaysYT)
* [What are we Fixing Today Facebook page](https://bit.ly/WhatAreWeFixingTodayFB)
* [What are we Fixing Today Twitter](https://bit.ly/WhatAreWeFixingTodayTW)

### Please help support the channel:
* [Patreon Membership](https://www.patreon.com/WhatAreWeFixingToday)
* [Buy me Coffee](https://www.buymeacoffee.com/SirGoodenough)
* [PayPal one-off donation link](https://www.paypal.me/SirGoodenough)
* [Cash App \$CASHTAG](https://cash.me/$SirGoodenough)
* [Venmo cash link](https://venmo.com/SirGoodenough)


## Disclaimer

:warning: **DANGER OF ELECTROCUTION** :warning:

If your device connects to mains electricity (AC power) there is danger of electrocution if not installed properly. If you don't know how to install it, please call an electrician (***Beware:*** certain countries prohibit installation without a licensed electrician present). Remember: _**SAFETY FIRST**_. It is not worth the risk to yourself, your family and your home if you don't know exactly what you are doing. Never tinker or try to flash a device using the serial programming interface while it is connected to MAINS ELECTRICITY (AC power).

We don't take any responsibility nor liability for using this software nor for the installation or any tips, advice, videos, etc. given by any member of this site or any related site.
