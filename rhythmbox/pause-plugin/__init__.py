# Copyright (c) 2008 Michal Hruby <michal.mhr at gmail.com>
#
# This plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import rb
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject, gtk
import sys
import serial

class PausePlugin(rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)
        self.player = None
        self.thread = None

    def activate(self, shell):
        self.player = shell.get_player()
        
        dbus_loop = DBusGMainLoop(set_as_default=True)
        self.session_bus = dbus.SessionBus(mainloop = dbus_loop)
        
        self.active = 1
        self.was_playing = 0
        
        self.start_listen()
    
    def deactivate(self, shell):
        if self.player: self.player = None
    
    def start_listen(self):
        
        try:
            pause_interface = self.session_bus.get_object('org.hipokrit.pauser', '/Pauser')
            # add signals
            pause_interface.connect_to_signal("clicked", self.play_pause)
        except:
            print "Failure to connect to dbus object"
        
        print pause_interface
   
    
    def play_pause(self, up=None):
        print "Triggered"
        if up is not None:
            if up:
                self.player.play()
            else:
                self.player.pause()
        else:
            self.player.playpause()
