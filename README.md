Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server and execute a binary-sensor to a GPIO pin.

![Version](https://img.shields.io/github/v/release/SirGoodenough/ThermoPI-Furnace) [![Community Forum](https://img.shields.io/badge/community-forum-orange.svg?style=for-the-badge)](https://community.home-assistant.io/t/raspi-python-mqtt-sensor-array-for-home-assistant/982594) [![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-gold)](https://github.com/SirGoodenough/ThermoPI-Furnace/)

[![GitHub issues](https://img.shields.io/github/issues-raw/SirGoodenough/ThermoPI-Furnace?style=for-the-badge)](https://github.com/SirGoodenough/ThermoPI-Furnace/issues?q=is%3Aopen+is%3Aissue) [![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/SirGoodenough/ThermoPI-Furnace?style=for-the-badge)](https://github.com/SirGoodenough/ThermoPI-Furnace/issues?q=is%3Aissue+is%3Aclosed) [![GitHub contributors](https://img.shields.io/github/contributors/SirGoodenough/ThermoPI-Furnace?style=for-the-badge)](https://github.com/SirGoodenough/ThermoPI-Furnace/graphs/contributors)

# ThermoPI-Furnace

This was born before ESPHome was a thing, but the number of sensors and controls at this point seems a bit more than I would like to depend on an ESP32 for.

I recently adapted this to work with a venv within the newer RasPI operating systems and updated everything to use just the pigpio library eliminating a bunch of unnecessary component loading.

In short there is a couple of thermocouples, Dallas sensors, and DHT22 sensors here along with an MQTT controlled output pin to interface my (oil) fired furnace and a wood pellet stove.

## ```|USER|``` FILE CHANGES

Here is a complete list of all the files that need to be edited to represent your user name an/or your home folder path for this to work. Most of the changes you will be looking for the key ```|user|``` and replace it with your username.

+ load-service.sh
+ MYsecrets.yaml (copied & edited from MYsecretsSample.yaml)
+ startThermoPI.sh
+ thermoPIFurnace.service
+ verboseThermoPI.sh
+ all folder permissions in the executable file's path

## USAGE

Install the program into ~/.ThermoPI/ThermoPI-Furnace/ or any suitable location. Make sure the username that is going to be running this script has access to the files and is able to get at python and anything else needed and used here-in. Use of a venv as described below is highly recommended.

If you see this error:
> FileNotFoundError: [Errno 2] No such file or directory: '/home/|user|/.ThermoPI/ThermoPI-Furnace/MYsecrets.yaml'

You will need to rename the file ***MYsecretsSample.yaml*** to ***MYsecrets.yaml***.
Edit the contents of the new ***MYsecrets.yaml*** to match your MQTT & Home Assistant installation and requirements.

You will need to supply the full path to the MYsecrets.yaml file in the startThermoPI.sh and verboseThermoPI.sh shell scripts. That path is a commandline input for furnace.py.

This program grabs the 2nd half of the MAC address to use as the device ID. This only works consistently when there is only 1 Ethernet interface configured or you have your multiple interfaces cloned to the same MAC Address. For instance if it boots from WIFI, it will grab that MAC, and if it uses the Ethernet cable or a USB interface, it will grab that MAC. You get my point. This can be avoided by hard coding the DeviceID with the random and unique number of your choice. Also I have not tested this with IP6 addresses. If you have solutions to any of this, please share.

## AUTO-Start

Here is a good reference on setting up a program to run from systemd. Use it to get familiar with the process.

[How-To Geek on 'Startup With Systemd'](https://www.howtogeek.com/687970/how-to-run-a-linux-program-at-startup-with-systemd/)

To run the program at boot in order to get constant readings, there is the ThermoPIFurnace.service to run this as a service with load-service.sh there to set it up as a service. More detail in [Installation - Section 8](#8.-automating-startup-at-boot) below.

The load-service.sh script will stop and scratch reload the service from the local repository (Once you get all the permissions happy).

The furnRestart.sh is the script to quickly restart the process if needed during troubleshooting. I found it helpful.

The startThermoPI.sh shell script starts the venv and run the program inside the venv so that all the requirements are there. Use this if running in a venv.

The verboseThermoPI.sh shell script does the same as startThermoPI.sh but enables verbose mode.

## Requirements

Program requirements (as written):  (Feel free to fork it & update any obsolete Libraries and dropping me a merge request...)

+ Python 3.11 or better
+ [paho-mqtt](https://pypi.org/project/paho-mqtt/) For MQTT broker connection
+ [PyYAML](https://pypi.org/project/PyYAML/) For reading the YAML parameter file
+ [pigpio](https://abyz.me.uk/rpi/pigpio/index.html) For reading the Thermocouples (MAX6675)

+ [max6675](https://github.com/tdack/MAX6675) Thermocouple demux code
+ [DS18B20](https://randomnerdtutorials.com/raspberry-pi-ds18b20-python/) pigpio interface.

**If you have any questions, comments or additions be sure to add an issue and bring them up on my Discord Server:**

## Installation

### 1. Prerequisites:

Suggested image for your PI is the latest 64bit lite. You can use the regular load if you are using the PI for other things, but none of the gui functions are needed.  The Raspi imager software also lets you set up name, password, timezone, and start the ssh server on image load, so do those things.  After it boots log in and update-upgrade it to get all the packages up to date.  Reboot...

*   **SSH:** You'll need SSH access to the Pi to perform the setup.
Use raspi-config to set up localization. In the 'Interface Options' enable 'Remote GPIO' and I2C. You may want to add other things.
*   **Python3:** A version of Python3 3.11 or newer is required.
*   **Raspberry Pi:** You’ll need a Raspberry Pi running a recent OS (Raspberry Pi OS is recommended).

These instructions assume you’re running the ThermoPI-Furnace on a Raspberry Pi and need it to start automatically when the Pi boots. We will be using a venv so it works with the more recent OS versions.

### 2. Create and Activate the venv (on the Pi - via SSH):

> SOURCE: https://forums.raspberrypi.com/viewtopic.php?t=330651#p1979605

*   **Connect to the Pi via SSH:** Use your terminal or SSH client to connect to the Raspberry Pi.
*   **Create the venv and install git:**

    ```bash
    sudo apt-get update
    sudo apt-get install python3.11-venv git
     [sudo] password for |user| ....
    python3 -m venv /home/|user|/.ThermoPI
    ```

*   **Activate the venv:**

    ```bash
    source /home/|user|/.ThermoPI/bin/activate
    ```

    * NOTE: The venv will need to be activated *every* time the python program runs (at boot or restart), so we’ll automate this using a shell script to start the python code. To leave the venv and return to regular command mode, the command is ```deactivate```.

### 3. Update PIP  * NOTE: Do this while logged into the venv

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

### 4. Install the requirements  * NOTE: Do this while logged into the venv

    * NOTE: paho-mqtt is pinned at 1.6.0 because of a config issue I couldn't figure out.

```bash
pip3 uninstall paho-mqtt
pip3 install PyYAML pigpio paho-mqtt==1.6.0
```

### 5. Install the 1 wire devices

**NOTE:** Be sure to note the serial numbers of the sensors and know where each sensor is physically located.

```bash
sudo nano /boot/firmware/config.txt
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
ls /sys/bus/w1/devices
```

You should see something like this with different numbers:

```text

28-3c01f0965030  28-60d70d1864ff  w1_bus_master1

```

The actual serial number(s) to remember are the '28-xxxxxxxxxxxx'.

### 5. Get the software:  * NOTE: Do this while logged into the venv

Change |user| to your user name.

```bash
cd /home/|user|/.ThermoPI
git clone https://github.com/SirGoodenough/ThermoPI-Furnace.git
cd ThermoPI-Furnace
```

### 6. Generate your version of the MYsecrets.yaml  * NOTE: Do this while logged into the venv

Based on the MYsecretsSample.yaml as a starting point, make your own.  You will need to have figured out your 1-wire sensor serial numbers, where they are located, and know your MQTT login information to complete this section.

```bash
cp MYsecretsSample.yaml MYsecrets.yaml
nano MYsecrets.yaml
```

### 7. Test that everything works  * NOTE: Do this while logged into the venv.

Be sure to change |user| to your user name.
Troubleshoot as needed.  'MQTT Update result 0' means that part of the loop went well.  After you get it to loop thru a couple of times, use 'ctrl-c' to stop it and continue to next step.

```bash
/usr/bin/python3 /home/|user|/.ThermoPI/ThermoPI-Furnace/startThermoPI.sh
```

### 8. Automating Startup at Boot  * NOTE: Do this while logged into the venv

Long term use of this software will make too many writes to the SD card, filling it up and wearing out the card. Therefore ```> /dev/null 2>&1``` has been added to the ```thermoPIFurnace.service``` file to reduce writes to the SD card. For Troubleshooting you *MAY* want to turn this off temporarily. Just remove those characters from this file and all will be logged. Be sure to turn this on or off as you desire before running this section, or if you change that file re-run this section.

These 4 lines containing '|user|' in the file ```thermoPIFurnace.service```
> User=|user|
> Group=|user|
> WorkingDirectory=/home/|user|/.ThermoPI/ThermoPI-Furnace
> ExecStart=/home/|user|/.ThermoPI/ThermoPI-Furnace/startThermoPI.sh
need to be edited to match the username & path that will be running the application. Running as Root is *HIGHLY DISCOURAGED*.
Also all directories leading to the executable file need to have the permissions ```755``` for the systemctl process to find it properly.

The shell script ```load-service.sh``` should be run every time after you edit ```thermoPIFurnace.service``` to install the changes, unless you want to push the changes manually to systemctl.

You should see similar to this as it runs:
```bash
Should be run as sudo...

Stopping ThermoPI-Furnace
Copy file over
Change permissions on new file
Reload the systemd daemon
Enable the new service
Start the new service
Check that the new service is running
● thermoPIFurnace.service - ThermoPI-Furnace Status Reader
     Loaded: loaded (/lib/systemd/system/thermoPIFurnace.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-01-19 21:54:47 CST; 7s ago
   Main PID: 6269 (startThermoPI.s)
      Tasks: 8 (limit: 760)
        CPU: 1.070s
     CGroup: /system.slice/thermoPIFurnace.service
             ├─6269 /bin/bash /home/|user|/.ThermoPI/ThermoPI-Furnace/startThermoPI.sh ">" /dev/null "2>&1"
             ├─6273 python furnace.py
             ├─6274 /home/|user|/.ThermoPI/lib/python3.11/site-packages/adafruit_blinka/microcontroller/bcm283x/pulseio/libgpiod>
             └─6276 /home/|user|/.ThermoPI/lib/python3.11/site-packages/adafruit_blinka/microcontroller/bcm283x/pulseio/libgpiod>

Jan 19 21:54:47 thermopifurn systemd[1]: Started thermoPIFurnace.service - ThermoPI-Furnace Status Reader.
Jan 19 21:54:47 thermopifurn startThermoPI.sh[6270]: /usr/bin/python
Jan 19 21:54:47 thermopifurn startThermoPI.sh[6269]: /home/|user|/.ThermoPI/ThermoPI-Furnace
Jan 19 21:54:47 thermopifurn startThermoPI.sh[6271]: /home/|user|/.ThermoPI/bin/python
```

## Verify Installation  * NOTE: Do this while logged into the venv

*   Reboot the Raspberry Pi (`sudo reboot`).
*   After the reboot, check if the ThermoPI-Furnace script is running using: `sudo systemctl status thermopifurnace.service`.
*   Assuming proper function at this point I suggest making sure the logging is off as per the instructions in Installation-section 8 above.

## Home Assistant

After it's running head to home assistant devices [![Open your Home Assistant instance and show your devices.](https://my.home-assistant.io/badges/devices.svg)](https://my.home-assistant.io/redirect/devices/) and look for ```ThermoPI Furnace```.  That is your list of sensors which you can do with as any other sensor.

![Sample Home Assistant Screen](HA-Screenshot.png)

To control the GPIO pin selected look at this blueprint:
HA link to download blueprint: [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSirGoodenough%2FHA_Blueprints%2Fblob%2Fmaster%2FScripts%2Fpellet_disable.yaml)

Direct link to  download Blueprint: ```https://github.com/SirGoodenough/HA_Blueprints/blob/master/Scripts/pellet_disable.yaml```

If you want to talk to the GPIO pin without a blueprint, see this code:

```yaml
#####################################################
# Pellet Feed Control                               #
#####################################################
# Scripts:

pellet_feed_off:
  alias: disable Pellet Feed
  sequence:
    - alias: Make sure fan is off
      action: mqtt.publish
      data:
        topic: 'homeassistant/binary_sensor/107935_pel_stove_disable/state'
        payload: 0

pellet_feed_on:
  alias: enable Pellet Feed
  sequence:
    - alias: Make sure fan is on
      action: mqtt.publish
      data:
        topic: 'homeassistant/binary_sensor/107935_pel_stove_disable/state'
        payload: 1

pellet_disable_script:
  alias: Enable or Disable the Pellet Stove pellet feed
  trace:
    stored_traces: 10
  fields:
    control:
      name: Control State
      description: Set to true to shut off pellets, false to restore normal operation.
      required: false
      example: "false"
      default: false
      selector:
        boolean:
  sequence:
    - alias: et the state
      action: mqtt.publish
      data:
        topic: 'homeassistant/binary_sensor/107935_pel_stove_disable/state'
        payload: >
          {{ iif(control, 1, 0, 0)}}
# Automation:

- id: '54069466-8ec0-4432-a003-a725ccf4afcd'
  alias: Fire Break
  description: Shut off the pellets if the timer is going.
  triggers:
  - trigger: state
    entity_id:
    - timer.fire15
    from:
    - idle
    to:
    - active
    id: Stall
  - trigger: state
    entity_id:
    - timer.fire30
    from:
    - idle
    to:
    - active
    id: Stall
  - trigger: state
    entity_id:
    - timer.fire45
    from:
    - idle
    to:
    - active
    id: Stall
  - trigger: state
    entity_id:
    - timer.fire60
    from:
    - idle
    to:
    - active
    id: Stall
  - trigger: state
    entity_id:
    - timer.fire15
    from:
    - active
    to:
    - idle
    id: Run
  - trigger: state
    entity_id:
    - timer.fire30
    from:
    - active
    to:
    - idle
    id: Run
  - trigger: state
    entity_id:
    - timer.fire45
    from:
    - active
    to:
    - idle
    id: Run
  - trigger: state
    entity_id:
    - timer.fire60
    from:
    - active
    to:
    - idle
    id: Run
  conditions: []
  actions:
  - choose:
    - conditions:
      - condition: trigger
        id:
        - Stall
      sequence:
      - action: script.pellet_feed_enable
        metadata: {}
        data:
          control: true
    - conditions:
      - condition: trigger
        id:
        - Run
      sequence:
      - action: script.pellet_feed_enable
        metadata: {}
        data:
          control: false
    default:
    - action: script.pellet_feed_enable
      metadata: {}
      data:
        control: false
  mode: single
```

## Schematic

This is roughly the circuit used with this program:

![Sample Circuit matching this software](ThermoPI-Furnace.png)

## Contact Links

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
