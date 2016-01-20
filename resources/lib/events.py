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

def requires_subtopic():
    return ['onFileSystemChange', 'onLogSimple', 'onLogRegex', 'onIdle', 'onWindowOpen', 'onWindowClose', 'onNotification']


class Events(object):
    Player = {
        'onPlayBackStarted':{
            'text':'on Playback Started',
            'reqInfo':[],
            'optArgs':['mediaType', 'fileName', 'title', 'aspectRatio', 'resolution'],
            'varArgs':{'%mt':'mediaType', '%fn':'fileName', '%ti':'title', '%ar':'aspectRatio', '%rs':'resolution'},
            'expArgs':{'mediaType':'movie', 'fileName':'G:\\movies\\Star Wars - Episode IV\\movie.mkv',
                       'title':'Star Wars Episode IV - A New Hope', 'aspectRatio':'2.35', 'resolution':'1080'}
        },
        'onPlayBackEnded':{
            'text':'on Playback Ended',
            'reqInfo':[],
            'optArgs':['mediaType', 'fileName', 'title', 'percentPlayed'],
            'varArgs':{'%mt':'mediaType', '%fn':'fileName', '%ti':'title', '%pp':'percentPlayed'},
            'expArgs':{'mediaType':'movie', 'fileName':'G:\\movies\\Star Wars - Episode IV\\movie.mkv',
                       'title':'Star Wars Episode IV - A New Hope', 'percentPlayed':'26'}
        },
        'onPlayBackPaused':{
            'text':'on Playback Paused',
            'reqInfo':[],
            'optArgs':['time'],
            'varArgs':{'%ti':'time'},
            'expArgs':{'time':'235.026016235'}
        },
        'onPlayBackResumed':{
            'text':'on Playback Resumed',
            'reqInfo':[],
            'optArgs':[]
        },
        'onPlayBackSeek':{
            'text':'on Playback Seek',
            'reqInfo':[],
            'optArgs':['time'],
            'varArgs':{'%ti':'time'},
            'expArgs':{'time':'252615'}
        },
        'onPlayBackSeekChapter':{
            'text':'on Playback Seek Chapter',
            'reqInfo':[],
            'optArgs':['chapter'],
            'varArgs':{'%ch':'chapter'},
            'expArgs':{'chapter':'2'}
        },
        'onPlayBackSpeedChanged':{
            'text':'on Playback Speed Changed',
            'reqInfo':[],
            'optArgs':['speed'],
            'varArgs':{'%sp':'speed'},
            'expArgs':{'speed':'2'}
        },
        'onQueueNextItem':{
            'text':'on Queue Next Item',
            'reqInfo':[],
            'optArgs':[]
        }
    }
    Monitor = {
        'onCleanFinished':{
            'text':'on Clean Finished',
            'reqInfo':[],
            'optArgs':['library'],
            'varArgs':{'%li':'library'},
            'expArgs':{'library':'movies'}
        },
        'onCleanStarted':{
            'text':'on Clean Started',
            'reqInfo':[],
            'optArgs':['library'],
            'varArgs':{'%li':'library'},
            'expArgs':{'library':'movies'}
        },
        'onDPMSActivated':{
            'text':'on DPMS Activated',
            'reqInfo':[],
            'optArgs':[]
        },
        'onDMPSDeactivated':{
            'text':'on DPMS Deactivated',
            'reqInfo':[],
            'optArgs':[]
        },
        'onNotification':{
            'text':'on JSON Notification',
            'reqInfo':[('sender', 'text', ''), ('method', 'text', ''), ('data', 'text', '')],
            'optArgs':['sender', 'method', 'data'],
            'varArgs':{'%se':'sender', '%me':'method', '%da':'data'},
            'expArgs':{'sender':'xbmc', 'method':'VideoLibrary.OnScanStarted', 'data':'null'}
        },
        'onScanFinished':{
            'text':'on Scan Finished',
            'reqInfo':[],
            'optArgs':['library'],
            'varArgs':{'%li':'library'},
            'expArgs':{'library':'movies'}
        },
        'onScanStarted':{
            'text':'on Scan Started',
            'reqInfo':[],
            'optArgs':['library'],
            'varArgs':{'%li':'library'},
            'expArgs':{'library':'movies'}
        },
        'onScreensaverActivated':{
            'text':'on Screensaver Activated',
            'reqInfo':[],
            'optArgs':[]
        },
        'onScreensaverDeactivated':{
            'text':'on Screensaver Deactivated',
            'reqInfo':[],
            'optArgs':[]
        },
    }
    CustomLoop = {
        'onStereoModeChange':{
            'text':'on Stereoscopic Mode Change ',
            'reqInfo':[],
            'optArgs':['stereoMode'],
            'varArgs':{'%sm':'stereoMode'},
            'expArgs':{'stereoMode':'split_vertical'}
        },
        'onProfileChange':{
            'text':'on Profile Change',
            'reqInfo':[],
            'optArgs':['profilePath'],
            'varArgs':{'%pp':'profilePath'},
            'expArgs':{'profilePath':'C:\\Users\\Ken User\\AppData\\Roaming\\Kodi\\userdata\\'}
        },
        'onWindowOpen':{
            'text':'on Window Opened',
            'reqInfo':[('windowIdO', 'int', 0)],
            'optArgs':['windowId'],
            'varArgs':{'%wi':'windowId'},
            'expArgs':{'windowId':'10000'}
        },
        'onWindowClose':{
            'text':'on Window Closed',
            'reqInfo':[('windowIdC','int', 0)],
            'optArgs':['windowId'],
            'varArgs':{'%wi':'windowId'},
            'expArgs':{'windowId':'10000'}
        },
        'onIdle':{
            'text':'on Idle [secs]',
            'reqInfo':[('idleTime','int', '60')],
            'optArgs':[]
        }
    }
    Basic = {
        'onStartup':{
            'text':'on Startup',
            'reqInfo':[],
            'optArgs':[]
        },
        'onShutdown':{
            'text':'on Shutdown',
            'reqInfo':[],
            'optArgs':[]
        }
    }
    Log = {
        'onLogSimple':{
            'text':'on Log Simple',
            'reqInfo':[('matchIf','text', '') , ('rejectIf','text', '')],
            'optArgs':['logLine'],
            'varArgs':{'%ll':'logLine'},
            'expArgs':{'logLine':'16:10:31 T:13092  NOTICE:  fps: 23.976024, pwidth: 1916, pheight: 796, dwidth: 1916, dheight: 796'}
        },
        'onLogRegex':{
            'text':'on Log Regex',
            'reqInfo':[('matchIf','text', '') , ('rejectIf','text', '')],
            'optArgs':['logLine'],
            'varArgs':{'%ll':'logLine'},
            'expArgs':{'logLine':'16:10:31 T:13092  NOTICE:  fps: 23.976024, pwidth: 1916, pheight: 796, dwidth: 1916, dheight: 796'}
        }
    }
    Watchdog = {
        'onFileSystemChange':{
            'text':'on File System Change',
            'reqInfo':[('folder','folder', ''), ('patterns', 'text', ''), ('ignore_patterns', 'text', ''),('ignore_directories', 'text', ''),('recursive','bool', '')],
            'optArgs':['path', 'event'],
            'varArgs':{'%pa':'path', '%{ev':'event'},
            'expArgs':{'path':'C:\\Users\\User\\text.txt', 'event':'deleted' }
        },
    }

    def __init__(self):
        self.AllEvents = self._AllEvents()
        self.AllEventsSimple = self._AllEventsSimple()

    @staticmethod
    def mergedicts(*dicts):
        result = {}
        for d in dicts:
            result.update(d)
        return result

    @staticmethod
    def _AllEvents():
        return Events.mergedicts(Events.Player, Events.Monitor, Events.CustomLoop, Events.Basic, Events.Log, Events.Watchdog)

    @staticmethod
    def _AllEventsSimple():
        return Events._AllEvents().keys()