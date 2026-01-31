#!/usr/bin/python3

import pigpio  # https://abyz.me.uk/rpi/pigpio/index.html
import DHT     # Code included from DHT.py and pigpio library
from w1thermsensor import W1ThermSensor, Sensor
import paho.mqtt.client as mqtt
import sys
import time
import yaml
import json
import uuid
import random

# 2 Command line arguments available: 
#  * {REQUIRED} Text Path pointing to the location of MYsecrets.yaml.
#     The last Text argument (not verbose) found will be attempted to be used as the path.
#     Default is /home/|user|/.ThermoPI/ThermoPI-Furnace/MYsecrets.yaml
#      where you change |user| to your user name.
#  * {Optional} The word "verbose or --verbose" turns on verbose troubleshoot mode.

argc = len(sys.argv) # get number of command line arguments

if argc < 2:
    print("Need to specify the path to the MYsecrets.yaml as argument")
    print(" in the shell script starting the venv and calling furnace.py")
    print(" similar to: /home/|user|/.ThermoPI/ThermoPI-Furnace/MYsecrets.yaml")
    exit()

verbose = False  # Set False as default quiet mode if no CL argument for it.

for i in range(1, argc): # ignore first argument which is command name
    if (sys.argv[i] == "verbose") or (sys.argv[i] == "--verbose"):
        verbose = True
    else:
        # Assume this is the path to the MYsecrets.yaml file (last one wins)
        with open(sys.argv[i], "r") as ymlfile:
            MYs = yaml.safe_load(ymlfile)

# Subroutine to look up temp/humid sensors
def tempHumid():
    global pi
    global list
    global count
    global temp
    global humidity
    try:
        _d = DHT.sensor(pi, list[count]).read()
        _status = _d[2]
        _tempC = _d[3]
        _humidityI = _d[4]
        _wStatus = ("DHT_GOOD:0", "DHT_BAD_CHECKSUM:1", "DHT_BAD_DATA:2", "DHT_TIMEOUT:3")
        """
            The returned data (_d) is a tuple of timestamp, GPIO, status,
            temperature, and humidity.

            The status will be one of:
            0 DHT_GOOD (a good reading)
            1 DHT_BAD_CHECKSUM (received data failed checksum check)
            2 DHT_BAD_DATA (data received had one or more invalid values)
            3 DHT_TIMEOUT (no response from sensor)
        """
        if _status != 0 or _humidityI is None or _humidityI > 100.0 or _tempC is None or _tempC > 150.0 or _tempC < 4.44:
            print('Status: {0} Bad Reading {1} {2}'.format(_wStatus[_status], _tempC, _humidityI))
            return

        temp = round((9.0/5.0 * _tempC + 32.0), 1)  # Conversion to F & round to .1
        humidity = round(_humidityI, 1)             # Round to .1

        if verbose: # Troubleshooting print
            print("{:.3f} {:2d} {} {:3.1f} F {:3.1f} %".format(_d[0], _d[1], _wStatus[_d[2]], temp, humidity))
    except RuntimeError as _e:
        # Errors happen fairly often, DHT's are hard to read, just try again
        print('DHT reading error: ' + str(_e.args[0]))
        print('Status: {0} Bad Reading {1} {2}'.format(_wStatus[_status], _tempC, _humidityI))
        pass
        # Skip to the next reading if a valid measurement couldn't be taken.
        # This might happen if the CPU is under a lot of load and the sensor
        # can't be reliably read (timing is critical to read the sensor).

# Subroutine look up 1 Wire temp(s)
def W1():
    global temp
    global sensor
    global list
    global count

    _tempC = 0.0
    _tF = 0.0

    # sensor = W1ThermSensor()
    sensor = W1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=list[count])

    # Get the temp
    _tempC = sensor.get_temperature()
    # Test the result.  Make sure it is reasonable and not a glitch.
    if _tempC is None or _tempC > 120.0 or _tempC < 4.44:
        return
    # Conversion to F & round to .1
    _tF = round((9.0/5.0 * _tempC + 32.0), 1)       # Round to .1
    if verbose: # Troubleshooting print
        print('1-Wire Temp: {0:0.1f} F'.format(_tF))
    # Done
    temp = _tF

# Subroutine look up thermocouple temps
def thermocouple():
    global temp
    global pi
    global list
    global count

    _tempC = 0.0
    _tF = 0.0
    _d = 0
    _c = 0
    _word = 0

    # Check the thermocouple(s) on the Serial links.
    _sensor = pi.spi_open(list[count], 1000000, 0)
    _c, _d = pi.spi_read(_sensor, 2)
    pi.spi_close(_sensor)

    if _c == 2:
        _word = (_d[0] << 8) | _d[1]
        if (_word & 0x8006) == 0:  # Bits 15, 2, and 1 should be zero.
            _tempC = (_word >> 3)/4.0
            # Test the result
            if _tempC is None or _tempC > 1500.0 or _tempC < 4.44:
                return
            # Conversion to F & round to .1
            _tF = round((9.0/5.0 * _tempC + 32.0), 1)
            if verbose: # Troubleshooting print
                print("Thermocouple Temp: {:.2f} F".format(_tF))
        else:
            print('bad reading {:b}'.format(_word))
            return
        # Done
        temp = _tF

# subroutine to set the pellet feed on-off
def disablePelletFeed(_state):
    global pi
    global client
    global state_topic
    global PIN_CTL1

    # This operates GPIO(PIN_CTL1) connected to an NC relay contact,
    #   default (0) is to allow normal operation.
    #   setting to 1 disables the pellet feed.
    #   setting to 10 is used to force the HA toggle OFF in addition to GPIO off.

    if _state == 1:
        pi.write(PIN_CTL1, 1)  # Turn OFF the pellet feed
    elif _state == 10:
        client.publish(state_topic[0], 0, 1, True) # Ensure HA Toggle matches relay state
        if verbose: # Troubleshooting print
            print('HA Pellet feed disable state set to OFF')
    else:
        pi.write(PIN_CTL1, 0)  # Set the pellet feed to internal normal operation

    if verbose: # Troubleshooting print
        print('GPIO {0} set to {1}'.format(PIN_CTL1, pi.read(PIN_CTL1)))

# Subroutine to send results to MQTT
def mqttSend():
    global temp
    global humidity
    global client
    global count
    global state_topic
    global LWT

    if temp == 0.0:
        return

    try:
        _payloadOut = {
            "temperature": temp,
            "humidity": humidity}
        _OutState = state_topic[count]

        (_result1,mid) = client.publish(_OutState, json.dumps(_payloadOut), 1, True)

        if verbose: # Troubleshooting print
            _currentdate = time.strftime('%Y-%m-%d %H:%M:%S')
            print('Updating {0} {1}'.format(_OutState,json.dumps(_payloadOut) ) )
            print('Date Time:   {0}'.format(_currentdate))
            print('MQTT Update result {0}'.format(_result1))

        if _result1 == 1:
            raise ValueError('Result message from MQTT was not 0')

    except Exception as _e:
        # Error appending data, most likely because credentials are stale.
        #  disconnect and re-connect...
        print('MQTT error, trying re-connect: ' + str(_e))
        client.loop_stop()
        client.unsubscribe(state_topic[0])
        time.sleep(2)
        client.publish(LWT, 'Offline', 1, True)
        client.disconnect()
        time.sleep(2)
        mqttConnect()
        pass

# Subroutine to connect to MQTT
#  Thanks to help from http://www.steves-internet-guide.com/into-mqtt-python-client/
def mqttConnect():
    global client
    global state_topic
    global HOST
    global PORT
    global USER
    global PWD
    global LWT
    global CONFIGH_TH1
    global CONFIGT_TH1
    global CONFIGH_TH2
    global CONFIGT_TH2
    global CONFIG_W13
    global CONFIG_W14
    global CONFIG_TC5
    global CONFIG_TC6
    global CONFIG_CTL1
    global payloadH_TH1config
    global payloadT_TH1config
    global payloadH_TH2config
    global payloadT_TH2config
    global payload_W13config
    global payload_W14config
    global payload_TC5config
    global payload_TC6config
    global payload_CTL1config

    print('Connecting to MQTT on {0} {1}'.format(HOST,PORT))
    client.disable_logger()  # Saves wear on SD card Memory.  Remove as needed for troubleshooting
    client.username_pw_set(USER, PWD) # deactivate if not needed
    client.on_message=on_message #attach function to callback
    client.connect(HOST, PORT, keepalive=60)
    client.loop_start()
    client.publish(LWT, "Online", 1, True)
    client.publish(CONFIGH_TH1, json.dumps(payloadH_TH1config), 1, True)
    client.publish(CONFIGT_TH1, json.dumps(payloadT_TH1config), 1, True)
    client.publish(CONFIGH_TH2, json.dumps(payloadH_TH2config), 1, True)
    client.publish(CONFIGT_TH2, json.dumps(payloadT_TH2config), 1, True)
    client.publish(CONFIG_W13, json.dumps(payload_W13config), 1, True)
    client.publish(CONFIG_W14, json.dumps(payload_W14config), 1, True)
    client.publish(CONFIG_TC5, json.dumps(payload_TC5config), 1, True)
    client.publish(CONFIG_TC6, json.dumps(payload_TC6config), 1, True)

    client.publish(CONFIG_CTL1, json.dumps(payload_CTL1config), 1, True)
    client.subscribe(state_topic[0], 2) #subscribe to the disable pellet feed topic

# MQTT message callback & Write GPIO to disable/enable pellet feed
#  Thanks to help from http://www.steves-internet-guide.com/into-mqtt-python-client/
def on_message(_client, _userdata, _message):
    try:
        _result = int(_message.payload.decode('utf-8')) 

        if verbose: # Troubleshooting print
            print('message received: ' + str(_result))
            print('message topic=',_message.topic)
            print('message qos=',_message.qos)
            print('message retain flag=',_message.retain)

        # Set the GPIO pin to disable or enable the pellet feed
        if  isinstance(_result, int):
            disablePelletFeed(_result)
        else:
            disablePelletFeed(0)

    except RuntimeError as _e:
        # Missing data in the subscribed topic
        print('Subscriber error: ' + str(_e.args[0]))
        print('message received: ' + str(_result))
        print('message topic=',_message.topic)
        print('message qos=',_message.qos)
        print('message retain flag=',_message.retain)
        pass

# Read parameters from MYsecrets.yaml
LOOP = MYs["MAIN"]["LOOP"]
HOST = MYs["MAIN"]["HOST"]
PORT = MYs["MAIN"]["PORT"]
USER = MYs["MAIN"]["USER"]
PWD = MYs["MAIN"]["PWD"]
AREA = MYs["MAIN"]["AREA"]
if verbose: # Troubleshooting print
    print("LOOP = %s" % LOOP)
    print("HOST = %s" % HOST)
    print("PORT = %s" % PORT)
    print("USER = %s" % USER)
    print("PWD = %s" % PWD)
    print("AREA = %s" % AREA)
    print("===============================")

# Pulling the unique MAC SN section address using uuid and getnode() function 
DEVICE_ID = (hex(uuid.getnode())[-6:]).upper()

TOPIC = "homeassistant/sensor/"
BSTOPIC = "homeassistant/binary_sensor/"

NAMED = MYs["MAIN"]["DEVICE_NAME"]
D_ID = DEVICE_ID + '_' + NAMED
LWT = TOPIC + D_ID + '/lwt'
if verbose: # Troubleshooting print
    print("DEVICE_ID = %s" % DEVICE_ID)
    print("TOPIC = %s" % TOPIC)
    print("BSTOPIC = %s" % BSTOPIC)
    print("NAMED = %s" % NAMED)
    print("D_ID = %s" % D_ID)
    print("LWT = %s" % LWT)
    print("===============================")

# Create MQTT client
client_id = f'{D_ID}-mqtt-{random.randint(0, 1000)}'
client = mqtt.Client(client_id)
if verbose: # Troubleshooting print
    print("client_id = %s" % client_id)
    print("client = %s" % client)
    print("===============================")

PIN_TH1 = int(MYs["TEMP_HUMID"]["PIN_TH1"])
NAMEH_TH1 = MYs["TEMP_HUMID"]["NAMEH_TH1"]
H_TH1_ID =  DEVICE_ID + '_' + MYs["TEMP_HUMID"]["H_TH1_ID"]
CONFIGH_TH1 = TOPIC + H_TH1_ID + '/config'
TH1_STATE = TOPIC + H_TH1_ID + '/state'
if verbose: # Troubleshooting print
    print("PIN_TH1 = %s" % PIN_TH1)
    print("NAMEH_TH1 = %s" % NAMEH_TH1)
    print("H_TH1_ID = %s" % H_TH1_ID)
    print("CONFIGH_TH1 = %s" % CONFIGH_TH1)
    print("TH1_STATE = %s" % TH1_STATE)
    print("===============================")

NAMET_TH1 = MYs["TEMP_HUMID"]["NAMET_TH1"]
T_TH1_ID = DEVICE_ID + '_' + MYs["TEMP_HUMID"]["T_TH1_ID"]
CONFIGT_TH1 = TOPIC + T_TH1_ID + '/config'
if verbose: # Troubleshooting print
    print("NAMET_TH1 = %s" % NAMET_TH1)
    print("T_TH1_ID = %s" % T_TH1_ID)
    print("CONFIG_T_TH1 = %s" % CONFIGT_TH1)
    print("===============================")

PIN_TH2 = int(MYs["TEMP_HUMID"]["PIN_TH2"])
NAMEH_TH2 = MYs["TEMP_HUMID"]["NAMEH_TH2"]
H_TH2_ID =  DEVICE_ID + '_' + MYs["TEMP_HUMID"]["H_TH2_ID"]
CONFIGH_TH2 = TOPIC + H_TH2_ID + '/config'
TH2_STATE = TOPIC + H_TH2_ID + '/state'
if verbose: # Troubleshooting print
    print("PIN_TH2 = %s" % PIN_TH2)
    print("NAMEH_TH2 = %s" % NAMEH_TH2)
    print("H_TH2_ID = %s" % H_TH2_ID)
    print("CONFIGH_TH2 = %s" % CONFIGH_TH2)
    print("TH2_STATE = %s" % TH2_STATE)
    print("===============================")

NAMET_TH2 = MYs["TEMP_HUMID"]["NAMET_TH2"]
T_TH2_ID = DEVICE_ID + '_' + MYs["TEMP_HUMID"]["T_TH2_ID"]
CONFIGT_TH2 = TOPIC + T_TH2_ID + '/config'
if verbose: # Troubleshooting print
    print("NAMET_TH2 = %s" % NAMET_TH2)
    print("T_TH2_ID = %s" % T_TH2_ID)
    print("CONFIG_T_TH2 = %s" % CONFIGT_TH2)
    print("===============================")

ADDR_W13 = MYs["W1"]["ADDR_W13"]
NAME_W13 = MYs["W1"]["NAME_W13"]
W13_ID =  DEVICE_ID + '_' + MYs["W1"]["W13_ID"]
CONFIG_W13 = TOPIC + W13_ID + '/config'
W13_STATE = TOPIC + W13_ID + '/state'
if verbose: # Troubleshooting print
    print("ADDR_W13 = %s" % ADDR_W13)
    print("NAME_W13 = %s" % NAME_W13)
    print("W13_ID = %s" % W13_ID)
    print("CONFIG_W13 = %s" % CONFIG_W13)
    print("W13_STATE = %s" % W13_STATE)
    print("===============================")

ADDR_W14 = MYs["W1"]["ADDR_W14"]
NAME_W14 = MYs["W1"]["NAME_W14"]
W14_ID =  DEVICE_ID + '_' + MYs["W1"]["W14_ID"]
CONFIG_W14 = TOPIC + W14_ID + '/config'
W14_STATE = TOPIC + W14_ID + '/state'
if verbose: # Troubleshooting print
    print("ADDR_W14 = %s" % ADDR_W14)
    print("NAME_W14 = %s" % NAME_W14)
    print("W14_ID = %s" % W14_ID)
    print("CONFIG_W14 = %s" % CONFIG_W14)
    print("W14_STATE = %s" % W14_STATE)
    print("===============================")

SEN_TC5 = int(MYs["THERMOCOUPLE"]["SEN_TC5"])
NAME_TC5 = MYs["THERMOCOUPLE"]["NAME_TC5"]
TC5_ID =  DEVICE_ID + '_' + MYs["THERMOCOUPLE"]["TC5_ID"]
CONFIG_TC5 = TOPIC + TC5_ID + '/config'
TC5_STATE = TOPIC + TC5_ID + '/state'
if verbose: # Troubleshooting print
    print("SEN_TC5 = %s" % NAME_TC5)
    print("NAME_TC5 = %s" % NAME_TC5)
    print("TC5_ID = %s" % TC5_ID)
    print("CONFIG_TC5 = %s" % CONFIG_TC5)
    print("TC5_STATE = %s" % TC5_STATE)
    print("===============================")

SEN_TC6 = int(MYs["THERMOCOUPLE"]["SEN_TC6"])
NAME_TC6 = MYs["THERMOCOUPLE"]["NAME_TC6"]
TC6_ID =  DEVICE_ID + '_' + MYs["THERMOCOUPLE"]["TC6_ID"]
CONFIG_TC6 = TOPIC + TC6_ID + '/config'
TC6_STATE = TOPIC + TC6_ID + '/state'
if verbose: # Troubleshooting print
    print("SEN_TC6 = %s" % NAME_TC6)
    print("NAME_TC6 = %s" % NAME_TC6)
    print("TC6_ID = %s" % TC6_ID)
    print("CONFIG_TC6 = %s" % CONFIG_TC6)
    print("TC6_STATE = %s" % TC6_STATE)
    print("===============================")

NAME_CTL1 = MYs["ON_OFF"]["NAME_CTL1"]
CTL1_ID = DEVICE_ID + '_' +  MYs["ON_OFF"]["CTL1_ID"]
PIN_CTL1 = int(MYs["ON_OFF"]["PIN_CTL1"])
CONFIG_CTL1 = BSTOPIC + CTL1_ID + '/config'
CTL1_STATE = BSTOPIC + CTL1_ID + '/state'
if verbose: # Troubleshooting print
    print("NAME_CTL1 = %s" % NAME_CTL1)
    print("CTL1_ID = %s" % CTL1_ID)
    print("PIN_CTL1 = %s" % PIN_CTL1)
    print("CONFIG_CTL1 = %s" % CONFIG_CTL1)
    print("CTL1_STATE = %s" % CTL1_STATE)
    print("===============================")

# These are the GPIO's / SP ports / s/ns used for the temp/humid sensors.
list = [PIN_CTL1, PIN_TH1, PIN_TH2, ADDR_W13, ADDR_W14, SEN_TC5, SEN_TC6, 999, 999 ]
# These are the STATE Topics
state_topic = [CTL1_STATE, TH1_STATE, TH2_STATE, W13_STATE, W14_STATE, TC5_STATE, TC6_STATE, "", "" ]
if verbose: # Troubleshooting print
    print("list = %s" % list)
    print()
    print("state_topic = %s" % state_topic)
    print("===============================")

# Create the MQTT Discovery payloads
payloadH_TH1config = {
    "name": NAMEH_TH1,
    "stat_t": TH1_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": H_TH1_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas": "%",
    "dev_cla":"humidity",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.humidity }}"
}

payloadT_TH1config = {
    "name": NAMET_TH1,
    "stat_t": TH1_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": T_TH1_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payloadH_TH2config = {
    "name": NAMEH_TH2,
    "stat_t": TH2_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": H_TH2_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas": "%",
    "dev_cla":"humidity",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.humidity }}"
}

payloadT_TH2config = {
    "name": NAMET_TH2,
    "stat_t": TH2_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": T_TH2_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payload_W13config = {
    "name": NAME_W13,
    "stat_t": W13_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": W13_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payload_W14config = {
    "name": NAME_W14,
    "stat_t": W14_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": W14_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payload_TC5config = {
    "name": NAME_TC5,
    "stat_t": TC5_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": TC5_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payload_TC6config = {
    "name": NAME_TC6,
    "stat_t": TC6_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": TC6_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

payload_CTL1config = {
    "name": NAME_CTL1,
    "stat_t": CTL1_STATE,
    "avty_t": LWT,
    "pl_avail": "Online",
    "pl_not_avail": "Offline",
    "uniq_id": CTL1_ID,
    "dev": {
        "ids": [
        D_ID,
        DEVICE_ID
        ],
        "name": "ThermoPI Furnace",
        'sa': AREA,
        "mf": "SirGoodenough",
        "mdl": "HomeAssistant Discovery for ThermoPI Furnace",
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace",
        "cu": "https://github.com/SirGoodenough/ThermoPI-Furnace/blob/main/README.md"
    },
    "payload_on": '1',
    "payload_off": '0',
    "frc_upd": False
}

# set initial temp/humid values
temp = 0.0
humidity = 0.0

# set loop counter
count = 0

# Initialize pigpio library
pi = pigpio.pi()
if not pi.connected:
    exit(0)
pi.set_mode(PIN_CTL1, pigpio.OUTPUT)  # Set to output mode
pi.set_pull_up_down(PIN_CTL1, pigpio.PUD_DOWN)  # Set the pull down resistor

disablePelletFeed(10) # Ensure pellet feed is ON at start

# Log Message to start
print('Logging {0} sensor measurements every {1} seconds.'.format(D_ID, LOOP))
print('Press Ctrl-C to quit.')

# Connect to MQTT
mqttConnect()

# Main loop reading and sending data
try:
    count = 0
    while count < 7:
        if count > 5:  # Reset the loop
            count = 0
        count += 1
        if verbose: # Troubleshooting print
            print('Updating loop %s.' % count)
        temp = 0.0
        humidity = 0.0

        if count > 4:
            thermocouple()
        elif count > 2:
            W1()
        else:
            tempHumid()
        mqttSend()
        time.sleep(LOOP)

except KeyboardInterrupt:
    print(' Keyboard Interrupt. Closing MQTT.')
    client.loop_stop()
    client.unsubscribe(state_topic[0])
    disablePelletFeed(10)  # Ensure pellet feed is set to normal at interrupt
    time.sleep(2)
    client.publish(LWT, 'Offline', 1, True)
    time.sleep(1)
    client.disconnect()
    sys.exit()

'''
<<<===============================<<<
 MAX6675.py
 2016-05-02
 Public Domain
>>>===============================>>>
This script reads the temperature of a type K thermocouple
connected to a MAX6675 SPI chip.

Type K thermocouples are made of chromel (+ve) and alumel (-ve)
and are the commonest general purpose thermocouple with a
sensitivity of approximately 41 uV/C.

The MAX6675 returns a 12-bit reading in the range 0 - 4095 with
the units as 0.25 degrees centigrade.  So the reported
temperature range is 0 - 1023.75 C.

Accuracy is about +/- 2 C between 0 - 700 C and +/- 5 C
between 700 - 1000 C.

The MAX6675 returns 16 bits as follows

F   E   D   C   B   A   9   8   7   6   5   4   3   2   1   0
0  B11 B10  B9  B8  B7  B6  B5  B4  B3  B2  B1  B0  0   0   X

The reading is in B11 (most significant bit) to B0.

The conversion time is 0.22 seconds.  If you try to read more
often the sensor will always return the last read value.

    # pi.spi_open(0, 1000000, 0)   # CE0, 1Mbps, main SPI
    # pi.spi_open(1, 1000000, 0)   # CE1, 1Mbps, main SPI
    # pi.spi_open(0, 1000000, 256) # CE0, 1Mbps, auxiliary SPI
    # pi.spi_open(1, 1000000, 256) # CE1, 1Mbps, auxiliary SPI
    # pi.spi_open(2, 1000000, 256) # CE2, 1Mbps, auxiliary SPI
'''