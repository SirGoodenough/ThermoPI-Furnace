#!/bin/sh

ps auxw | grep furnace5.py | grep -v grep > /dev/null

if [ $? != 0 ]
then
        systemctl restart furnaceTemp.service > /dev/null
fi

