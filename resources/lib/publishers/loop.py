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
# MONITORS EVENTS NOT AVAILABLE IN XBMC API

import threading
import time
from json import loads as jloads

import xbmc
import xbmcgui
from resources.lib.pubsub import Publisher, Message, Topic
from resources.lib.events import Events


def getStereoscopicMode():
    """
    Retrieves stereoscopic mode from json-rpc
    @return: "off", "split_vertical", "split_horizontal", "row_interleaved", "hardware_based", "anaglyph_cyan_red",
             "anaglyph_green_magenta", "monoscopic"
    @rtype: str
    """
    query = '{"jsonrpc": "2.0", "method": "GUI.GetProperties", "params": {"properties": ["stereoscopicmode"]}, "id": 1}'
    result = xbmc.executeJSONRPC(query)
    jsonr = jloads(result)
    ret = ''
    if 'result' in jsonr:
        if 'stereoscopicmode' in jsonr['result']:
            if 'mode' in jsonr['result']['stereoscopicmode']:
                ret = jsonr['result']['stereoscopicmode']['mode'].encode('utf-8')
    return ret


def getProfileString():
    """
    Retrieves the current profile as a path
    @rtype: str
    """
    ps = xbmc.translatePath('special://profile')
    return ps


class LoopPublisher(Publisher, threading.Thread):
    publishes = Events().CustomLoop.keys()
    def __init__(self, dispatcher, owids=None, cwids=None, idleT=None, interval=500):
        Publisher.__init__(self, dispatcher)
        threading.Thread.__init__(self, name='LoopPublisher')
        self.interval = interval
        self.abort_evt = threading.Event()
        self.abort_evt.clear()
        if owids is None:
            self.openwindowids = {}
        else:
            self.openwindowids = owids
        if cwids is None:
            self.closewindowsids = {}
        else:
            self.closewindowsids = cwids
        self.player = xbmc.Player()
        if idleT is not None:
            if len(idleT) > 0:
                self.doidle = True
                self.idleTs = []
                self._startidle = 0
                self._playeridle = False
                for i, key in enumerate(idleT.keys()):
                    # time, key, executed
                    self.idleTs.append([idleT[key], key, False])
            else:
                self.doidle = False
        else:
            self.doidle = False
        self.publishes = Events().CustomLoop.keys()

    def run(self):
        lastwindowid = xbmcgui.getCurrentWindowId()
        lastprofile = getProfileString()
        laststereomode = getStereoscopicMode()
        interval = self.interval
        firstloop = True
        starttime = time.time()
        while not self.abort_evt.is_set():

            self._checkIdle()

            newprofile = getProfileString()
            if newprofile != lastprofile:
                self.publish(Message(Topic('onProfileChange'), profilePath=newprofile))
                lastprofile = newprofile

            newstereomode = getStereoscopicMode()
            if newstereomode != laststereomode:
                self.publish(Message(Topic('onStereoModeChange'), stereoMode=newstereomode))
                laststereomode = newstereomode

            newwindowid = xbmcgui.getCurrentWindowId()
            if newwindowid != lastwindowid:
                if lastwindowid in self.closewindowsids.keys():
                    self.publish(Message(Topic('onWindowClose', self.closewindowsids[lastwindowid])))
                if newwindowid in self.openwindowids:
                    self.publish(Message(Topic('onWindowOpen', self.openwindowids[newwindowid])))
                lastwindowid = newwindowid

            if firstloop:
                endtime = time.time()
                interval = int(interval - (endtime - starttime) * 1000)
                interval = max(5, interval)
                firstloop = False
            xbmc.sleep(interval)
        del self.player

    def _checkIdle(self):
        if self.doidle is False:
            return
        XBMCit = xbmc.getGlobalIdleTime()
        if self.player.isPlaying():
            self._playeridle = False
            self._startidle = XBMCit
        else:
            if self._playeridle is False:
                self._playeridle = True
                self._startidle = XBMCit
        myit = XBMCit - self._startidle
        for it in self.idleTs:
            if myit > it[0]:
                if not it[2]:
                    msg = Message(Topic('onIdle', it[1]))
                    self.publish(msg)
                    it[2] = True
            else:
                it[2] = False

    def abort(self, timeout=0):
        self.abort_evt.set()
        if timeout > 0:
            self.join(timeout)
            if self.is_alive():
                xbmc.log(msg='Could not stop LoopPublisher T:%i' % self.ident)
