# ThermoPI
Use a Raspberry PI connected to one or more temperature sensors to send the results to a MQTT server.

## USAGE:

Install the program into opt/ThermoPI or any suitable location.

You will need to rename the file '''sample_MYsecrets.py''' to '''MYsecrets.py'''
Edit the contents of '''MYsecrets.py''' to match your MQTT installation.



The PY program itself is well documented.
Follow the comments there to change the necessary information.

Program requirements (as written):  (feel free to fork it and convert to Python 3.x...)
+ Python 2.7 
+ pigpio            For reading GPIO / Thermocouple
+ paho-mqtt         For MQTT
+ W1ThermSensor     For 2 wire temp sensors (DS18B20)
+ Adafruit_DHT      For the other temp / humid sensors (AM2302)

If you have any questions, comments or additions be sure to add an issue and bring them up on my Discord Server: 

## Contact Links:
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
