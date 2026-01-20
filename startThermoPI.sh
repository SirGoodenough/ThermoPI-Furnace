#!/bin/bash
which python
cd /home/|user|/.ThermoPI/ThermoPI-Furnace
pwd
activate() {
. /home/|user|/.ThermoPI/bin/activate
}
activate
which python
python furnace.py