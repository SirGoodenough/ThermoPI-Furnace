#!/bin/sh

echo "Stopping ThermoPI"
sudo systemctl stop ThermoPI.service  

echo "Copy file over"
sudo cp /opt/ThermoPI-Furnace/thermoPIFurnace.service /lib/systemd/system/thermoPIFurnace.service

echo "Change permissions on new file"
sudo chmod 644 /lib/systemd/system/thermoPIFurnace.service

echo "Reload the systemd daemon"
sudo systemctl daemon-reload

echo "Enable the new service"
sudo systemctl enable thermoPIFurnace.service

echo "Start the new service"
sudo systemctl start thermoPIFurnace.service  

echo "Check that the new service is running"
# Delay to give the pi a chance to think
sleep 7

sudo systemctl status thermoPIFurnace.service
