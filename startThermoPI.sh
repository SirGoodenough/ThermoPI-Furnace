#!/bin/bash
which python
cd /home/off/.ThermoPI/ThermoPI-Furnace
pwd
activate() {
. /home/off/.ThermoPI/ThermoPI-Furnace/bin/activate
}
activate
which python
python furnace.py