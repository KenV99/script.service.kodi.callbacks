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
testdebug = False

import threading
import resources.lib.pubsub as PubSub_Threaded
from resources.lib import taskdict
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.settings import Settings
from resources.lib.kodilogging import KodiLogger
from resources.lib.publishers.log import LogPublisher
from resources.lib.publishers.loop import LoopPublisher
from resources.lib.publishers.monitor import MonitorPublisher
from resources.lib.publishers.player import PlayerPublisher

log = None
dispatcher = None
publishers = None

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


class NotificationTask(PubSub_Threaded.Task):
    def __init__(self):
        super(NotificationTask, self).__init__()

    def run(self):
        msg = 'Task received: %s: %s' % (str(self.topic), str(self.kwargs))
        log(msg= msg)
        dialog = xbmcgui.Dialog()
        dialog.notification('Kodi Callbacks', msg, xbmcgui.NOTIFICATION_INFO, 5000)


class MainMonitor(xbmc.Monitor):
    def __init__(self):
        super(MainMonitor, self).__init__()

    def onSettingsChanged(self):
        global dispatcher, publishers, log
        log(msg='Settings change detected - attempting to restart')
        for p in publishers:
            p.abort(0.525)
        dispatcher.abort(0.25)
        start()


def createTaskT(taskSettings, eventSettings, xlog):
    global log
    if xlog is None:
        xlog = log
    mytask = taskdict[taskSettings['type']]['class']
    taskKwargs = taskSettings
    if mytask.validate(taskKwargs, xlog=xlog) is True:
        return mytask, taskKwargs
    else:
        return None, None


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


def createSubscriber(tasksettings, eventSettings, retHandler=returnHandler, log=None):
    taskT, taskKwargs = createTaskT(tasksettings, eventSettings, log)
    if taskT is not None:
        tm = PubSub_Threaded.TaskManager(taskT, taskid=eventSettings['task'], userargs=eventSettings['userargs'],
                                         **taskKwargs)
        tm.returnHandler = retHandler
        subscriber = PubSub_Threaded.Subscriber(logger=KodiLogger)
        subscriber.addTaskManager(tm)
        return subscriber


def start():
    global dispatcher, publishers, log
    settings = Settings()
    settings.getSettings()
    if settings.general['elevate_loglevel'] is True:
        KodiLogger.setLogLevel(xbmc.LOGNOTICE)
    else:
        KodiLogger.setLogLevel(xbmc.LOGDEBUG)
    log = KodiLogger.log
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
            subscriber.taskmanagers[0].taskKwargs['notify'] = settings.general['Notify']
            dispatcher.addSubscriber(subscriber)
            subscribers.append(subscriber)
            log(msg='Subscriber for event: %s, task: %s created' % (str(topic), task_key))
        else:
            log(loglevel=xbmc.LOGERROR, msg='Subscriber for event: %s, task: %s NOT created due to errors' % (str(topic), task_key))

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
    global dispatcher, publishers
    xbmc.log(msg='$$$ [kodi.callbacks] Staring kodi.callbacks ver: %s' % str(xbmcaddon.Addon().getAddonInfo('version')), level=xbmc.LOGNOTICE)
    dispatcher, publishers = start()
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onStartup')))
    monitor = MainMonitor()
    log(msg='Entering wait loop')
    monitor.waitForAbort()

    # Shutdown tasks
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown')))
    log(msg='Shutdown started')
    for p in publishers:
        try:
            p.abort()
        except Exception as e:
            log(msg='Error aborting: %s - Error: %s' % (str(p), str(e)))
    dispatcher.abort()
    xbmc.sleep(1000)
    if len(threading.enumerate()) > 1:
        main_thread = threading.current_thread()
        log(msg='Enumerating threads to kill others than main (%i)' % main_thread.ident)
        for t in threading.enumerate():
            if t is not main_thread:
                log(msg='Attempting to kill thread: %i: %s' % (t.ident, t.name))
                xbmc.sleep(25)
                try:
                    t.abort(0.525)
                except:
                    log(msg='Error killing thread')
                else:
                    if not t.is_alive():
                        log(msg='Thread killed succesfully')
    log(msg='Shutdown complete')


def test(key):
    global log
    log = KodiLogger.log
    import resources.lib.tests.direct_test as direct_test
    from resources.lib.events import Events
    log(msg='Running Test for Event: %s' % key)
    events = Events().AllEvents
    settings = Settings()
    settings.getSettings()
    if settings.general['elevate_loglevel'] is True:
        KodiLogger.setLogLevel(xbmc.LOGNOTICE)
    else:
        KodiLogger.setLogLevel(xbmc.LOGDEBUG)
    log(msg='Settings for test read')
    evtsettings = settings.events[key]
    topic = settings.topicFromSettingsEvent(key)
    task_key = settings.events[key]['task']
    tasksettings = settings.tasks[task_key]
    testlogger = direct_test.TestLogger()
    testlog = testlogger.log
    log(msg='Creating subscriber for test')
    subscriber = createSubscriber(tasksettings, evtsettings, log=testlog)
    if subscriber is not None:
        log(msg='Test subscriber created successfully')
        subscriber.addTopic(topic)
        subscriber.taskmanagers[0].taskKwargs['notify'] = settings.general['Notify']
        kwargs = events[evtsettings['type']]['expArgs']
        testRH = direct_test.TestHandler(direct_test.testMsg(subscriber.taskmanagers[0], tasksettings, kwargs))
        subscriber.taskmanagers[0].returnHandler = testRH.testReturnHandler
        # Run test
        log(msg='Running test')
        nMessage = PubSub_Threaded.Message(topic=topic, **kwargs)
        try:
            subscriber.notify(nMessage)
        except Exception as e:
            pass
    else:
        log(msg='Test subscriber creation failed due to errors')
        msgList = testlogger.retrieveLogAsList()
        import resources.lib.dialogtb as dialogtb
        dialogtb.show_textbox('Error', msgList)

    xbmc.sleep(100000)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if testdebug is True:
            sys.path.append('C:\\Program Files (x86)\\JetBrains\\PyCharm 5.0.2\\debug-eggs\\pycharm-debug.egg')
            import pydevd
            pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)
        if sys.argv[1] == 'regen':
            from resources.lib.xml_gen import generate_settingsxml
            generate_settingsxml()
        else:
            eventId = sys.argv[1]
            test(eventId)
    else:
        main()
