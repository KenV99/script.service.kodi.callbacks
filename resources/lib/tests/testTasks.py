#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2016 KenV99
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
import os
import sys
import Queue
import time
import traceback
import json
from resources.lib import taskdict
from resources.lib.pubsub import Topic, TaskManager
from resources.lib.events import Events
from resources.lib.kodilogging import log
import xbmc, xbmcaddon
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString
events = Events().AllEvents

testdir = os.path.join(xbmcaddon.Addon('service.kodi.callbacks').getAddonInfo('path'), 'resources', 'lib', 'tests')

def is_xbmc_debug():
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettings", "params":'
                                     ' { "filter":{"section":"system", "category":"debug"} } }')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    if json_response.has_key('result') and json_response['result'].has_key('settings') and json_response['result']['settings'] is not None:
        for item in json_response['result']['settings']:
            if item["id"] == "debug.showloginfo":
                if item["value"] is True:
                    return True
                else:
                    return False



class testTasks(object):
    def __init__(self):
        self.task = None
        self.q = Queue.Queue()

    def testHttp(self):
        self.task = taskdict['http']['class']
        taskKwargs = {'http':'http://localhost:9091/jsonrpc', 'user':'', 'pass':'', 'type':'http', 'notify':False}
        userargs = '?request={"jsonrpc": "2.0", "id": 1, "method":"Application.Setmute", "params":{"mute":"toggle"}}'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        try:
            tr = self.q.get(timeout=1)
        except Queue.Empty:
            raise Queue.Empty('testHttp never returned')
        else:
            tm.start(topic, **runKwargs)  # Toggle Mute again
        if tr.iserror is True:
            log(loglevel=xbmc.LOGERROR, msg=_('testHttp returned with an error: %s') % tr.msg)
        if tr.msg.startswith('{"id":1,"jsonrpc":"2.0","result":') is False:
            raise AssertionError(_('Http test failed'))

    def returnHandler(self, taskReturn):
        self.q.put_nowait(taskReturn)

    def testBuiltin(self):
        start_debug = is_xbmc_debug()
        self.task = taskdict['builtin']['class']
        taskKwargs = {'builtin':'ToggleDebug', 'type':'builtin', 'notify':False}
        userargs = ''
        tm = TaskManager(self.task,1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        topic = Topic('onPlayBackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        time.sleep(1)
        debug = is_xbmc_debug()
        tm.start(topic, **runKwargs)
        if debug == start_debug:
            raise AssertionError(_('Builtin test failed'))


    def testScriptNoShell(self):
        self.task = taskdict['script']['class']
        outfile = os.path.join(testdir, 'scriptoutput.txt')
        try:
            os.remove(outfile)
        except:
            pass
        if sys.platform.startswith('win'):
            testfile = 'tstScript.bat'
        else:
            testfile = 'tstScript.sh'
        taskKwargs = {'scriptfile':os.path.join(testdir, testfile),
                      'use_shell':False, 'type':'script', 'waitForCompletion': True, 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        if tr.iserror is True:
            log(loglevel=xbmc.LOGERROR, msg=_('testScriptNoShell returned with an error: %s') % tr.msg)
        try:
            with open(outfile, 'r') as f:
                retArgs = f.readline()
        except OSError:
            retArgs = ''
        try:
            os.remove(outfile)
        except OSError:
            pass
        if retArgs.strip('\n') != userargs:
            raise AssertionError(_('Script without shell test failed'))

    def testScriptShell(self):
        self.task = taskdict['script']['class']
        outfile = os.path.join(testdir, 'scriptoutput.txt')
        try:
            os.remove(outfile)
        except:
            pass
        if sys.platform.startswith('win'):
            testfile = 'tstScript.bat'
        else:
            testfile = 'tstScript.sh'
        taskKwargs = {'scriptfile':os.path.join(testdir, testfile),
                      'use_shell':True, 'type':'script', 'waitForCompletion': True, 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        if tr.iserror is True:
            log(loglevel=xbmc.LOGERROR, msg=_('testScriptShell returned with an error: %s') % tr.msg)
        try:
            with open(outfile, 'r') as f:
                retArgs = f.readline()
        except Exception as e:
            retArgs = ''
        try:
            os.remove(outfile)
        except OSError:
            pass
        if retArgs.strip('\n') != userargs:
            raise AssertionError(_('Script with shell test failed'))


    def testPythonImport(self):
        self.task = taskdict['python']['class']
        taskKwargs = {'pythonfile':os.path.join(testdir,'tstPythonGlobal.py'),
                      'import':True, 'type':'python', 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        if tr.iserror is True:
            log(loglevel=xbmc.LOGERROR, msg=_('testPythonImport returned with an error: %s') % tr.msg)
        try:
            retArgs = sys.modules['__builtin__'].__dict__['testReturn']
        except KeyError:
            retArgs = sys.modules['builtins'].__dict__['testReturn']
        finally:
            try:
                sys.modules['__builtin__'].__dict__.pop('testReturn', None)
            except KeyError:
                sys.modules['builtins'].__dict__.pop('testReturn', None)
        if ' '.join(retArgs[0]) != userargs:
            raise AssertionError(_('Python import test failed'))

    def testPythonExternal(self):
        self.task = taskdict['python']['class']
        taskKwargs = {'pythonfile':os.path.join(testdir, 'tstPythonGlobal.py'),
                      'import':True, 'type':'python', 'notify':False}
        userargs = 'jkl mno:pqr'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        if tr.iserror is True:
            log(loglevel=xbmc.LOGERROR, msg=_('testPythonExternal returned with an error: %s') % tr.msg)
        try:
            retArgs = sys.modules['__builtin__'].__dict__['testReturn']
        except KeyError:
            retArgs = sys.modules['builtins'].__dict__['testReturn']
        finally:
            try:
                sys.modules['__builtin__'].__dict__.pop('testReturn', None)
            except KeyError:
                sys.modules['builtins'].__dict__.pop('testReturn', None)
        if ' '.join(retArgs[0]) != userargs:
            raise AssertionError(_('Python external test failed'))

    def runTests(self):
        tests = [self.testHttp, self.testBuiltin, self.testScriptNoShell, self.testScriptShell, self.testPythonExternal,
                 self.testPythonImport]
        for test in tests:
            testname = test.__name__
            try:
                test()
            except AssertionError as e:
                log(msg=_('Error: %s') % e.message)
            except Exception as e:
                msg = _('Error testing %s\n') % testname
                e = sys.exc_info()[0]
                if hasattr(e, 'message'):
                    msg += str(e.message)
                else:
                    msg += str(e)
                msg = msg + '\n' + traceback.format_exc()
                log(loglevel=xbmc.LOGERROR, msg=msg)
            else:
                log(msg=_('Test passed for task %s') % str(testname))
