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

debug = False  # TODO: check
testdebug = False  # TODO: check
testTasks = False  # TODO: check
branch = 'nonrepo'

from resources.lib.utils.debugger import startdebugger

if debug:
    startdebugger()

import os
import sys
import threading
import xbmc
import xbmcaddon
import xbmcgui
import resources.lib.pubsub as PubSub_Threaded
from resources.lib.kodilogging import KodiLogger
from resources.lib.publisherfactory import PublisherFactory
from resources.lib.subscriberfactory import SubscriberFactory
from resources.lib.settings import Settings
from resources.lib.utils.kodipathtools import translatepath, setPathExecuteRW, setPathRW
from resources.lib.utils.poutil import KodiPo

kodipo = KodiPo()
_ = kodipo.getLocalizedString
log = KodiLogger.log

try:
    __version__ = xbmcaddon.Addon().getAddonInfo('version')
except RuntimeError:
    try:
        __version__ = xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('version')
    except RuntimeError:
        __version__ = 'ERROR getting version'


class Cache(object):
    publishers = None
    dispatcher = None


def createUserTasks():
    paths = [translatepath('special://addondata')]
    try:
        setPathRW(paths[0])
    except OSError:
        pass
    paths.append(os.path.join(paths[0], 'lib'))
    paths.append(os.path.join(paths[1], 'usertasks'))
    for path in paths:
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
                setPathExecuteRW(path)
            except OSError:
                pass
    for path in paths[1:]:
        fn = os.path.join(path, '__init__.py')
        if not os.path.isfile(fn):
            try:
                with open(fn, mode='w') as f:
                    f.writelines('')
                setPathExecuteRW(fn)
            except (OSError, IOError):
                pass


class MainMonitor(xbmc.Monitor):
    def __init__(self):
        super(MainMonitor, self).__init__()

    def onSettingsChanged(self):
        log(msg=_('Settings change detected - attempting to restart'))
        abortall()
        start()


def abortall():
    for p in Cache.publishers:
        try:
            p.abort()
        except threading.ThreadError as e:
            log(msg=_('Error aborting: %s - Error: %s') % (str(p), str(e)))
    Cache.dispatcher.abort()
    for p in Cache.publishers:
        p.join(0.5)
    Cache.dispatcher.join(0.5)
    if len(threading.enumerate()) > 1:
        main_thread = threading.current_thread()
        log(msg=_('Enumerating threads to kill others than main (%i)') % main_thread.ident)
        for t in threading.enumerate():
            if t is not main_thread and t.is_alive():
                log(msg=_('Attempting to kill thread: %i: %s') % (t.ident, t.name))
                try:
                    t.abort(0.5)
                except (threading.ThreadError, AttributeError):
                    log(msg=_('Error killing thread'))
                else:
                    if not t.is_alive():
                        log(msg=_('Thread killed succesfully'))
                    else:
                        log(msg=_('Error killing thread'))


def start():
    global log
    settings = Settings()
    settings.getSettings()
    kl = KodiLogger()
    if settings.general['elevate_loglevel'] is True:
        kl.setLogLevel(xbmc.LOGNOTICE)
    else:
        kl.setLogLevel(xbmc.LOGDEBUG)
    log = kl.log
    log(msg=_('Settings read'))
    Cache.dispatcher = PubSub_Threaded.Dispatcher(interval=settings.general['TaskFreq'], sleepfxn=xbmc.sleep)
    log(msg=_('Dispatcher initialized'))

    subscriberfactory = SubscriberFactory(settings, kl)
    subscribers = subscriberfactory.createSubscribers()
    for subscriber in subscribers:
        Cache.dispatcher.addSubscriber(subscriber)
    publisherfactory = PublisherFactory(settings, subscriberfactory.topics, Cache.dispatcher, kl, debug)
    publisherfactory.createPublishers()
    Cache.publishers = publisherfactory.ipublishers

    Cache.dispatcher.start()
    log(msg=_('Dispatcher started'))

    for p in Cache.publishers:
        try:
            p.start()
        except threading.ThreadError:
            raise
    log(msg=_('Publisher(s) started'))


def main():
    xbmc.log(msg=_('$$$ [kodi.callbacks] - Staring kodi.callbacks ver: %s') % str(__version__), level=xbmc.LOGNOTICE)
    if branch != 'master':
        xbmcaddon.Addon().setSetting('installed branch', branch)
    start()
    Cache.dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onStartup')))
    monitor = MainMonitor()
    log(msg=_('Entering wait loop'))
    monitor.waitForAbort()

    # Shutdown tasks
    Cache.dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown'), pid=os.getpid()))
    log(msg=_('Shutdown started'))
    abortall()
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
    log(msg=_('Creating subscriber for test'))
    subscriberfactory = SubscriberFactory(settings, testlogger)
    subscriber = subscriberfactory.createSubscriber(key)
    if subscriber is not None:
        log(msg=_('Test subscriber created successfully'))
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
        except Exception:
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
    dryrun = False
    addonid = 'script.service.kodi.callbacks'

    if len(sys.argv) > 1:
        if testdebug is True and debug is False:
            startdebugger()
            dryrun = True

        if sys.argv[1] == 'regen':
            from resources.lib.kodisettings.generate_xml import generate_settingsxml

            generate_settingsxml()
            dialog = xbmcgui.Dialog()
            msg = _('Settings Regenerated')
            dialog.ok(_('Kodi Callbacks'), msg)

        elif sys.argv[1] == 'test':
            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            from resources.lib.tests.testTasks import testTasks

            tt = testTasks()
            tt.runTests()
            dialog = xbmcgui.Dialog()
            msg = _('Native Task Testing Complete - see log for results')
            dialog.notification(_('Kodi Callbacks'), msg, xbmcgui.NOTIFICATION_INFO, 5000)

        elif sys.argv[1] == 'updatefromzip':
            from resources.lib.utils.updateaddon import UpdateAddon

            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            dialog = xbmcgui.Dialog()
            zipfn = dialog.browse(1, _('Locate zip file'), 'files', '.zip', False, False, translatepath('~'))
            if zipfn != translatepath('~'):
                if os.path.isfile(zipfn):
                    ua = UpdateAddon(addonid)
                    ua.installFromZip(zipfn, updateonly=True, dryrun=dryrun)
                else:
                    dialog.ok(_('Kodi Callbacks'), _('Incorrect path'))

        elif sys.argv[1] == 'restorebackup':
            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            dialog = xbmcgui.Dialog()
            zipfn = dialog.browse(1, _('Locate backup zip file'), 'files', '.zip', False, False,
                                  translatepath('special://addondata/backup/'))
            if zipfn != translatepath('special://addondata/backup/'):
                from resources.lib.utils.updateaddon import UpdateAddon

                ua = UpdateAddon(addonid)
                ua.installFromZip(zipfn, updateonly=False, dryrun=dryrun)

        elif sys.argv[1] == 'lselector':
            from resources.lib.utils.selector import selectordialog

            try:
                result = selectordialog(sys.argv[2:])
            except (SyntaxError, TypeError) as e:
                xbmc.log(msg='Error: %s' % str(e), level=xbmc.LOGERROR)

        elif sys.argv[1] == 'logsettings':
            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            settings = Settings()
            settings.getSettings()
            settings.logSettings()
            dialog = xbmcgui.Dialog()
            msg = _('Settings written to log')
            dialog.ok(_('Kodi Callbacks'), msg)

        elif branch != 'master' and sys.argv[1] == 'checkupdate':
            try:
                from resources.lib.utils.githubtools import processargs
            except ImportError:
                pass
            else:
                processargs(sys.argv)

        else:
            # Direct Event/Task Testing
            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            eventId = sys.argv[1]
            test(eventId)

    elif testTasks:
        KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
        startdebugger()
        from resources.lib.tests.testTasks import testTasks

        tt = testTasks()
        tt.runTests()
    else:
        if branch != 'master':
            try:
                from resources.lib.utils.githubtools import processargs
            except ImportError:
                pass
            else:
                processargs(sys.argv)
        createUserTasks()
        main()
