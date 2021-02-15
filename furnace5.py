#!/usr/bin/python
import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html
import Adafruit_DHT
import paho.mqtt.client as mqtt
import datetime
import time
import sys
import requests
import json
import secrets
from w1thermsensor import W1ThermSensor
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
    # Test the result
    if tempC is None or tempC > 150.0 or tempC < 1.0:
        return
    # Conversion to F & round to .2
    tF = round((9.0/5.0 * tempC + 32.0), 2)
    # print("{:.2f}".format(tF))
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
            # Conversion to F & round to .2
            tF = round((9.0/5.0 * tempC + 32.0), 2)
            # print("{:.2f}".format(tF))
        else:
            print('bad reading {:b}'.format(word))
            return
        # Done
        temp = tF


# Subroutine to look up temp/humid sensors
def temphumid():

    global temp
    global humidity

    temp = 0.0
    tempC = 0.0
 
    time.sleep(FREQUENCY_SECONDS / 10)  # Settling time
    humidity, tempC = Adafruit_DHT.read_retry(
        DHT_TYPE, list[count], retries=8, delay_seconds=.85)

    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).

    if humidity is None or humidity > 100.0 or tempC is None or tempC > 150.0:
        print('bad reading {0} {1}'.format(tempC, humidity))
        return

    temp = round((9.0/5.0 * tempC + 32.0), 2)  # Conversion to F & round to .2
    humidity = round(humidity, 2)            # Round to .2


# Subroutine to mqtt
def mqttsend():

    global temp
    global humidity
    global ftemp
    global fhumid
    global mqttempC
    global count

    if temp == 0.0:
        return

    try:
        time.sleep(1)
        (result1, mid) = mqttempC.publish(
            ftemp, temp, qos=0, retain=True)
        result2 = -1
        if count < 3:
            time.sleep(3)
            (result2, mid) = mqttempC.publish(
                fhumid, humidity, qos=0, retain=True)
        currentdate = time.strftime('%Y-%m-%d %H:%M:%S')
        print('Date Time:   {0}'.format(currentdate))
        print('Temp: {0:0.2f}F Humd: {1:0.2f}%'.format(temp, humidity))
        if result1 == 1 or result2 == 1:
            print('MQTT Updated result {0} and {1}'.format(result1, result2))
            raise ValueError('MQTT Fail, ', mid)

    except Exception as e:
        # Error appending data, most likely because credentials are stale.
        # Null out the worksheet and login again.
        mqttempC.publish('furnacepi/lwt', 'Offline', 0, True)
        mqttempC.disconnect()
        print('Append error, logging in again: ' + str(e))
        global MOSQUITTO_HOST
        global MOSQUITTO_PORT
        mqttempC.connect(MOSQUITTO_HOST, MOSQUITTO_PORT)
        mqttempC.publish('furnacepi/lwt', 'Online', 0, True)
        pass


# Type of sensor, can be Adafruit_DHT.DHT11, Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
DHT_TYPE = Adafruit_DHT.AM2302

MOSQUITTO_HOST = secrets.HOST
MOSQUITTO_PORT = secrets.PORT
MOSQUITTO_USER = secrets.USER
MOSQUITTO_PWD = secrets.PWD
temp = 0.00
humidity = 0.00
# These are the topics.
ftemp = ''
fhumid = ''
# Set Template strings
templ_t_string = 'furnacepi/temperature'
templ_h_string = 'furnacepi/humidity'
# set loop counter
count = 0
# These are the GPIO's / SP ports used for the temp/humid sensors.
list = [999, 4, 17, "60d70d1864ff", "0ad50d1864ff", 0, 1, 999, 999]
# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS = 10
# Get the library for the thermocouples
pi = pigpio.pi()
# Check the library connection
if not pi.connected:
    exit(0)

print('Logging sensor measurements to {0} every {1} seconds.'
      .format('MQTT', FREQUENCY_SECONDS))
print('Press Ctrl-C to quit.')
print('Connecting to MQTT on {0}'.format(MOSQUITTO_HOST))
mqttempC = mqtt.Client('python_pub', 'False', 'MQTTv311')
mqttempC.username_pw_set(MOSQUITTO_USER, MOSQUITTO_PWD)
mqttempC.will_set('furnacepi/lwt', 'Offline', 0, True)

try:
        # Log onto the MQTT server
    mqttempC.connect(MOSQUITTO_HOST, MOSQUITTO_PORT)
    mqttempC.publish('furnacepi/lwt', 'Online', 0, True)
    
    count = 0
    while count < 7:
        if count > 5:  # Reset the loop
            count = 0
        count += 1
        print('Updating loop %s.' % count)

        temp = 0.0
        humidity = 0.0
        ftemp = templ_t_string + str(count)
        fhumid = templ_h_string + str(count)
        if count > 4:
            thermocouple()
        elif count > 2:
            W1()
        else:
            temphumid()
        mqttsend()
        time.sleep(FREQUENCY_SECONDS)

except Exception as e:
    mqttempC.publish('furnacepi/lwt', 'Offline', 0, True)
    mqttempC.disconnect()
    print('Connection Error: ' + str(e))
    pass
