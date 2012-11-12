#/bin/bash

DEVBASE="/dev/ttyACM"
DEVCOUNT=`ls $DEVBASE* | wc -l`

GNOMESESSION=`pgrep gnome-session`
GNOMEUSER=`stat --printf="%U" /proc/$GNOMESESSION`

if [ $DEVCOUNT -gt 1 ]
then
    echo "More than one device is attached. Please ensure only a single Launchpad device is connected to the computer."
    exit 1
fi

SERIAL=`udevadm info -a -p $(udevadm info -q path -n /dev/ttyACM?) | grep '{serial}' | head -n 1 | sed 's/.*"\(.*\)".*/\1/'`

UDEV='ATTRS{idVendor}=="0451", ATTRS{idProduct}=="f432", ATTRS{serial}=="'$SERIAL'", SUBSYSTEM=="tty", MODE="0660", GROUP="plugdev", NAME="pauser"'


echo $UDEV > /etc/udev/rules.d/48-pauser.rules

cp pauseService.py /usr/local/bin
cp pauseService.py.desktop $home/.config/autostart


