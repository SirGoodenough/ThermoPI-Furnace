#!/bin/sh

ps auxw | grep furnace.py | grep -v grep > /dev/null

if [ $? != 0 ]
then
        systemctl restart thermoPIFurnace.service > /dev/null
fi

