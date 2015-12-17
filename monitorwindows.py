#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2015 KenV99
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import threading
import xbmc
import xbmcgui

class MonitorWindows(threading.Thread):
    def __init__(self, interval):
        super(MonitorWindows, self).__init__()
        self.monitoropen = {}
        self.monitorclose = {}
        self._abort_evt = threading.Event()
        self._abort_evt.clear()
        self.interval = interval
        self.opensend = True
        self.closesend = True

    def run(self):
        monitorclosedids = self.monitorclose.keys()
        monitorbothids = self.monitoropen.keys() + monitorclosedids
        closedid = None
        openedids = []
        while not self._abort_evt.is_set():
            ids = [xbmcgui.getCurrentWindowId()]
            for id in ids:
                if id in monitorbothids:
                    if id in monitorclosedids:
                        closedid = id
                    else:
                        if id not in openedids:
                            if self.opensend:
                                self.monitoropen[id]([str(id)])
                            else:
                                self.monitoropen[id]([])
                            openedids.append(id)
                else:
                    if closedid is not None:
                        if id != closedid:
                            if self.closesend:
                                self.monitorclose[closedid]([str(id)])
                            else:
                                self.monitorclose[closedid]([])
                            closedid = None
                    openedids=[]
            xbmc.sleep(self.interval)