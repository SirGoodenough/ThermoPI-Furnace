# ThermoPI-Furnace

Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server.

## USAGE

Install the program into opt/ThermoPI-Furnace or any suitable location. (Some people like /usr/local/bin instead of /opt) Make sure the username that is going to be running this script has access to the files and is able to get at python and anything else needed and used here-in.

You will need to rename the file ***MYsecretsSample.yaml*** to ***MYsecrets.yaml***.
Edit the contents of the new ***MYsecrets.yaml*** to match your MQTT & Home Assistant installation and requirements. You will also need to supply the full path to the secrets file in the **Get the parameter file** section of this python code around line 225.

This program grabs the 2nd half of the MAC address to use as the device ID. This only works consistently when there is only 1 Ethernet interface configured or you have your multiple interfaces cloned to the same MAC Address. For instance if it boots from WIFI, it will grab that MAC, and if it uses the Ethernet cable or a USB interface, it will grab that MAC. You get my point. This can be avoided by hard coding the DeviceID with the random and unique number of your choice. Also I have not tested this with IP6 addresses. If you have solutions to any of this, please share.

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
cd /opt
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

Troubleshoot as needed.  'MQTT Update result 0' means that part of the loop went well.  After you get it to loop thru a couple of times, use 'ctrl-c' to stop it and continue to next step.

```bash
/usr/bin/python3 /opt/ThermoPI-Furnace/furnace.py
```

### Auto Start

Long term use of this software will make too many writes to the SD card, filling it up and wearing out the card.  Therefore ``` > /dev/null 2>&1``` has been added to the ```thermoPIFurnace.service``` file to reduce writes to the SD card.  For Troubleshooting you *MAY* want to turn this off temporarily. Just remove those characters from this file and all will be logged. Be sure to turn this on or off as you desire before running this section, or if you change that file re-run this section. Frankly I prefer stopping the application ```sudo systemctl stop thermoPIFurnace.service``` and running it manually like above for troubleshooting.  Then restarting it when done ```sudo systemctl start thermoPIFurnace.service```.

The line 'User=XXX' in the file ```thermoPIFurnace.service``` needs to be edited to match the username that will be running the application.  Running as Root is *HIGHLY DISCOURAGED*.

```bash
/opt/ThermoPI-Furnace/load-service.sh
```

You should see similar to this:

```text
furnacepi@furnpi:/opt/ThermoPI-Furnace $ ./load-service.sh
Stopping ThermoPI-Furnace
Failed to stop thermoPIFurnace.service: Unit thermoPIFurnace.service not loaded.
Copy file over
Change permissions on new file
Reload the systemd daemon
Enable the new service
Created symlink /etc/systemd/system/multi-user.target.wants/thermoPIFurnace.service → /lib/systemd/system/thermoPIFurnace.service.
Start the new service
Check that the new service is running
● thermoPIFurnace.service - ThermoPI-Furnace Status Reader
     Loaded: loaded (/lib/systemd/system/thermoPIFurnace.service; enabled; vendor preset: enabled)
     Active: active (running) since Sun 2023-01-22 14:02:40 CST; 7s ago
   Main PID: 1267 (python3)
      Tasks: 3 (limit: 1596)
        CPU: 1.242s
     CGroup: /system.slice/thermoPIFurnace.service
             └─1267 /usr/bin/python3 /opt/ThermoPI-Furnace/furnace.py > /dev/null 2>&1

Jan 22 14:02:40 furnpi systemd[1]: Started ThermoPI-Furnace Status Reader.
```

### Instructions for Setting Up ThermoPI-Furnace with a venv  (Auto Start)

These instructions assume you have Python 3.7 or later installed.
**WARNING** These venv instructions are LLM Generated and have not been fully
  tested yet. Verification and debug is in progress. Use at your own risk...

These instructions assume you’re running the ThermoPI-Furnace on a Raspberry Pi and need it to start automatically when the Pi boots.

**1. Prerequisites:**

*   **Raspberry Pi:** You’ll need a Raspberry Pi running a recent OS (Raspberry Pi OS is recommended).
*   **Git:** Ensure Git is installed on the Pi.
*   **SSH:** You'll need SSH access to the Pi to perform the setup.

**2. Create and Activate the venv (on the Pi - via SSH):**

*   **Connect to the Pi via SSH:** Use your terminal or SSH client to connect to the Raspberry Pi.
*   **Create the venv:**

    ```bash
    python3 -m venv .venv
    ```

*   **Activate the venv:**

    ```bash
    source .venv/bin/activate
    ```

    *   This needs to be run *every* time the Pi boots, so we’ll automate this.

**3. Clone the Repository (on the Pi - via SSH):**

*   Make the Folder and Clone the repository as listed above

*   **Navigate to the project directory:**

    ```bash
    cd ThermoPI-Furnace
    ```

**4. Install Dependencies (on the Pi - via SSH):**

*   **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

**5. Configuration (Important!) (on the Pi - via SSH):**

*   **Modify `config.ini`:** This is crucial. Ensure you have:
    *   `device_address`: Your Pi's IP address.
    *   `port`: The port number.
    *   `relay_names`:  Relay names.
    *   `sensor_names`: Sensor names.
    *   `device_name`: Device name.

    *   **Remember to save this file after making changes.**

**6. Automating Startup at Boot (on the Pi - via SSH):**

This is the key change for an automatic setup. We'll use systemd, the standard init system for Linux.

*   **Create a systemd service file:**

    ```bash
    sudo nano /etc/systemd/system/thermopifurnace.service
    ```

*   **Paste the following content into the file:**

    ```
    [Unit]
    Description=ThermoPI-Furnace Status Reader
    After=multi-user.target network.target

    [Service]
    User=furnacepi
    Type=simple
    WorkingDirectory=/opt/ThermoPI-Furnace # or the actual location
    ExecStart=/opt/ThermoPI-Furnace/furnace.py > /dev/null 2>&1  # Full path to your script
    KillSignal=SIGINT
    Restart=always
    RestartSec=10
    SyslogIdentifier=ThermoPI-Furnace
    StandardOutput=journal
    StandardError=journal

    [Install]
    WantedBy=multi-user.target
    ```

    *   **Important:**  Adjust the `User`, `WorkingDirectory`, and `ExecStart` lines to match *your* specific setup. The `User` should be the user that owns the `ThermoPI-Furnace` directory.
    *   `Restart=on-failure` ensures the script restarts if it crashes.
    *   `StandardOutput=journal` and `StandardError=journal` send the output of the script to the systemd journal.

*   **Save the file** (Ctrl+X, Y, Enter).

*   **Enable and start the service:**

    ```bash
    sudo systemctl enable thermopifurnace.service
    sudo systemctl start thermopifurnace.service
    ```

*   **Check the status:**

    ```bash
    sudo systemctl status thermopifurnace.service
    ```

    This will show you if the service is running, any errors, and recent output from the script.

**7. Verify:**

*   Reboot the Raspberry Pi (`sudo reboot`).
*   After the reboot, check if the ThermoPI-Furnace script is running using: `sudo systemctl status thermopifurnace.service`. 

**Key Considerations:**

*   **Systemd:**  This setup relies on systemd to manage the ThermoPI-Furnace script as a service.
*   **User:**  Running the script as a specific user (e.g., `pi`) is more secure than running it as root.
*   **Full Paths:** Always use full paths to files and executables in systemd service files.
*   **Journaling:** Using `journalctl` is crucial for debugging issues.

This detailed setup provides a robust foundation for running the ThermoPI-Furnace automatically on your Raspberry Pi.  Remember to adjust the paths and settings to match your specific configuration.


### Home Assistant

After it's running head to home assistant devices [![Open your Home Assistant instance and show your devices.](https://my.home-assistant.io/badges/devices.svg)](https://my.home-assistant.io/redirect/devices/) and look for ```ThermoPI Furnace```.  That is your list of sensors which you can do with as any other sensor.

![Sample Home Assistant Screen](HA-Screenshot.png)

### Schematic

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
