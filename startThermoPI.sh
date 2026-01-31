#!/bin/bash
which python
cd /home/|user|/.ThermoPI/ThermoPI-Furnace
pwd
activate() {
. /home/|user|/.ThermoPI/bin/activate
}
activate
which python

# 2 Command line arguments available: 
#  * {REQUIRED} Text Path pointing to the location of MYsecrets.yaml.
#     The last Text argument (not verbose) found will be attempted to be used as the path.
#     Default is /home/|user|/.ThermoPI/ThermoPI-Furnace/MYsecrets.yaml
#      where you change |user| to your user name.
#  * {Optional} The word "verbose or --verbose" turns on verbose troubleshoot mode.

python furnace.py /home/|user|/.ThermoPI/ThermoPI-Furnace/MYsecrets.yaml