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
import xbmcaddon
from resources.lib.PubSub_Threaded import Topic
from resources.lib.events import Events
from resources.lib.kodilogging import log
try:
    addonid = xbmcaddon.Addon().id
except:
    addonid = 'service.kodi.callbacks'

def get(settingid, var_type):
    t = xbmcaddon.Addon(addonid).getSetting(settingid)
    if var_type == 'text':
        return t
    elif var_type == 'int':
        try:
            return int(t)
        except:
            log(msg='TYPE ERROR for variable %s. Expected int got "%s"' % (settingid, t))
            return 0
    elif var_type == 'bool':
        if t == 'false':
            return False
        else:
            return True
    else:
        log(msg='ERROR Could not process variable %s = "%s"' % (settingid, t))
        return None

class Settings(object):
    allevents = Events().AllEvents
    taskSuffixes = {'general':[['type', 'text'], ['maxrunning', 'int'], ['maxruns','int'], ['refractory', 'int']],
                    'script':[['scriptfile','text'], ['shell','bool']],
                    'python':[['pythondoc','text']],
                    'builtin':[['builtin','text']],
                    'http':[['http','text']]
                    }
    eventsReverseLookup = None

    def __init__(self):
        self.tasks = {}
        self.events = {}
        self.general = {}
        rl = {}
        for key in Settings.allevents.keys():
            evt = Settings.allevents[key]
            rl[evt['text']] = key
        Settings.eventsReverseLookup = rl

    def getSettings(self):
        self.getTaskSettings()
        self.getEventSettings()
        self.getGeneralSettings()

    def getTaskSettings(self):
        for i in xrange(1,11):
            pid = 'T%s' % str(i)
            tsk = self.getTaskSetting(pid)
            if tsk is not None:
                self.tasks[pid] = tsk

    def getTaskSetting(self, pid):
        tsk = {}
        for suff in Settings.taskSuffixes['general']:
            tsk[suff[0]] = get('%s.%s' % (pid,suff[0]), suff[1])
        if tsk['type'] == 'none':
            return None
        for suff in Settings.taskSuffixes[tsk['type']]:
            tsk[suff[0]] = get('%s.%s' % (pid,suff[0]), suff[1])
        return tsk

    def getEventSettings(self):
        for i in xrange(1,11):
            pid = "E%s" % str(i)
            evt = self.getEventSetting(pid)
            if evt is not None:
                self.events[pid] = evt

    def getEventSetting(self, pid):
        evt = {}
        et = get('%s.type' % pid, 'text')
        if et == 'None':
            return
        else:
            et = Settings.eventsReverseLookup[et]
            evt['type'] = et
        tsk = get('%s.task' % pid,'text')
        evt['task'] = 'T%s' % int(tsk[5:])
        for ri in Settings.allevents[et]['reqInfo']:
            evt[ri[0]] = get('%s.%s' % (pid,ri[0]), ri[1])
        evt['userargs'] = get('%s.userargs' % pid, 'text')

        # for oa in Settings.allevents[et]['optArgs']:
        #     evt[oa] = get('%s.%s' % (pid, oa),'bool')
        # evt['eventId'] = get('%s.eventId' % pid, 'bool')
        # evt['taskId'] = get('%s.taskId' % pid, 'bool')
        return evt

    def getTestEventSettings(self, taskId):
        evt = {}
        evt['type'] = 'onTest'
        evt['task'] = taskId
        for oa in Settings.allevents['onTest']['optArgs']:
            evt[oa] = True
        evt['eventId'] = True
        evt['taskId'] = True
        return evt

    def getGeneralSettings(self):
        polls = ['LoopFreq', 'LogFreq', 'TaskFreq']
        self.general['Notify'] = get('Notify','bool')
        for p in polls:
            self.general[p] = get(p,'int')

    def openwindowids(self):
        ret = []
        for evtkey in self.events.keys():
            evt = self.events[evtkey]
            if evt['type'] == 'onWindowOpen':
                ret.append(evt['windowIdO'])
        return ret

    def closewindowids(self):
        ret = []
        for evtkey in self.events.keys():
            evt = self.events[evtkey]
            if evt['type'] == 'onWindowClose':
                ret.append(evt['windowIdC'])
        return ret

    def getEventsByType(self, eventType):
        ret = []
        for key in self.events.keys():
            evt = self.events[key]
            if evt['type'] == eventType:
                evt['key'] = key
                ret.append(evt)
        return ret

    def getIdleTimes(self):
        idleEvts = self.getEventsByType('onIdle')
        ret = {}
        for evt in idleEvts:
            ret[evt['key']] = int(evt['idleTime'])
        return ret

    def getJsonNotifications(self):
        jsonEvts = self.getEventsByType('onNotification')
        ret = []
        dic = {}
        for evt in jsonEvts:
            dic['eventId'] = evt['eventId']
            dic['sender'] = evt['reqInfo']['sender']
            dic['method'] = evt['regInfo']['method']
            dic['data'] = evt['reqInfo']['data']
            ret.append(dic)
        return ret

    def getLogSimples(self):
        evts = self.getEventsByType('onLogSimple')
        ret = []
        for evt in evts:
            ret.append([evt['matchIf'], evt['rejectIf']])
        return ret

    def getLogRegexes(self):
        evts = self.getEventsByType('onLogSimple')
        ret = []
        for evt in evts:
            ret.append([evt['matchIf'], evt['rejectIf']])
        return ret

    def topicFromSettingsEvent(self, key):
        top = self.events[key]['type']
        if top == 'onIdle':
            return Topic(top, key)
        elif top == 'onWindowOpen':
            return Topic(top, str(self.events[key]['windowIdO']))
        elif top == 'onWindowClose':
            return Topic(top, str(self.events[key]['windowIdC']))
        elif top == 'onNotification':
            return Topic(top, key)
        else:
            return Topic(top)