#!/bin/sh

echo "Should be run as sudo..."
echo 
echo "Stopping ThermoPI-Furnace"
sudo systemctl stop thermoPIFurnace.service

echo "Copy file over"
# Edit next line to exact location & replace |user| with real username.
sudo cp /home/|user|/.ThermoPI/ThermoPI-Furnace/thermoPIFurnace.service /lib/systemd/system/thermoPIFurnace.service

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
