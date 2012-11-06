#!/usr/bin/python

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gtk
import time
import thread
import threading
import serial
import sys

class Watcher(threading.Thread):
    
    def __init__(self, dev, pauser):
        threading.Thread.__init__(self)
        self.bus = dbus.SessionBus()
        
        self.dev = dev
        self.pauser = pauser
        self.killed = False
    
    def run(self):
        try:
            
            self.dev.flushInput()
            while not self.killed:
                char = self.dev.read(1)
                if char:
                    if char == 'U':
                        print "Click up"
                        self.pauser.clickUp()
                    elif char == 'D':
                        print "Click down"
                        self.pauser.clickDown()
                    
                self.dev.flushInput()
                
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
    def __init__(self, pauser):
        
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
        
        self.background = Watcher(dev, pauser)
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
    

class Pauser(dbus.service.Object):
    def __init__(self):
        busName = dbus.service.BusName('org.hipokrit.pauser', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/Pauser')
    
    @dbus.service.method('org.hipokrit.pauser', in_signature = '', out_signature = 'b')
    def click(self):
        self.clicked()
        return True
    
    @dbus.service.method('org.hipokrit.pauser', in_signature = '', out_signature = 'b')
    def clickUp(self):
        self.clicked(True)
        return True
    
    @dbus.service.method('org.hipokrit.pauser', in_signature = '', out_signature = 'b')
    def clickDown(self):
        self.clicked(False)
        return True
    
    @dbus.service.signal(dbus_interface='org.hipokrit.pauser', signature='b')
    def clicked(self, up):
        return up



gtk.gdk.threads_init()
myMainLoop = DBusGMainLoop(set_as_default = True)
myservice = Pauser()
serialInput = SerialInit(myservice)
try:
    gtk.main()
finally:
    serialInput.background.kill()
