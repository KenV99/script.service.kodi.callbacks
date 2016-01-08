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
debug = False
remote = False

import threading
import resources.lib.PubSub_Threaded as PubSub_Threaded
import resources.lib.Tasks as Tasks
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.Settings import Settings
from resources.lib.kodilogging import KodiLogger
from resources.lib.publishers.log import LogPublisher
from resources.lib.publishers.loop import LoopPublisher
from resources.lib.publishers.monitor import MonitorPublisher
from resources.lib.publishers.player import PlayerPublisher

log = KodiLogger.log

if debug:
    import sys

    if remote:
        sys.path.append('C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\service.kodi.callbacks\\resources\\lib\\'
                        'pycharm-debug.py3k\\')
        import pydevd

        pydevd.settrace('192.168.1.103', port=51234, stdoutToServer=True, stderrToServer=True)
    else:
        sys.path.append('C:\\Program Files (x86)\\JetBrains\\PyCharm 5.0.2\\debug-eggs\\pycharm-debug.egg')
        import pydevd

        pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)

#
# class NotificationTask(PubSub_Threaded.Task):
#     def __init__(self):
#         super(NotificationTask, self).__init__()
#
#     def run(self):
#         msg = 'Task received: %s: %s' % (str(self.topic), str(self.kwargs))
#         log(msg='@@@@@ xbmc.callbacks2 %s' % msg)
#         dialog = xbmcgui.Dialog()
#         dialog.notification('xbmc.callabacks2', msg, xbmcgui.NOTIFICATION_INFO, 5000)


class MainMonitor(xbmc.Monitor):
    def __init__(self, publishers, dispatcher):
        super(MainMonitor, self).__init__()
        self.publishers = publishers
        self.dispatcher = dispatcher

    def onSettingsChanged(self):
        log(msg='Settings change detected - attempting to restart')
        for p in self.publishers:
            p.abort()
        self.dispatcher.abort()
        start()


def createTaskT(taskSettings, eventSettings, log=xbmc.log):
    userargs = eventSettings['userargs']
    if taskSettings['type'] == 'script':
        cmdstr = taskSettings['scriptfile']
        taskKwargs = {'needs_shell': taskSettings['shell']}
        if Tasks.WorkerScript.check(cmdstr, userargs, xlog=log) is True:
            ret = Tasks.WorkerScript
            return cmdstr, ret, taskKwargs
        else:
            return None, None, None
    elif taskSettings['type'] == 'python':
        cmdstr = taskSettings['pythondoc']
        taskKwargs = {'runType': 'builtin'}
        if Tasks.WorkerPy.check(cmdstr, userargs, xlog=log) is True:
            ret = Tasks.WorkerPy
            return cmdstr, ret, taskKwargs
        else:
            return None, None, None
    elif taskSettings['type'] == 'builtin':
        cmdstr = taskSettings['builtin']
        ret = Tasks.WorkerBuiltin
        return cmdstr, ret, {}
    elif taskSettings['type'] == 'http':
        cmdstr = taskSettings['http']
        if Tasks.WorkerHTTP.check(cmdstr, userargs, xlog=log) is True:
            ret = Tasks.WorkerHTTP
            return cmdstr, ret, {}
        else:
            return None, None, None
    else:
        return None, None, None


def returnHandler(taskReturn):
    assert isinstance(taskReturn, PubSub_Threaded.TaskReturn)
    if taskReturn.iserror is False:
        msg = 'Command for Task %s, Event %s completed succesfully!' % (taskReturn.taskId, taskReturn.eventId)
        if taskReturn.msg != '':
            msg += '\nThe following message was returned: %s' % taskReturn.msg
        log(msg=msg)
    else:
        msg = 'ERROR encountered for Task %s, Event %s\nERROR mesage: %s' % (
            taskReturn.taskId, taskReturn.eventId, taskReturn.msg)
        log(loglevel=xbmc.LOGERROR, msg=msg)


def createSubscriber(tasksettings, eventSettings, retHandler=returnHandler, log=xbmc.log):
    cmd_str, taskT, taskKwargs = createTaskT(tasksettings, eventSettings, log)
    if taskT is not None:
        tm = PubSub_Threaded.TaskManager(taskT, maxrunning=tasksettings['maxrunning'],
                                         refractory_period=tasksettings['refractory'], max_runs=tasksettings['maxruns'],
                                         cmd_str=cmd_str, userargs=eventSettings['userargs'],
                                         taskid=eventSettings['task'], **taskKwargs)
        tm.returnHandler = retHandler
        subscriber = PubSub_Threaded.Subscriber(logger=KodiLogger)
        subscriber.addTaskManager(tm)
        return subscriber


def start():
    # global settings, dispatcher, publishers, topics
    settings = Settings()
    settings.getSettings()
    log(msg='Settings read')
    publishers = []
    subscribers = []
    topics = []
    dispatcher = PubSub_Threaded.Dispatcher(interval=settings.general['TaskFreq'], sleepfxn=xbmc.sleep)
    log(msg='Dispatcher initialized')

    for key in settings.events.keys():
        evtsettings = settings.events[key]
        topic = settings.topicFromSettingsEvent(key)
        topics.append(topic.topic)
        task_key = settings.events[key]['task']
        tasksettings = settings.tasks[task_key]
        subscriber = createSubscriber(tasksettings, evtsettings)
        if subscriber is not None:
            subscriber.addTopic(topic)
            dispatcher.addSubscriber(subscriber)
            subscribers.append(subscriber)
            log(msg='Subsriber for event: %s, task: %s created' % (str(topic), task_key))
    if not set(topics).isdisjoint(LoopPublisher.publishes):
        loopPublisher = LoopPublisher(dispatcher, settings.openwindowids(), settings.closewindowids(),
                                      settings.getIdleTimes(), settings.general['LoopFreq'])
        publishers.append(loopPublisher)
        log(msg='Loop Publisher initialized')
    if not set(topics).isdisjoint(PlayerPublisher.publishes):
        playerPublisher = PlayerPublisher(dispatcher)
        publishers.append(playerPublisher)
        log(msg='Player Publisher initialized')
    if not set(topics).isdisjoint(MonitorPublisher.publishes):
        monitorPublisher = MonitorPublisher(dispatcher)
        monitorPublisher.jsoncriteria = settings.getJsonNotifications()
        publishers.append(monitorPublisher)
        log(msg='Monitor Publisher initialized')
    if not set(topics).isdisjoint(LogPublisher.publishes):
        logPublisher = LogPublisher(dispatcher, settings.general['LogFreq'])
        logPublisher.add_simple_checks(settings.getLogSimples())
        logPublisher.add_regex_checks(settings.getLogRegexes())
        publishers.append(logPublisher)
        log(msg='Log Publisher initialized')

    dispatcher.start()
    log(msg='Dispatcher started')
    for p in publishers:
        try:
            p.start()
        except Exception as e:
            raise
    log(msg='Publisher(s) started')
    return dispatcher, publishers


def main():
    log(msg='Staring kodi.callbacks ver: %s' % str(xbmcaddon.Addon().getAddonInfo('version')))
    dispatcher, publishers = start()
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onStartup')))
    monitor = MainMonitor(publishers, dispatcher)
    log(msg='Entering wait loop')
    monitor.waitForAbort()
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown')))
    log(msg='Shutdown started')
    for p in publishers:
        try:
            p.abort()
        except Exception as e:
            log(msg='Error aborting: %s - Error: %s' % (str(p), str(e)))
    dispatcher.abort()
    xbmc.sleep(1000)
    main_thread = threading.current_thread()
    log(msg='Enumerating threads to kill others than main (%i)' % main_thread.ident)
    for t in threading.enumerate():
        if t is not main_thread:
            log(msg='Attempting to kill thread: %i: %s' % (t.ident, t.name))
            xbmc.sleep(25)
            try:
                t.exit()
            except:
                log(msg='Error killing thread')
            else:
                xbmc.log(msg='Thread killed succesfully')
    log(msg='Shutdown complete')


def test(key):
    # sys.path.append('C:\\Program Files (x86)\\JetBrains\\PyCharm 5.0.2\\debug-eggs\\pycharm-debug.egg')
    # import pydevd
    # pydevd.settrace('localhost', port=51235, stdoutToServer=True, stderrToServer=True, suspend=False)
    import resources.lib.tests.DirectTsting as DT
    from resources.lib.events import Events
    log(msg='Running Test for Event: %s' % key)
    events = Events().AllEvents
    settings = Settings()
    settings.getSettings()
    log(msg='Settings for test read')
    evtsettings = settings.events[key]
    topic = settings.topicFromSettingsEvent(key)
    task_key = settings.events[key]['task']
    tasksettings = settings.tasks[task_key]
    testlogger = DT.TestLogger()
    testlog = testlogger.log
    log(msg='Creating subscriber for test')
    subscriber = createSubscriber(tasksettings, evtsettings, log=testlog)
    if subscriber is not None:
        log(msg='Test subscriber created successfully')
        subscriber.addTopic(topic)
        kwargs = events[evtsettings['type']]['expArgs']
        testRH = DT.TestHandler(DT.testMsg(subscriber.taskmanagers[0], tasksettings, kwargs))
        subscriber.taskmanagers[0].returnHandler = testRH.testReturnHandler
        # Run test
        log(msg='Running test')
        nMessage = PubSub_Threaded.Message(topic=topic, **kwargs)

        subscriber.notify(nMessage)
    else:
        log(msg='Test subscriber creation failed')
        msgList = testlogger.retrieveLogAsList()
        import resources.lib.dialogtb as dialogtb
        dialogtb.show_textbox('Error', msgList)

    xbmc.sleep(10000)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        eventId = sys.argv[1]
        test(eventId)
    else:
        main()
