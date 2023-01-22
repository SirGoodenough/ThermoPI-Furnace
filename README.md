# ThermoPI-Furnace

Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server.

## USAGE

Install the program into opt/ThermoPI-Furnace or any suitable location. (Some people like /usr/local/bin instead of /opt) Make sure the username that is going to be running this script has access to the files and is able to get at python and anything else needed and used here-in.

You will need to rename the file ***MYsecretsSample.yaml*** to ***MYsecrets.yaml***.
Edit the contents of the new ***MYsecrets.yaml*** to match your MQTT & Home Assistant installation and requirements. You will also need to supply the full path to the secrets file in the **Get the parameter file** section of this python code around line 225.

This program grabs the 2nd half of the MAC address to use as the device ID. This only works consistantly when there is only 1 Ethernet interface configured or you have your multiple interfaces cloned to the same MAC Address. For instance if it boots from WIFI, it will grab that MAC, and if it uses the Ethernet cable or a USB interface, it will grab that MAC. You get my point. This can be avoided by hard coding the DeviceID with the random and unique number of your choice. Also I have not tested this with IP6 addresses. If you have solutions to any of this, please share.

## AUTO-Start

Here is a good reference on setting up a program to run from systemd. Use it to get familiar with the process.

[How-To Geek on 'Startup With Systemd'](https://www.howtogeek.com/687970/how-to-run-a-linux-program-at-startup-with-systemd/)

To run the program at boot in order to get constant readings, there is the ThermoPIFurnace.service to run this as a service with load-service.sh there to set it up as a service.

The load-service.sh script will stop and scratch reload the service from the local repository (Once you get all the permissions happy).

The furnRestart.sh is the script to quickly restart the process if needed during troubleshooting. I found it helpful.

## Requirements

Program requirements (as written):  (Feel free to fork it & update the obsolete DHT Libraries to CircuitPython DHT Libraries and dropping me a merge request...)

+ Python 3.6 or better
+ [PyYAML](https://pypi.org/project/PyYAML/) For reading the YAML parameter file
+ [pigpio](http://abyz.co.uk/rpi/pigpio/python.html) For reading the Thermocouples (MAX6675)
+ [max6675](https://github.com/tdack/MAX6675) Thermocouple demux code
+ [W1ThermSensor](https://github.com/timofurrer/w1thermsensor) For 2 wire temp sensors [(DS18B20)](http://www.d3noob.org/2015/02/raspberry-pi-multiple-temperature.html)
+ [Adafruit_DHT](https://github.com/adafruit/Adafruit_Python_DHT) For temp / humid sensors (AM2302)
+ [paho-mqtt](https://pypi.org/project/paho-mqtt/) For MQTT broker connection

**If you have any questions, comments or additions be sure to add an issue and bring them up on my Discord Server:**

## Installation

Suggested image for your PI is the latest 32bit lite.  You can use the regular load if you are using the PI for other things, but none of the gui functions are needed.  The Raspi imager software also lets you set up name, password, timezone, and start the ssh server on image load, so do those things.  After it boots log in and update-upgrade it to get all the packages up to date.  Reboot...

Use raspi-config to set up localization. In the 'Interface Options' enable 'Remote GPIO'. You may want to add other things.

### Update PIP, git, and pigpio

```bash
sudo apt-get update                  
sudo apt-get install python3-pip git pigpio python3-gpiozero python3-pigpio
sudo python3 -m pip install --upgrade pip setuptools wheel
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Install the requirements

```bash
sudo pip3 install Adafruit_DHT PyYAML w1thermsensor paho-mqtt
```

### Install the 1 wire devices

**NOTE:** Be sure to note the serial numbers of the sensors and know where each sensor is physically located.

```bash
sudo nano /boot/config.txt
```

Add this line at the end.  I am using GPIO23.  You can use another GPIO but the GPIO numbers (not the header pin numbers) must match where the dallas sensors are connected.

If you are using the internal pull-up (NOT Recommended) you can eliminate the ',pullup=0' part.

```text
dtoverlay=w1-gpio,gpiopin=23,pullup=0
```

Then reboot:

```bash
sudo reboot
```

Then install the 1-wire sensors and make sure they are there.

```bash
sudo modprobe w1-gpio
sudo modprobe w1-therm
ls -la /sys/bus/w1/devices
```

You should see something like this with different numbers:

```text
28-3c01f0965030  28-60d70d1864ff  w1_bus_master1
```

The actual serial number(s) to remember is everything after the '28-'.

### Make the folder:

```bash
cd /opt
sudo mkdir ThermoPI-Furnace
sudo chown [your user name here] ./ThermoPI-Furnace
sudo chgrp [your user name here] ./ThermoPI-Furnace
```

### Get the software:

```bash
git clone https://github.com/SirGoodenough/ThermoPI-Furnace.git
cd ThermoPI-Furnace
```

### Generate your version of the MYsecrets.yaml

Based on the MYsecretsSample.yaml as a starting point, make your own.  You will need to have figured out your 1-wire sensor serial numbers and know your MQTT login information to complete this section.

```bash
cp MYsecretsSample.yaml MYsecrets.yaml
nano MYsecrets,yaml
```

### Test that everything works

Troubleshoot as needed.  'MQTT Update result 0' means it went well.

```bash
/usr/bin/python3 /opt/ThermoPI-Furnace/furnace.py
```


This is roughly the circuit used with this program:
![Sample Circuit matching this software](ThermoPI-Furnace.png)

### Contact Links

+ [Discord WhatAreWeFixingToday](https://discord.gg/Uhmhu3B)
+ [What are we Fixing Today Homepage](https://www.WhatAreWeFixing.Today/)
+ [YouYube Channel Link](https://bit.ly/WhatAreWeFixingTodaysYT)
+ [What are we Fixing Today Facebook page](https://bit.ly/WhatAreWeFixingTodayFB)
+ [What are we Fixing Today Twitter](https://bit.ly/WhatAreWeFixingTodayTW)

### Please help support the channel

+ [Patreon Membership](https://www.patreon.com/WhatAreWeFixingToday)
+ [Buy me Coffee](https://www.buymeacoffee.com/SirGoodenough)
+ [PayPal one-off donation link](https://www.paypal.me/SirGoodenough)

## Disclaimer

⚠️ **DANGER OF ELECTROCUTION** ⚠️

If your device connects to mains electricity (AC power) there is danger of electrocution if not installed properly. If you don't know how to install it, please call an electrician.

#### **Beware:** certain countries prohibit installation without a licensed electrician present

Remember: **SAFETY FIRST**. It is not worth the risk to yourself, your family and your home if you don't know exactly what you are doing. Never tinker or try to flash a device using the serial programming interface while it is connected to MAINS ELECTRICITY (AC power).

We don't take any responsibility nor liability for using this software nor for the installation or any tips, advice, videos, etc. given by any member of this site or any related site.
