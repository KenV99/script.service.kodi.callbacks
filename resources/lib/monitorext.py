# -*- coding: utf-8 -*-
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file LICENSE.txt.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *

import threading
from json import loads as jloads

import xbmc
import xbmcaddon

__p__ = None
# __addon__ = xbmcaddon.Addon('script.module.monitorext')
# __scriptname__ = __addon__.getAddonInfo('name')


def debug(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u"### [%s] - %s" % ('xbmc.callbacks2', txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)


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


def getPlayingState():
    """
    Retrieves the current player state from xbmc.player
    @return: 'Unknown', 'Playing' or 'Stopped'
    @rtype: str
    """
    if __p__ is not None:
        if __p__.isPlaying():
            ps = 'Playing'
        else:
            ps = 'Stopped'
    else:
        if xbmc.Player.isPlaying(xbmc.Player()):
            ps = 'Playing'
        else:
            ps = 'Stopped'
    return ps


class __MonitorThread__ (threading.Thread):
    """
    Class for monitoring state
    Should not be accessed from outside the module
    """

    def __init__(self, monitorfunc, executefunc, mname, interval):
        """
        @param monitorfunc: The function which provides state information
        @type monitorfunc: method
        @param executefunc: The function/method that is called when state changes
        @type executefunc: method
        @param mname: The name for the thread which is arbitrary
        @type mname: str
        @param interval: The frequency with which to poll for state change
        @type interval: int
        @return: None
        """
        threading.Thread.__init__(self, name=mname)
        self.currentState = None
        self.executefunc = executefunc
        self.monitorfunc = monitorfunc
        self.interval = interval
        self.running = False

    def start(self):
        self.running = True
        threading.Thread.start(self)

    def stop(self):
        self.running = False
        self.join(0.5)
        self.close()

    def close(self):
        pass

    def run(self):
        threading.Thread.run(self)
        while not xbmc.abortRequested:
            newstate = self.monitorfunc()
            if self.currentState is None:
                self.currentState = newstate
            else:
                if newstate != self.currentState:
                    self.currentState = newstate
                    self.executefunc()
            xbmc.sleep(self.interval)


class MonitorEx(xbmc.Monitor):

    def __init__(self, monitorStereoMode, monitorProfiles, monitorPlayback):
        """
        Class that subclasses xbmc.Monitor and extends it with onSteroModeChanged(), onProfileChanges and
            onPlaybackStarted() events. The last is needed for external players in Gotham up to 13.1.
        @param monitorStereoMode: whether or not to monitor for StereoMode changes
        @type monitorStereoMode: bool
        @param monitorProfiles: whether or not to monitor for Profile changes
        @type monitorProfiles: bool
        @param monitorPlayback: whether or not to monitor for player Playback starting
        @type monitorPlayback: bool
        """
        global __p__
        super(xbmc.Monitor, self).__init__()
        if monitorStereoMode:
            self.monitorStereoMode = True
        else:
            self.monitorStereoMode = False
        if monitorProfiles:
            self.monitorProfiles = True
        else:
            self.monitorProfiles = False
        if monitorPlayback:
            self.monitorPlayback = True
            __p__ = xbmc.Player()
        else:
            self.monitorPlayback = False

        self.smtr = None
        self.psmtr = None
        self.pbmtr = None

    def __onStereoModeChange(self):
        self.onStereoModeChange()

    def onStereoModeChange(self):
        pass

    def getCurrentStereoMode(self):
        sm = getStereoscopicMode()
        return sm

    def __onProfileChange(self):
        self.onProfileChange()

    def onProfileChange(self):
        pass

    def getCurrentProfile(self):
        ps = getProfileString()
        return ps

    def __onPlaybackStarted(self):
        if getPlayingState() == 'Playing':
            self.onPlaybackStarted()
        else:
            self.onPlaybackStopped()

    def onPlaybackStarted(self):
        pass

    def onPlaybackStopped(self):
        pass

    def Listen(self, **kwargs):
        """
        Starts listening for events OTHER THAN the built-in xbmc.Monitor events
        @keyword interval: default interval to poll for state changes
        @type interval: int
        @keyword stereoInterval: interval to poll for playback stereoMode change
        @type stereoInterval: int
        @keyword profileInterval: interval to poll for profile state change
        @type profileInterval: int
        @keyword playbackInterval: interval to poll for playback state change
        @type playbackInterval: int
        @param kwargs: interval, stereoInterval, profileInterval, playbackInterval
        """

        if kwargs['interval'] is not None:
            try:
                _interval = int(kwargs['interval'])
            except ValueError:
                _interval = 1000
        else:
            _interval = 1000

        if self.monitorStereoMode:
            if 'stereoInterval' in kwargs:
                try:
                    _stereoInterval = int(kwargs['stereoInterval'])
                except ValueError:
                    _stereoInterval = _interval
            else:
                _stereoInterval = _interval
            self.smtr = __MonitorThread__(getStereoscopicMode, self.__onStereoModeChange, 'StereoMode', _stereoInterval)
            self.smtr.start()
        if self.monitorProfiles:
            if 'profileInterval' in kwargs:
                try:
                    _profileInterval = int(kwargs['profileInterval'])
                except ValueError:
                    _profileInterval = _interval
            else:
                _profileInterval = _interval
            self.psmtr = __MonitorThread__(getProfileString, self.__onProfileChange, 'Profile', _profileInterval)
            self.psmtr.start()
        if self.monitorPlayback:
            if 'playbackInterval' in kwargs:
                try:
                    _playbackInterval = int(kwargs['playbackInterval'])
                except ValueError:
                    _playbackInterval = _interval
            else:
                _playbackInterval = _interval
            self.pbmtr = __MonitorThread__(getPlayingState, self.__onPlaybackStarted, 'Playback', _playbackInterval)
            self.pbmtr.start()

    def StopListening(self):
        if self.smtr is not None:
            self.smtr.stop()
            del self.smtr
        if self.psmtr is not None:
            self.psmtr.stop()
            del self.psmtr
        if self.pbmtr is not None:
            self.pbmtr.stop()
            del self.pbmtr
