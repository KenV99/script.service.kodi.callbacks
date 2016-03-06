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

import os
import sys


def startdebugger():
    debugegg = 'C:\\Program Files (x86)\\JetBrains\\PyCharm 5.0.2\\debug-eggs\\pycharm-debug.egg'
    if os.path.exists(debugegg):
        sys.path.append(debugegg)
        try:
            import pydevd
        except ImportError:
            pass
        else:
            pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)


if debug:
    startdebugger()

import threading
import xbmc
import xbmcaddon
import xbmcgui
import resources.lib.pubsub as PubSub_Threaded
from resources.lib.kodilogging import KodiLogger
from resources.lib.publisherfactory import PublisherFactory
from resources.lib.subscriberfactory import SubscriberFactory
from resources.lib.settings import Settings
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


class MainMonitor(xbmc.Monitor):
    def __init__(self, dispatcher, publishers):
        super(MainMonitor, self).__init__()
        self.dispatcher = dispatcher
        self.publishers = publishers

    def onSettingsChanged(self):
        log(msg=_('Settings change detected - attempting to restart'))
        for p in self.publishers:
            p.abort(0.525)
        self.dispatcher.abort(0.25)
        start()


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
    dispatcher = PubSub_Threaded.Dispatcher(interval=settings.general['TaskFreq'], sleepfxn=xbmc.sleep)
    log(msg=_('Dispatcher initialized'))

    subscriberfactory = SubscriberFactory(settings, kl)
    subscribers = subscriberfactory.createSubscribers()
    for subscriber in subscribers:
        dispatcher.addSubscriber(subscriber)
    publisherfactory = PublisherFactory(settings, subscriberfactory.topics, dispatcher, kl, debug)
    publisherfactory.createPublishers()
    publishers = publisherfactory.ipublishers

    dispatcher.start()
    log(msg=_('Dispatcher started'))

    for p in publishers:
        try:
            p.start()
        except threading.ThreadError:
            raise
    log(msg=_('Publisher(s) started'))
    return dispatcher, publishers


def main():
    xbmc.log(msg=_('$$$ [kodi.callbacks] - Staring kodi.callbacks ver: %s') % str(__version__), level=xbmc.LOGNOTICE)
    dispatcher, publishers = start()
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onStartup')))
    monitor = MainMonitor(dispatcher, publishers)
    log(msg=_('Entering wait loop'))
    monitor.waitForAbort()

    # Shutdown tasks
    dispatcher.q_message(PubSub_Threaded.Message(PubSub_Threaded.Topic('onShutdown'), pid=os.getpid()))
    xbmc.sleep(500)
    log(msg=_('Shutdown started'))
    for p in publishers:
        try:
            p.abort()
        except threading.ThreadError as e:
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
                except threading.ThreadError:
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
    GHUser = 'KenV99'
    reponame = addonid

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
            from resources.lib.utils.kodipathtools import translatepath
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
            from resources.lib.utils.kodipathtools import translatepath

            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            dialog = xbmcgui.Dialog()
            zipfn = dialog.browse(1, _('Locate backup zip file'), 'files', '.zip', False, False,
                                  translatepath('special://addondata/backup/'))
            if zipfn != translatepath('special://addondata/backup/'):
                from resources.lib.utils.updateaddon import UpdateAddon

                ua = UpdateAddon(addonid)
                ua.installFromZip(zipfn, updateonly=False, dryrun=dryrun)

        elif sys.argv[1] == 'checkupdate':
            from resources.lib.utils.githubtools import GitHubTools

            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            branchname = xbmcaddon.Addon().getSetting('repobranchname')
            downloadnew, ghversion, currentversion = GitHubTools.checkForDownload(GHUser, reponame, branchname, addonid)
            dialog = xbmcgui.Dialog()
            if downloadnew is True:
                answer = dialog.yesno(_('New version available for branch: %s' % branchname), line1=_('Current version: %s') % currentversion,
                                      line2=_('Available version: %s') % ghversion,
                                      line3=_('Download and install?'))
            else:
                answer = dialog.yesno(_('A new version is not available for branch: %s' % branchname), line1='Current version: %s' % currentversion,
                                      line2=_('Available version: %s') % ghversion,
                                      line3=_('Download and install anyway?'))
            if answer != 0:
                silent = (xbmcaddon.Addon().getSetting('silent_install') == 'true')
                GitHubTools.downloadAndInstall(GHUser, reponame, addonid, branchname, dryrun=dryrun,
                                               updateonly=downloadnew, silent=silent)

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
        from resources.lib.utils.githubtools import GitHubTools

        GitHubTools.updateSettingsWithBranches('repobranchname', GHUser, reponame)
        if xbmcaddon.Addon().getSetting('autodownload') == 'true':
            silent = (xbmcaddon.Addon().getSetting('silent_install') == 'true')
            branchname = xbmcaddon.Addon().getSetting('repobranchname')
            GitHubTools.downloadAndInstall(GHUser, reponame, addonid, branchname, dryrun=dryrun, updateonly=True,
                                           silent=silent)
        main()
