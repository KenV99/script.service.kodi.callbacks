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
debug = True
remote = False
testdebug = False
testTasks = False

import os
import threading

import resources.lib.pubsub as PubSub_Threaded
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib import taskdict
from resources.lib.kodilogging import KodiLogger
from resources.lib.publishers.log import LogPublisher
from resources.lib.publishers.loop import LoopPublisher
from resources.lib.publishers.monitor import MonitorPublisher
from resources.lib.publishers.player import PlayerPublisher
from resources.lib.settings import Settings
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString

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

try:
    from resources.lib.publishers.watchdog import WatchdogPublisher
except:
    from resources.lib.publishers.dummy import WatchdogPublisherDummy as WatchdogPublisher

class NotificationTask(PubSub_Threaded.Task):
    def __init__(self):
        super(NotificationTask, self).__init__()

    def run(self):
        msg = _('Task received: %s: %s') % (str(self.topic), str(self.kwargs))
        log(msg= msg)
        dialog = xbmcgui.Dialog()
        dialog.notification(_('Kodi Callbacks'), msg, xbmcgui.NOTIFICATION_INFO, 5000)


class MainMonitor(xbmc.Monitor):
    def __init__(self):
        super(MainMonitor, self).__init__()

    def onSettingsChanged(self):
        global dispatcher, publishers, log
        log(msg=_('Settings change detected - attempting to restart'))
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
        msg = _('Command for Task %s, Event %s completed succesfully!') % (taskReturn.taskId, taskReturn.eventId)
        if taskReturn.msg != '':
            msg += _('\nThe following message was returned: %s') % taskReturn.msg
        log(msg=msg)
    else:
        msg = _('ERROR encountered for Task %s, Event %s\nERROR mesage: %s') % (
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
    log(msg=_('Settings read'))
    publishers = []
    subscribers = []
    topics = []
    dispatcher = PubSub_Threaded.Dispatcher(interval=settings.general['TaskFreq'], sleepfxn=xbmc.sleep)
    log(msg=_('Dispatcher initialized'))

    for key in settings.events.keys():
        task_key = settings.events[key]['task']
        evtsettings = settings.events[key]
        topic = settings.topicFromSettingsEvent(key)
        topics.append(topic.topic)
        tasksettings = settings.tasks[task_key]
        subscriber = createSubscriber(tasksettings, evtsettings)
        if subscriber is not None:
            subscriber.addTopic(topic)
            subscriber.taskmanagers[0].taskKwargs['notify'] = settings.general['Notify']
            dispatcher.addSubscriber(subscriber)
            subscribers.append(subscriber)
            log(msg=_('Subscriber for event: %s, task: %s created') % (str(topic), task_key))
        else:
            log(loglevel=xbmc.LOGERROR, msg=_('Subscriber for event: %s, task: %s NOT created due to errors') % (str(topic), task_key))

    if not set(topics).isdisjoint(LoopPublisher.publishes) or debug is True:
        loopPublisher = LoopPublisher(dispatcher, settings.getOpenwindowids(), settings.getClosewindowids(),
                                      settings.getIdleTimes(), settings.getAfterIdleTimes(), settings.general['LoopFreq'])
        publishers.append(loopPublisher)
        log(msg=_('Loop Publisher initialized'))
    if not set(topics).isdisjoint(PlayerPublisher.publishes)or debug is True:
        playerPublisher = PlayerPublisher(dispatcher)
        publishers.append(playerPublisher)
        log(msg=_('Player Publisher initialized'))
    if not set(topics).isdisjoint(MonitorPublisher.publishes)or debug is True:
        monitorPublisher = MonitorPublisher(dispatcher)
        monitorPublisher.jsoncriteria = settings.getJsonNotifications()
        publishers.append(monitorPublisher)
        log(msg=_('Monitor Publisher initialized'))
    if not set(topics).isdisjoint(LogPublisher.publishes)or debug is True:
        logPublisher = LogPublisher(dispatcher, settings.general['LogFreq'])
        logPublisher.add_simple_checks(settings.getLogSimples())
        logPublisher.add_regex_checks(settings.getLogRegexes())
        publishers.append(logPublisher)
        log(msg=_('Log Publisher initialized'))
    if not set(topics).isdisjoint(WatchdogPublisher.publishes)or debug is True:
        watchdogPublisher = WatchdogPublisher(dispatcher, settings.getWatchdogSettings())
        publishers.append(watchdogPublisher)
        log(msg=_('Watchdog Publisher initialized'))

    dispatcher.start()
    log(msg=_('Dispatcher started'))
    for p in publishers:
        try:
            p.start()
        except Exception as e:
            raise
    log(msg=_('Publisher(s) started'))
    return dispatcher, publishers


def main():
    global dispatcher, publishers
    xbmc.log(msg=_('$$$ [kodi.callbacks] Staring kodi.callbacks ver: %s') % str(xbmcaddon.Addon().getAddonInfo('version')), level=xbmc.LOGNOTICE)
    dispatcher, publishers = start()
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onStartup')))
    monitor = MainMonitor()
    log(msg=_('Entering wait loop'))
    # xbmc.sleep(2000)
    # dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown'), pid=os.getpid()))
    monitor.waitForAbort()

    # Shutdown tasks
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown'), pid=os.getpid()))
    xbmc.sleep(500)
    log(msg=_('Shutdown started'))
    for p in publishers:
        try:
            p.abort()
        except Exception as e:
            log(msg=_('Error aborting: %s - Error: %s') % (str(p), str(e)))
    dispatcher.abort()
    xbmc.sleep(1000)
    if len(threading.enumerate()) > 1:
        main_thread = threading.current_thread()
        log(msg=_('Enumerating threads to kill others than main (%i)') % main_thread.ident)
        for t in threading.enumerate():
            if t is not main_thread:
                log(msg=_('Attempting to kill thread: %i: %s') % (t.ident, t.name))
                xbmc.sleep(25)
                try:
                    t.abort(0.525)
                except:
                    log(msg=_('Error killing thread'))
                else:
                    if not t.is_alive():
                        log(msg=_('Thread killed succesfully'))
    log(msg='Shutdown complete')


def test(key):
    global log
    log = KodiLogger.log
    import resources.lib.tests.direct_test as direct_test
    from resources.lib.events import Events
    import traceback
    log(msg=_('Running Test for Event: %s') % key)
    events = Events().AllEvents
    settings = Settings()
    settings.getSettings()
    if settings.general['elevate_loglevel'] is True:
        KodiLogger.setLogLevel(xbmc.LOGNOTICE)
    else:
        KodiLogger.setLogLevel(xbmc.LOGDEBUG)
    log(msg=_('Settings for test read'))
    evtsettings = settings.events[key]
    topic = settings.topicFromSettingsEvent(key)
    task_key = settings.events[key]['task']
    tasksettings = settings.tasks[task_key]
    testlogger = direct_test.TestLogger()
    testlog = testlogger.log
    log(msg=_('Creating subscriber for test'))
    subscriber = createSubscriber(tasksettings, evtsettings, log=testlog)
    if subscriber is not None:
        log(msg=_('Test subscriber created successfully'))
        subscriber.addTopic(topic)
        subscriber.taskmanagers[0].taskKwargs['notify'] = settings.general['Notify']
        try:
            kwargs = events[evtsettings['type']]['expArgs']
        except KeyError:
            kwargs = {}
        testRH = direct_test.TestHandler(direct_test.testMsg(subscriber.taskmanagers[0], tasksettings, kwargs))
        subscriber.taskmanagers[0].returnHandler = testRH.testReturnHandler
        # Run test
        log(msg=_('Running test'))
        nMessage = PubSub_Threaded.Message(topic=topic, **kwargs)
        try:
            subscriber.notify(nMessage)
        except:
            msg = _('Unspecified error during testing')
            e = sys.exc_info()[0]
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
            log(msg=msg)
            msgList = msg.split('\n')
            import resources.lib.dialogtb as dialogtb
            dialogtb.show_textbox('Error', msgList)
    else:
        log(msg=_('Test subscriber creation failed due to errors'))
        msgList = testlogger.retrieveLogAsList()
        import resources.lib.dialogtb as dialogtb
        dialogtb.show_textbox('Error', msgList)

    xbmc.sleep(2000)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if testdebug is True:
            sys.path.append('C:\\Program Files (x86)\\JetBrains\\PyCharm 5.0.2\\debug-eggs\\pycharm-debug.egg')
            import pydevd
            pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)
        if sys.argv[1] == 'regen':
            from resources.lib.utils.xml_gen import generate_settingsxml
            generate_settingsxml()
        elif sys.argv[1] == 'test':
            from resources.lib.tests.testTasks import testTasks
            tt = testTasks()
            tt.runTests()
            dialog = xbmcgui.Dialog()
            msg = _('Native Task Testing Complete - see log for results')
            dialog.notification('Kodi Callbacks', msg, xbmcgui.NOTIFICATION_INFO, 5000)
        else:
            eventId = sys.argv[1]
            test(eventId)
    elif testTasks:
        from resources.lib.tests.testTasks import testTasks
        tt = testTasks()
        tt.runTests()

    else:
        main()
