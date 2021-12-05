#!/usr/bin/python3

import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html
import Adafruit_DHT
from w1thermsensor import W1ThermSensor
import paho.mqtt.client as mqtt
import sys
import time
import yaml
import json
import uuid

'''
 DHT Sensor Data-logging to MQTT Temperature channel

 Requies a Mosquitto Server Install On the destination.

 Copyright (c) 2014 Adafruit Industries
 Author: Tony DiCola
 MQTT Encahncements: David Cole (2016)

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

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

# Subroutine look up 1 Wire temp(s)
def W1():
    global temp
    global sensor
    global list
    global count

    tempC = 0.0
    temp = 0.0

    # sensor = W1ThermSensor()
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, list[count])

    # Get the temp
    tempC = sensor.get_temperature()
    # Test the result.  Make sure it is reasonable and not a glitch.
    if tempC is None or tempC > 150.0 or tempC < 1.0:
        return
    # Conversion to F & round to .1
    tF = round((9.0/5.0 * tempC + 32.0), 1)
    # Use while Troubleshooting...
    # print("{:.1f}".format(tF))
    # Done
    temp = tF


# Subroutine look up thermcouple temps
def thermocouple():
    global temp
    global pi
    global list
    global count

    temp = 0.0
    tempC = 0.0
    
    # Check the thermocouple(s) on the Serial links.
    sensor = pi.spi_open(list[count], 1000000, 0)
    c, d = pi.spi_read(sensor, 2)
    pi.spi_close(sensor)

    if c == 2:
        word = (d[0] << 8) | d[1]
        if (word & 0x8006) == 0:  # Bits 15, 2, and 1 should be zero.
            tempC = (word >> 3)/4.0
            # Test the result
            if tempC is None or tempC > 1500.0 or tempC < 1.0:
                return
            # Conversion to F & round to .1
            tF = round((9.0/5.0 * tempC + 32.0), 1)
            # Use while Troubleshooting...
            # print("{:.2f}".format(tF))
        else:
            print('bad reading {:b}'.format(word))
            return
        # Done
        temp = tF


# Subroutine to look up temp/humid sensors
def tempHumid():
    global temp
    global humidity

    temp = 0.0
    tempC = 0.0

    time.sleep(LOOP / 10)  # Settling time
    humidity, tempC = Adafruit_DHT.read_retry(
        DHT_TYPE, list[count], retries=8, delay_seconds=.85)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).

    if humidity is None or humidity > 100.0 or tempC is None or tempC > 150.0:
        print('bad reading {0} {1}'.format(tempC, humidity))
        return

    temp = round((9.0/5.0 * tempC + 32.0), 1)  # Conversion to F & round to .1
    humidity = round(humidity, 1)            # Round to .1
        # Use while Troubleshooting...
    # print('Temp: {0:0.1f}F Humd: {1:0.1f}%'.format(temp, humidity))

def mqttConnect():
    print('Connecting to MQTT on {0} {1}'.format(HOST,PORT))
    mqttc.connect(HOST, PORT, 60)
    mqttc.loop_start()
    mqttc.publish(LWT, "Online", 1, True)
    mqttc.publish(CONFIGH_TH1, json.dumps(payloadH_TH1config), 1, True)
    mqttc.publish(CONFIGT_TH1, json.dumps(payloadT_TH1config), 1, True)
    mqttc.publish(CONFIGH_TH2, json.dumps(payloadH_TH2config), 1, True)
    mqttc.publish(CONFIGT_TH2, json.dumps(payloadT_TH2config), 1, True)
    mqttc.publish(CONFIG_W13, json.dumps(payload_W13config), 1, True)
    mqttc.publish(CONFIG_W14, json.dumps(payload_W14config), 1, True)
    mqttc.publish(CONFIG_TC5, json.dumps(payload_TC5config), 1, True)
    mqttc.publish(CONFIG_TC6, json.dumps(payload_TC6config), 1, True)

# Subroutine to send results to MQTT
def mqttSend():
    global temp
    global humidity
    global mqttc
    global count
    global state_topic

    if temp == 0.0:
        return

    try:

        payloadOut = {
            "temperature": temp,
            "humidity": humidity}
        OutState = state_topic[count]
        print('Updating {0} {1}'.format(OutState,json.dumps(payloadOut) ) )
        (result1,mid) = mqttc.publish(OutState, json.dumps(payloadOut), 1, True)

        currentdate = time.strftime('%Y-%m-%d %H:%M:%S')
        print('Date Time:   {0}'.format(currentdate))
        print('MQTT Update result {0}'.format(result1))

        if result1 == 1:
            raise ValueError('Result message from MQTT was not 0')

    except Exception as e:
        # Error appending data, most likely because credentials are stale.
        #  disconnect and re-connect...
        print('MQTT error, trying re-connect: ' + str(e))
        mqttc.publish(LWT, 'Offline', 0, True)
        time.sleep(2)
        mqttc.loop_stop()
        mqttc.disconnect()
        time.sleep(1)
        mqttConnect()
        pass

# Type of sensor, can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
DHT_TYPE = Adafruit_DHT.AM2302

temp = 0.00
humidity = 0.00
# set loop counter
count = 0
# Get the library for the thermocouples
pi = pigpio.pi()
# Check the library connection
if not pi.connected:
    exit(0)

#  Get the parameter file
with open("/opt/ThermoPI-Furnace/MYsecrets.yaml", "r") as ymlfile:
    MYs = yaml.safe_load(ymlfile)

# Type of sensor, can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302
DHT_TYPE = Adafruit_DHT.AM2302
# Example of sensor connected to Raspberry Pi pin 23
#DHT_PIN = 23
# Example of sensor connected to Beaglebone Black pin P8_11
#DHT_PIN  = 'P8_11'

LOOP = MYs["MAIN"]["LOOP"]
HOST = MYs["MAIN"]["HOST"]
PORT = MYs["MAIN"]["PORT"]
USER = MYs["MAIN"]["USER"]
PWD = MYs["MAIN"]["PWD"]
AREA = MYs["MAIN"]["AREA"]

# Pulling the unique MAC SN section address using uuid and getnode() function 
DEVICE_ID = (hex(uuid.getnode())[-6:]).upper()

TOPIC = "homeassistant/sensor/"

NAMED = MYs["MAIN"]["DEVICE_NAME"]
D_ID = DEVICE_ID + '_' + NAMED
LWT = TOPIC + D_ID + '/lwt'

PIN_TH1 = MYs["TEMP_HUMID"]["PIN_TH1"]
NAMEH_TH1 = MYs["TEMP_HUMID"]["NAMEH_TH1"]
H_TH1_ID =  DEVICE_ID + '_' + MYs["TEMP_HUMID"]["H_TH1_ID"]
CONFIGH_TH1 = TOPIC + H_TH1_ID + '/config'
TH1_STATE = TOPIC + H_TH1_ID + '/state'

NAMET_TH1 = MYs["TEMP_HUMID"]["NAMET_TH1"]
T_TH1_ID = DEVICE_ID + '_' + MYs["TEMP_HUMID"]["T_TH1_ID"]
CONFIGT_TH1 = TOPIC + T_TH1_ID + '/config'

PIN_TH2 = MYs["TEMP_HUMID"]["PIN_TH2"]
NAMEH_TH2 = MYs["TEMP_HUMID"]["NAMEH_TH2"]
H_TH2_ID =  DEVICE_ID + '_' + MYs["TEMP_HUMID"]["H_TH2_ID"]
CONFIGH_TH2 = TOPIC + H_TH2_ID + '/config'
TH2_STATE = TOPIC + H_TH2_ID + '/state'

NAMET_TH2 = MYs["TEMP_HUMID"]["NAMET_TH2"]
T_TH2_ID = DEVICE_ID + '_' + MYs["TEMP_HUMID"]["T_TH2_ID"]
CONFIGT_TH2 = TOPIC + T_TH2_ID + '/config'

ADDR_W13 = MYs["W1"]["ADDR_W13"]
NAME_W13 = MYs["W1"]["NAME_W13"]
W13_ID =  DEVICE_ID + '_' + MYs["W1"]["W13_ID"]
CONFIG_W13 = TOPIC + W13_ID + '/config'
W13_STATE = TOPIC + W13_ID + '/state'

ADDR_W14 = MYs["W1"]["ADDR_W14"]
NAME_W14 = MYs["W1"]["NAME_W14"]
W14_ID =  DEVICE_ID + '_' + MYs["W1"]["W14_ID"]
CONFIG_W14 = TOPIC + W14_ID + '/config'
W14_STATE = TOPIC + W14_ID + '/state'

SEN_TC5 = MYs["THERMOCOUPLE"]["SEN_TC5"]
NAME_TC5 = MYs["THERMOCOUPLE"]["NAME_TC5"]
TC5_ID =  DEVICE_ID + '_' + MYs["THERMOCOUPLE"]["TC5_ID"]
CONFIG_TC5 = TOPIC + TC5_ID + '/config'
TC5_STATE = TOPIC + TC5_ID + '/state'

SEN_TC6 = MYs["THERMOCOUPLE"]["SEN_TC6"]
NAME_TC6 = MYs["THERMOCOUPLE"]["NAME_TC6"]
TC6_ID =  DEVICE_ID + '_' + MYs["THERMOCOUPLE"]["TC6_ID"]
CONFIG_TC6 = TOPIC + TC6_ID + '/config'
TC6_STATE = TOPIC + TC6_ID + '/state'

# These are the GPIO's / SP ports / s/ns used for the temp/humid sensors.
list = [999, PIN_TH1, PIN_TH2, ADDR_W13, ADDR_W14, SEN_TC5, SEN_TC6, 999, 999 ]

# These are the STATE Topics
state_topic = ["", TH1_STATE, TH2_STATE, W13_STATE, W14_STATE, TC5_STATE, TC6_STATE, "", "" ]

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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
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
        "sw": "https://github.com/SirGoodenough/ThermoPI-Furnace"
    },
    "unit_of_meas":"°F",
    "dev_cla":"temperature",
    "frc_upd": True,
    'exp_aft': 400,
    "val_tpl": "{{ value_json.temperature }}"
}

    #Log Message to start
print('Logging {0} sensor measurements every {1} seconds.'.format(D_ID, LOOP))
print('Press Ctrl-C to quit.')
mqttc = mqtt.Client('python_pub', 'False', 'MQTTv311', 60)
#mqttc.disable_logger()  # Saves wear on SD card Memory.  Remove as needed for troubleshooting
mqttc.username_pw_set(USER, PWD) # deactivate if not needed
mqttConnect()

try:
    count = 0
    while count < 7:
        if count > 5:  # Reset the loop
            count = 0
        count += 1
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
    mqttc.publish(LWT, 'Offline', 1, True)
    time.sleep(1)
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit()
