#!/usr/bin/python

import dbus
import gtk
import time
import thread
import threading
import serial
import sys


class Watcher(threading.Thread):

    def __init__(self, dev):
        threading.Thread.__init__(self)
        self.bus = dbus.SessionBus()

        self.dev = dev
        self.killed = False

    def getMediaServices(self):
        service_names = [str(name) for name in self.bus.list_names() if str(name).startswith('org.mpris.MediaPlayer2')]
        proxies = [self.bus.get_object(name, '/org/mpris/MediaPlayer2') for name in service_names]
        ifaces = [dbus.Interface(proxy, dbus_interface="org.mpris.MediaPlayer2.Player") for proxy in proxies]
        return ifaces

    def pause(self):
        ifaces = self.getMediaServices()
        for iface in ifaces:
            iface.Pause()

    def play(self):
        ifaces = self.getMediaServices()
        for iface in ifaces:
            iface.Pause()
            iface.PlayPause()

    def playPause(self):
        ifaces = self.getMediaServices()
        for iface in ifaces:
            iface.PlayPause()

    def run(self):
        try:

            self.dev.flushInput()
            while not self.killed:
                char = self.dev.read(1)
                self.dev.flushInput()
                if char:
                    if char == 'U':
                        print "Click up"
                        self.play()
                        time.sleep(0.1)
                    elif char == 'D':
                        print "Click down"
                        self.pause()
                        time.sleep(0.1)

            print "Shutting down..."
            self.dev.write("Z") # Send reset signal to device
            self.dev.close()
            print "Done"
        except:
            print "Shutting down..."
            gtk.main_quit()

    def kill(self):
        self.killed = True


class SerialInit:
    def __init__(self):

        self.running = False
        term = "/dev/pauser"
        dev = None

        while not self.running:
            try:
                print "Trying ", term
                dev = serial.Serial(port=term, baudrate=9600, timeout=1)

                assert dev

                self.running = self.initDevice(dev)

                if self.running:
                    break

                # No devices found
                assert dev
            except:
                print "Can't open device"
                time.sleep(5)
                continue

        print "Ready"

        self.background = Watcher(dev)
        self.background.start()

    def thread(self):
        return self.background.currentThread()

    def initDevice(self, dev):
        result = False

        dev.flushInput();
        dev.flushOutput();

        print "Sending init"
        dev.write("!")

        char = dev.read(1)

        if char:
            print char
            if char == "00".decode("hex"):
                print "Found Null"
                char = dev.read(1)

            if char == "#":
                print char
                dev.write("#")
                regcode = dev.read(4)
                if regcode:
                    print "Registration code: " + regcode
                    if(regcode == "5617"):
                        print "self.running = True"
                        result = True
                else:
                    print "No Regcode"
                    sys.exit(2)
            elif char == "+":
                print "Already Running! ZOMG Resetting!"
                dev.write("Z")
            else:
                print "Unexpected char: " + char
        else:
            print "No Char!"

        return result


gtk.gdk.threads_init()
serialInput = SerialInit()
try:
    gtk.main()
finally:
    serialInput.background.kill()
