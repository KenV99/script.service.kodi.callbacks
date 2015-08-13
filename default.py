#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 KenV99
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
##    This script is based on script.randomitems & script.wacthlist & script.xbmc.callbacks
#    Thanks to their original authors and pilulli

debug = False
remote = False
if debug:
    import sys
    if remote:
        sys.path.append(r'C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\script.ambibox\\resources\\lib\\'
                        r'pycharm-debug.py3k\\')
        import pydevd
        pydevd.settrace('192.168.1.103', port=51234, stdoutToServer=True, stderrToServer=True)
    else:
        sys.path.append('C:\Program Files (x86)\JetBrains\PyCharm 4.5\pycharm-debug-py3k.egg')
        import pydevd
        pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)


import os
from json import loads as jloads
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import subprocess
import sys
import abc
import requests as requests
import urllib2
import httplib
from urlparse import urlparse
import socket
import traceback

__addon__ = xbmcaddon.Addon('script.xbmc.callbacks2')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = str(__addon__.getAddonInfo('version'))
__settings__ = xbmcaddon.Addon("script.xbmc.callbacks2")
__language__ = __settings__.getLocalizedString
__settingsdir__ = xbmc.translatePath(os.path.join(__cwd__, 'resources')).decode('utf-8')
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')).decode('utf-8')
__author__ = 'KenV99'
__options__ = dict()
sys.path.append(__resource__)
import monitorext
from gotham2helix import get_installedversion
ver = get_installedversion()
if int(ver['major']) > 13:
    from gotham2helix import helix_abortloop as abortloop
else:
    from gotham2helix import gotham_abortloop as abortloop


def notification(text, *silence):
    """
    Display an XBMC notification box, optionally turn off sound associated with it
    @type text: str
    @type silence: bool
    """
    text = text.encode('utf-8')
    if __options__['notifications'] or __options__['tester']:
        icon = __settings__.getAddonInfo("icon")
        smallicon = icon.encode("utf-8")
        dialog = xbmcgui.Dialog()
        if __options__['tester']:
            dialog.ok(__scriptname__, text)
        else:
            if silence:
                dialog.notification(__scriptname__, text, smallicon, 1000, False)
            else:
                dialog.notification(__scriptname__, text, smallicon, 1000, True)


def debug(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u"$$$ [%s] - %s" % (__scriptname__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)


def info(txt):
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u"$$$ [%s] - %s" % (__scriptname__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGNOTICE)


def read_settings(ddict):
    """
    Reads settings from settings.xml and loads gloval __options__ and Dispatcher.ddict
    @param ddict: dictionary object from Dispatcher
    @type ddict: dict
    """
    global __options__
    _settings = xbmcaddon.Addon("script.xbmc.callbacks2")

    # Read in binary options
    setlist = ['user_monitor_playback', 'notifications', 'arg_eventid', 'arg_mediatype', 'arg_filename',
               'arg_title', 'arg_aspectratio', 'arg_resolution', 'arg_profilepath', 'arg_stereomode']
    for i in setlist:
        __options__[i] = (_settings.getSetting(i) == 'true')
    __options__['interval'] = int(float(_settings.getSetting('interval')))
    __options__['needs_listener'] = __options__['monitorStereoMode'] = __options__['monitorProfiles'] = False
    __options__['monitorPlayback'] = False

    # Read from settings command related settings and create workers in dictionary structure
    setlist = ['onPlaybackStarted', 'onPlaybackStopped', 'onPlaybackPaused', 'onPlaybackResumed',
               'onScreensaverActivated', 'onScreensaverDeactivated', 'onShutdown', 'onStereoModeChange',
               'onProfileChange', 'onIdle', 'onStartup',
               'onPlayBackSeekChapter', 'onQueueNextItem', 'onCleanStarted', 'onCleanFinished', 'onScanStarted',
               'onScanFinished', 'onDPMSActivated', 'onDPMSDeactivated']
    for i in setlist:
        setid = (i + '_type').decode('utf-8')
        mtype = _settings.getSetting(setid)
        if mtype != 'none' and mtype != '':
            setid = (i + '_str').decode('utf-8')
            if mtype == 'script':
                mstr = _settings.getSetting(setid + '.scr')
            elif mtype == 'python':
                mstr = _settings.getSetting(setid + '.pyt')
            elif mtype == 'builtin':
                mstr = _settings.getSetting(setid + '.btn')
            else:
                mstr = _settings.getSetting(setid + '.htp')
            if mstr == '':
                continue
            if mtype == 'script' or mtype == 'python':
                setid = (i + '_arg').decode('utf-8')
                argstr = _settings.getSetting(setid)
            else:
                argstr = ''
            worker = Factory.build_worker(mtype, mstr, argstr)
            if worker is not None:
                if mtype == 'script':
                    setid = (i + '_shell').decode('utf-8')
                    if _settings.getSetting(setid) == 'true':
                        worker.needs_shell = True
                    else:
                        worker.needs_shell = False
                worker.event_id = i
                ddict[i] = worker
                if i in ['onStereoModeChange', 'onProfileChange']:
                    __options__['needs_listener'] = True
                    if i == 'onStereoModeChange':
                        __options__['monitorStereoMode'] = True
                    else:
                        __options__['monitorProfiles'] = True
                elif i in ['onPlaybackStarted', 'onPlaybackStopped']:
                    if __options__['user_monitor_playback']:
                        __options__['needs_listener'] = True
                        __options__['monitorPlayback'] = True
                if i == 'onIdle':
                    __options__['idle_time'] = int(_settings.getSetting('idle_time'))
            else:
                info('Due to errors, unable to register command: %s' % mstr)


class Factory(object):
    """
    Factory object for building workers with abstract worker superclass and specific subclasses of worker
    """

    @staticmethod
    def build_worker(worker_type, cmd_string, argstr):
        """
        Builds workers
        @param worker_type: script, python, builtin, json, http
        @type worker_type: str
        @param cmd_string: the main command, language specific
        @type cmd_string: str
        @param argstr: user arguments as entered in settings
        @type argstr: list
        @return:
        """
        worker = None
        if worker_type == 'script':
            worker = WorkerScript(cmd_string, argstr)
        elif worker_type == 'python':
            worker = WorkerPy(cmd_string, argstr)
        elif worker_type == 'builtin':
            worker = WorkerBuiltin(cmd_string, argstr)
        elif worker_type == 'json':
            worker = WorkerJson(cmd_string, argstr)
        elif worker_type == 'http':
            worker = WorkerHTTP(cmd_string, argstr)
        if worker.passed:
            return worker
        else:
            del worker
            return None


class Player(xbmc.Player):
    """
    Subclasses xbmc.Player
    """
    global __options__
    dispatcher = None

    def __init__(self):
        super(Player, self).__init__()

    @staticmethod
    def playing_type():
        """
        @return: [music|movie|episode|stream|liveTV|recordedTV|PVRradio|unknown]
        """
        substrings = ['-trailer', 'http://']
        isMovie = False
        if xbmc.Player.isPlayingAudio(xbmc.Player()):
            return "music"
        else:
            if xbmc.getCondVisibility('VideoPlayer.Content(movies)'):
                isMovie = True
        try:
            filename = xbmc.Player.getPlayingFile(xbmc.Player())
        except:
            filename = ''
        if filename != '':
            if filename[0:3] == 'pvr':
                if xbmc.getCondVisibility('Pvr.IsPlayingTv'):
                    return 'liveTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRecording'):
                    return 'recordedTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
                    return 'PVRradio'
                else:
                    for string in substrings:
                        if string in filename:
                            isMovie = False
                            break
        if isMovie:
            return "movie"
        elif xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
            # Check for tv show title and season to make sure it's really an episode
            if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                return "episode"
        elif xbmc.getCondVisibility('Player.IsInternetStream'):
            return 'stream'
        else:
            return 'unknown'

    def getTitle(self):
        if self.isPlayingAudio():
            while xbmc.getInfoLabel('MusicPlayer.Title') is None:
                xbmc.sleep(250)
            return xbmc.getInfoLabel('MusicPlayer.Title')
        elif self.isPlayingVideo():
            while xbmc.getInfoLabel('VideoPlayer.Title') is None:
                xbmc.sleep(250)
            if xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
                if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                    return (xbmc.getInfoLabel('VideoPlayer.TVShowTitle') + '-Season ' +
                            xbmc.getInfoLabel('VideoPlayer.Season') + '-' + xbmc.getInfoLabel('VideoPlayer.Title'))
            else:
                return xbmc.getInfoLabel('VideoPlayer.Title')
        else:
            return 'Kodi cannot detect title'


    def getPlayingFileEx(self):
        try:
            fn = self.getPlayingFile()
        except:
            fn = 'unknown'
        if fn is None:
            fn = 'Kodi returned playing file is none'
        return xbmc.translatePath(fn)

    def getAspectRatio(self):
        try:
            ar = xbmc.getInfoLabel("VideoPlayer.VideoAspect")
        except:
            ar = 'unknown'
        if ar is None:
            ar = 'unknown'
        return ar

    def getResoluion(self):
        try:
            vr = xbmc.getInfoLabel("VideoPlayer.VideoResolution")
        except:
            vr = 'unknown'
        if vr is None:
            vr = 'unknown'
        return vr

    def onPlayBackStarted(self):
         if not __options__['monitorPlayback']:
            for i in xrange(1, 40):
                if not (self.isPlayingAudio() or self.isPlayingVideo()):
                    if i == 40:
                        return
                    else:
                        xbmc.sleep(250)
            self.onPlayBackStartedEx()

    def getRuntimeArgs(self):
        runtimeargs = []
        if __options__['arg_mediatype']:
            t = self.playing_type()
            if t is None:
                t = 'unknown'
            runtimeargs.append('type=' + t)
        if __options__['arg_filename']:
            runtimeargs.append('file=' + self.getPlayingFileEx())
        if __options__['arg_title']:
            runtimeargs.append('title=' + self.getTitle())
        if self.isPlayingVideo():
            if __options__['arg_aspectratio']:
                runtimeargs.append('aspectratio=' + self.getAspectRatio())
            if __options__['arg_resolution']:
                runtimeargs.append('resolution=' + self.getResoluion())
        return runtimeargs

    def onPlayBackStartedEx(self):
        runtimeargs = self.getRuntimeArgs()
        self.dispatcher.dispatch('onPlaybackStarted', runtimeargs)

    def onPlayBackStopped(self):
        if not __options__['monitorPlayback']:
            self.onPlayBackStoppedEx()

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

    def onPlayBackStoppedEx(self):
        self.dispatcher.dispatch('onPlaybackStopped', [])

    def onPlayBackPaused(self):
        self.dispatcher.dispatch('onPlaybackPaused', [])

    def onPlayBackResumed(self):
        runtimeargs = self.getRuntimeArgs()
        self.dispatcher.dispatch('onPlaybackResumed', runtimeargs)

    def onPlayBackSeekChapter(self, chapnum):
        self.dispatcher.dispatch('onPlayBackSeekChapter', [])

    def onPlayBackQueueNextItem(self):
        self.dispatcher.dispatch('onPlayBackQueueNextItem', [])


class Monitor(monitorext.MonitorEx):  # monitorext.MonitorEx
    """
    Subclasses MonitorEx which is a subclass of xbmc.Monitor
    """
    player = None
    dispatcher = None

    def __init__(self, monitorStereoMode, monitorProfiles, monitorPlayback):
        """
        @type monitorStereoMode: bool
        @type monitorProfiles: bool
        @type monitorPlayback: bool
        """
        monitorext.MonitorEx.__init__(self, monitorStereoMode, monitorProfiles, monitorPlayback)

    def onScanStarted(self, database):
        self.dispatcher.dispatch('onScanStarted', [])

    def onScanFinished(self, database):
        self.dispatcher.dispatch('onScanFinished', [])

    def onDPMSActivated(self):
        self.dispatcher.dispatch('onDPMSActivated', [])

    def onDPMSDeactivated(self):
        self.dispatcher.dispatch('onDPMSDeactivated', [])

    def onCleanStarted(self, database):
        self.dispatcher.dispatch('onCleanStarted', [])

    def onCleanFinished(self, database):
        self.dispatcher.dispatch('onCleanFinished', [])

    def onScreensaverActivated(self):
        self.dispatcher.dispatch('onScreensaverActivated', [])

    def onScreensaverDeactivated(self):
        self.dispatcher.dispatch('onScreensaverDeactivated', [])

    def onSettingsChanged(self):
        Main.load()

    def onStereoModeChange(self):
        runtimeargs = []
        if __options__['arg_stereomode']:
            runtimeargs = ['stereomode=' + self.getCurrentStereoMode()]
        self.dispatcher.dispatch('onStereoModeChange', runtimeargs)

    def onProfileChange(self):
        runtimeargs = []
        if __options__['arg_profilepath']:
            runtimeargs = ['profilepath=' + self.getCurrentProfile()]
        self.dispatcher.dispatch('onProfileChange', runtimeargs)

    def onPlaybackStarted(self):
        self.player.onPlayBackStartedEx()

    def onPlaybackStopped(self):
        self.player.onPlayBackStoppedEx()


class Dispatcher():
    """
    Class for dispatching workers to jobs
    """
    ddict = dict()

    def __init__(self):
        self.ddict = dict()

    def dispatch(self, event_id, runtimeargs):
        if event_id in self.ddict:
            worker = self.ddict[event_id]
            if __options__['arg_eventid']:
                runtimeargs = ['event=' + event_id] + runtimeargs
            info('Executing command: [%s] for event: %s' % (worker.cmd_str, event_id))
            result = worker.run(runtimeargs)
            if result[0]:
                info('Command for %s resulted in ERROR: %s' % (event_id, result[1]))
                notification(__language__(32051) % (event_id, result[1]))
            else:
                info('Command for %s executed successfully' % event_id)
                if not __options__['tester']:
                    (__language__(32052) % event_id)
            return result
        else:
            return [True, 'No registered command for \'%s\'' % event_id]


class AbstractWorker():
    """
    Abstract class for command specific workers to follow
    """
    __metaclass__ = abc.ABCMeta
    event_id = ''

    def __init__(self, cmd_str, userargs):
        self.cmd_str = cmd_str.strip()
        self.userargs = userargs
        self.passed = self.check()
        self.needs_shell = False

    @abc.abstractmethod
    def check(self):
        pass

    @abc.abstractmethod
    def run(self, runtimeargs):
        err = None  # True if error occured
        msg = ''    # string containing error message or return message
        return[err, msg]


class WorkerScript(AbstractWorker):

    def check(self):
        tmp = self.cmd_str
        self.cmd_str = []
        tmp = xbmc.translatePath(tmp).decode('utf-8')
        if xbmcvfs.exists(tmp):
            self.cmd_str.append(tmp)
            self.separate_userargs()
            self.type = 'script'
            return True
        else:
            info('Error - File not found: %s' % tmp)
            return False

    def separate_userargs(self):
        if len(self.userargs) > 0:
            ret = []
            new = str(self.userargs).split(' ')
            tst = ''
            for i in new:
                tst = tst + i + ' '
                if os.path.isfile(tst):
                    tst.rstrip()
                    ret.append(tst)
                elif len(ret) > 1:
                    ret.append(i)
            if len(ret) == 0:
                for i in new:
                    ret.append(i)
            self.userargs = ret
        else:
            self.userargs = []

    def run(self, runtimeargs):
        err = False
        msg = ''
        margs = self.cmd_str + runtimeargs + self.userargs
        try:
            result = subprocess.check_output(margs, shell=self.needs_shell, stderr=subprocess.STDOUT)
            if result is not None:
                msg = result
        except subprocess.CalledProcessError, e:
            err = True
            msg = e.output
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        return [err, msg]


class WorkerPy(AbstractWorker):

    def check(self):
        tmp = xbmc.translatePath(self.cmd_str).decode('utf-8')
        if xbmcvfs.exists(tmp):
            fn, ext = os.path.splitext(tmp)
            if ext == '.py':
                self.cmd_str = tmp
                self.type = 'python'
                return True
            else:
                info('Error - not a python script: %s' % tmp)
                return False
        else:
            info('Error - File not found: %s' % tmp)
            return False

    def run(self, runtimeargs):
        err = False
        msg = ''
        args = ', '.join(runtimeargs) + ', ' + self.userargs
        try:
            if len(args) > 1:
                result = xbmc.executebuiltin('XBMC.RunScript(%s, %s)' % (self.cmd_str, args))
            else:
                result = xbmc.executebuiltin('XBMC.RunScript(%s)' % self.cmd_str)
            if result is not None:
                msg = result
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        return [err, msg]


class WorkerBuiltin(AbstractWorker):

    def check(self):
        self.type = 'built-in'
        return True

    def run(self, runtimeargs):
        err = False
        msg = ''
        try:
            result = xbmc.executebuiltin(self.cmd_str)
            if result != '':
                err = True
                msg = result
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        return [err, msg]


class WorkerHTTP(AbstractWorker):

    def check(self):
        o = urlparse(self.cmd_str)
        if o.scheme != '' and o.netloc != '' and o.path != '':
            self.type = 'http'
            return True
        else:
            info('Invalid url: %s' % self.cmd_str)
            return False

    def run(self, runtimeargs):
        err = False
        msg = ''
        try:
            u = requests.get(self.cmd_str, timeout=20)
            info('requests return code: %s' % str(u.status_code))
            # u = urllib2.urlopen(self.cmd_str, timeout=20)
            # info('urlib2 return code: %s' % u.getcode())
            try:
                # result = u.read()
                result = u.text
            except Exception as e:
                err = True
                result = ''
                msg = 'Error on url read'
                if hasattr(e, 'message'):
                    msg = msg + '\n' + (str(e.message))
            del u
            msg = str(result)
        except requests.ConnectionError:
            err = True
            msg = 'Requests Connection Error'
        except requests.HTTPError:
            err = True
            msg = 'Requests HTTPError'
        except requests.URLRequired:
            err = True
            msg = 'Requests URLRequired Error'
        except requests.Timeout:
            err = True
            msg = 'Requests Timeout Error'
        except requests.RequestException:
            err = True
            msg = 'Generic Requests Error'
        except urllib2.HTTPError, e:
            err = True
            msg = 'HTTPError = ' + str(e.code)
        except urllib2.URLError, e:
            err = True
            msg = 'URLError\n' + e.reason
        except httplib.BadStatusLine, e:
            err = False
            info('Http Bad Status Line caught and passed')
            # pass - returned a status code that is not understood in the library
            if u is not None:
                try:
                    result = u.read()
                    info('Successful read after catching BadStatusLine')
                except Exception as e:
                    err = True
                    result = ''
                    msg = 'Error on url read'
                    if hasattr(e, 'message'):
                        msg = msg + '\n' + (str(e.message))
                del u
                msg = str(result)
        except httplib.HTTPException, e:
            err = True
            msg = 'HTTPException'
            if hasattr(e, 'message'):
                msg = msg + '\n' + e.message
        except socket.timeout, e:
            err = True
            msg = 'The request timed out, host unreachable'
        except Exception:
            err = True
            e = sys.exc_info()[0]
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        return [err, msg]


class WorkerJson(AbstractWorker):

    def check(self):
        self.type = 'json'
        return True

    def run(self, runtimeargs):
        err = False
        msg = ''
        try:
            result = xbmc.executeJSONRPC(self.cmd_str)
            msg = jloads(result)
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        return [err, msg]


class Main():
    dispatcher = None
    mm = None
    player = None

    @staticmethod
    def load():
        if Main.dispatcher is not None:
            del Main.dispatcher
        if Main.mm is not None:
            del Main.mm
        if Main.player is not None:
            del Main.player
        Main.dispatcher = Dispatcher()
        read_settings(Main.dispatcher.ddict)
        Main.mm = Monitor(__options__['monitorStereoMode'], __options__['monitorProfiles'],
                          __options__['monitorPlayback'])
        Main.mm.dispatcher = Main.dispatcher
        Main.player = Player()
        Main.player.dispatcher = Main.dispatcher
        Main.mm.player = Main.player
        if __options__['needs_listener']:
            Main.mm.Listen(interval=__options__['interval'])

    @staticmethod
    def run():
        # global __options__
        try:
            __options__['tester'] = False
            info('Starting %s version %s' % (__scriptname__, __version__))
            Main.load()
            if 'onStartup' in Main.dispatcher.ddict:
                Main.dispatcher.dispatch('onStartup', [])
            sleep_int = __options__['interval']
            executed_idle = False
            doidle = (('onIdle' in Main.dispatcher.ddict) is True)
            if doidle:
                idletime = 60 * __options__['idle_time']
            while not abortloop(sleep_int, Main.mm):
                if doidle:
                    if xbmc.getGlobalIdleTime() > idletime:
                        if not executed_idle:
                            Main.dispatcher.dispatch('onIdle', [])
                            executed_idle = True
                    else:
                        executed_idle = False
                #  xbmc.sleep(sleep_int)
            if 'onShutdown' in Main.dispatcher.ddict:
                Main.dispatcher.dispatch('onShutdown', [])
            if Main.mm is not None:
                Main.mm.StopListening()
                del Main.mm
            del Main.player
            del Main.dispatcher
            info('Stopped %s' % __scriptname__)
        except Exception, e:
            e = sys.exc_info()[0]
            msg = ''
            if hasattr(e, 'message'):
                msg = msg + str(e.message)
            msg = msg + '\n' + traceback.format_exc()
            info(__language__(32053) % msg)
            notification(__language__(32053) % msg)
            sys.exit()

    def __init__(self):
        pass

if __name__ == '__main__':
    Main().run()
