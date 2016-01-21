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
from resources.lib import taskdict
from resources.lib.pubsub import Topic, TaskManager
from resources.lib.events import Events
from resources.lib.kodilogging import log
import xbmc
events = Events().AllEvents




class testTasks(object):
    def __init__(self):
        self.task = None
        self.q = Queue.Queue()

    def setup(self):
        pass

    def teardown(self):
        pass

    def testHttp(self):
        self.task = taskdict['http']['class']
        taskKwargs = {'http':'http://localhost:9091/jsonrpc', 'user':'kpv', 'pass':'hippo', 'type':'http', 'notify':False}
        userargs = '?request={"jsonrpc": "2.0", "id": 1, "method":"Application.Setmute", "params":{"mute":"toggle"}}'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        assert tr.msg == '{"id":1,"jsonrpc":"2.0","result":false}'


    def returnHandler(self, taskReturn):
        self.q.put_nowait(taskReturn)


    def testBuiltin(self):
        self.task = taskdict['builtin']['class']
        taskKwargs = {'builtin':'ActivateWindow(10004)', 'type':'builtin', 'notify':False}
        userargs = ''
        tm = TaskManager(self.task,1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        topic = Topic('onPlayBackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        time.sleep(1)
        import xbmcgui
        cwid = xbmcgui.getCurrentWindowId()
        xbmc.executebuiltin('ActivateWindow(10000)')
        if cwid != 10004:
            raise AssertionError('Builtin test failed')


    def testScriptNoShell(self):
        self.task = taskdict['script']['class']
        outfile = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\scriptoutput.txt'
        try:
            os.remove(outfile)
        except:
            pass
        taskKwargs = {'scriptfile':r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\tstScript.bat',
                      'use_shell':False, 'type':'script', 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        assert tr.iserror is False
        try:
            with open(outfile, 'r') as f:
                retArgs = f.readline()
        except Exception as e:
            retArgs = ''
        try:
            os.remove(outfile)
        except:
            pass
        if retArgs.strip('\n') != userargs:
            raise AssertionError('Script without shell test failed')

    def testScriptShell(self):
        self.task = taskdict['script']['class']
        outfile = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\scriptoutput.txt'
        try:
            os.remove(outfile)
        except:
            pass
        taskKwargs = {'scriptfile':r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\tstScript.bat',
                      'use_shell':True, 'type':'script', 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        assert tr.iserror is False
        try:
            with open(outfile, 'r') as f:
                retArgs = f.readline()
        except Exception as e:
            retArgs = ''
        try:
            os.remove(outfile)
        except:
            pass
        if retArgs.strip('\n') != userargs:
            raise AssertionError('Script with shell test failed')


    def testPythonImport(self):
        self.task = taskdict['python']['class']
        taskKwargs = {'pythonfile':r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\tstPythonGlobal.py',
                      'import':True, 'type':'python', 'notify':False}
        userargs = 'abc def:ghi'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        assert tr.iserror is False
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
            raise AssertionError('Python import test failed')

    def testPythonExternal(self):
        self.task = taskdict['python']['class']
        taskKwargs = {'pythonfile':r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\tstPythonGlobal.py',
                      'import':True, 'type':'python', 'notify':False}
        userargs = 'jkl mno:pqr'
        tm = TaskManager(self.task, 1, None, -1, taskid='T1', userargs=userargs, **taskKwargs)
        tm.returnHandler = self.returnHandler
        topic = Topic('onPlaybackStarted')
        runKwargs = events['onPlayBackStarted']['expArgs']
        tm.start(topic, **runKwargs)
        tr = self.q.get(timeout=1)
        assert tr.iserror is False
        try:
            retArgs = sys.modules['__builtin__'].__dict__['testReturn']
        except KeyError:
            retArgs = sys.modules['builtins'].__dict__['testReturn']
        except:
            raise
        finally:
            try:
                sys.modules['__builtin__'].__dict__.pop('testReturn', None)
            except KeyError:
                sys.modules['builtins'].__dict__.pop('testReturn', None)
        if ' '.join(retArgs[0]) != userargs:
            raise AssertionError('Python external test failed')

    def runTests(self):
        tests = [self.testHttp, self.testBuiltin, self.testScriptNoShell, self.testScriptShell, self.testPythonExternal,
                 self.testPythonImport]
        for test in tests:
            self.setup()
            try:
                test()
            except AssertionError as e:
                log(msg='Error: %s' % e.message)
            except Exception as e:
                raise
            else:
                log(msg='Test passed for task %s' % str(test.__name__))
