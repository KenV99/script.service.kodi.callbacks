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
LOGLEVEL_CRITICAL = 50
LOGLEVEL_ERROR = 40
LOGLEVEL_WARNING = 30
LOGLEVEL_INFO = 20
LOGLEVEL_DEBUG = 10

import os
import threading
import Queue
import subprocess
import sys
import abc
import re
import requests as requests
import urllib2
import httplib
from urlparse import urlparse
import socket
import traceback
import stat
import xbmc
import xbmcvfs
sysplat = sys.platform
from resources.lib.events import Events
from resources.lib.kodilogging import KodiLogger
from resources.lib.PubSub_Threaded import TaskReturn

events = Events()

# def dictToString(mydict):
#     string = []
#     for key in mydict.keys():
#         if ' ' in mydict[key]:
#             d = '"%s"' % mydict[key]
#         else:
#             d = mydict[key]
#         string.append('%s:%s' % (key, d))
#     return ", ".join(string)
#
# def dictToList(mydict):
#     lst = []
#     for key in mydict.keys():
#         lst.append('%s:%s' % (key, mydict[key]))
#     return lst
#
# def invertDict(mydict):
#     return dict([[v,k] for k,v in mydict.items()])

class AbstractWorker(threading.Thread):
    """
    Abstract class for command specific workers to follow
    """
    __metaclass__ = abc.ABCMeta
    event_id = ''

    def __init__(self, logger=KodiLogger.log):
        super(AbstractWorker, self).__init__()
        self.cmd_str = ''
        self.userargs = ''
        self.log = logger
        self.runtimeargs = []
        self.taskKwargs = {}
        self.topic = None
        self.type = ''
        self.taskId = ''
        self.returnQ = Queue.Queue()
        self.delimitregex = re.compile(r'\s+,\s+|,\s+|\s+')

    # def processUserargs(self, kwargs):
    #     if self.userargs == '':
    #         return []
    #     try:
    #         needs_shell = self.taskKwargs['needs_shell']
    #     except:
    #         needs_shell = False
    #     ret = self.userargs
    #     ret = ret.replace(r'%%', '{@literal%@}')
    #     if (self.type == 'script' and needs_shell is False) or self.type == 'python' or self.type == 'builtin':
    #         tmp = self.delimitregex.sub(r'{@originaldelim@}', ret)
    #         ret = tmp
    #     try:
    #         varArgs = events.Player[self.topic.topic]['varArgs']
    #     except:
    #         pass
    #     else:
    #         for key in varArgs.keys():
    #             try:
    #                 kw = kwargs[varArgs[key]]
    #                 kw = kw.replace(" ", '%__')
    #                 ret = ret.replace(key, kw)
    #             except:
    #                 pass
    #     ret = ret.replace('@#$^&', r'%')
    #     if self.type == 'script' and needs_shell is False:
    #         ret = ret.replace('%__', " ")
    #         ret = ret.replace('{@literal%@}', '%')
    #         ret = ret.split('{@originaldelim@}')
    #     elif self.type == 'python' or self.type == 'builtin':
    #         ret = ret.replace('%__', " ")
    #         ret = ret.replace('{@literal%@}', '%')
    #         ret = ' %s' % ret.replace('{@originaldelim@}', ',')
    #     elif self.type == 'http':
    #         ret = ret.replace('%__', " ")
    #         ret = ret.replace('{@literal%@}', '%')
    #     return ret

    def processUserargs(self, kwargs):
        if self.userargs == '':
            return []
        ret = self.userargs
        ret = ret.replace(r'%%', '{@literal%@}')
        tmp = self.delimitregex.sub(r'{@originaldelim@}', ret)
        ret = tmp
        try:
            varArgs = events.Player[self.topic.topic]['varArgs']
        except:
            pass
        else:
            for key in varArgs.keys():
                try:
                    kw = kwargs[varArgs[key]]
                    kw = kw.replace(" ", '%__')
                    ret = ret.replace(key, kw)
                except:
                    pass
        ret = ret.replace('%__', " ")
        ret = ret.replace('{@literal%@}', r'%')
        ret = ret.split('{@originaldelim@}')
        return ret

    @staticmethod
    @abc.abstractmethod
    def check(cmd_str, userargs, xlog=KodiLogger.log):
        pass

    def t_start(self, topic, taskKwargs, **kwargs):
        self.topic = topic
        self.taskKwargs = taskKwargs
        self.cmd_str = taskKwargs['cmd_str']
        self.userargs = taskKwargs['userargs']
        self.taskId = taskKwargs['taskid']
        self.runtimeargs = self.processUserargs(kwargs)
        self.start()

    @abc.abstractmethod
    def run(self):
        err = None  # True if error occured
        msg = ''    # string containing error message or return message
        self.threadReturn(err, msg)

    def threadReturn(self, err, msg):
        taskReturn = TaskReturn(err, msg)
        taskReturn.eventId = str(self.topic)
        taskReturn.taskId = self.taskId
        self.returnQ.put(taskReturn)

class WorkerScript(AbstractWorker):

    def __init__(self):
        super(WorkerScript, self).__init__()
        self.type = 'script'

    @staticmethod
    def check(cmd_str, userargs, xlog=KodiLogger.log):

        tmp = cmd_str
        tmp = xbmc.translatePath(tmp).decode('utf-8')
        if xbmcvfs.exists(tmp):
            try:
                mode = os.stat(tmp).st_mode
                mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                os.chmod(tmp, mode)
            except:
                xlog(msg='Failed to set execute bit on script: %s' % tmp)
            return True
        else:
            xlog(msg='Error - File not found: %s' % tmp)
            return False

    def run(self):
        try:
            needs_shell = self.taskKwargs['needs_shell']
        except:
            needs_shell = False
        args = self.runtimeargs
        args.insert(0, self.cmd_str)
        if needs_shell:
            args = ' '.join(args)
        err = False
        debg = False
        msg = ''
        if sysplat.startswith('darwin') or debg:
            try:
                p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=needs_shell, stderr=subprocess.STDOUT)
                stdoutdata, stderrdata = p.communicate()
                if stdoutdata is not None:
                    msg = 'Process returned data: %s' % str(stdoutdata)
                if stderrdata is not None:
                    msg += 'Process returned error: %s' % str(stdoutdata)
            except subprocess.CalledProcessError, e:
                err = True
                msg = e.output
            except:
                e = sys.exc_info()[0]
                err = True
                if hasattr(e, 'message'):
                    msg = str(e.message)
                msg = msg + '\n' + traceback.format_exc()
            self.threadReturn(err, msg)
        else:
            try:
                result = subprocess.check_output(args, shell=needs_shell, stderr=subprocess.STDOUT)
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
            self.threadReturn(err, msg)


class WorkerPy(AbstractWorker):
    def __init__(self):
        super(WorkerPy, self).__init__()
        self.type = 'python'

    @staticmethod
    def check(cmd_str, userargs, xlog=KodiLogger.log):
        tmp = xbmc.translatePath(cmd_str).decode('utf-8')
        if xbmcvfs.exists(tmp):
            fn, ext = os.path.splitext(tmp)
            if ext == '.py':
                return True
            else:
                xlog(msg='Error - not a python script: %s' % tmp)
                return False
        else:
            xlog(msg='Error - File not found: %s' % tmp)
            return False

    def run(self):
        err = False
        msg = ''
        args = self.runtimeargs
        try:
            run_type = self.taskKwargs['run_type']
        except:
            run_type = 'builtin'
        result = None
        #TODO: implement options
        try:
            if len(self.runtimeargs) > 0:
                if run_type == 'builtin':
                    args = ' %s' % ' '.join(args)
                    result = xbmc.executebuiltin('XBMC.RunScript(%s, %s)' % (self.cmd_str, args))
                elif run_type == 'execfile':
                    sys.argv = args
                    result = execfile(self.cmd_str)
                elif run_type == 'import':
                    import os
                    directory, module_name = os.path.split(self.cmd_str)
                    module_name = os.path.splitext(module_name)[0]

                    path = list(sys.path)
                    sys.path.insert(0, directory)
                    try:
                        module = __import__(module_name)
                        result = module.run(args)
                    finally:
                        sys.path[:] = path
            else:
                if run_type == 'builtin':
                    result = xbmc.executebuiltin('XBMC.RunScript(%s)' % self.cmd_str)
                elif run_type == 'execfile':
                    result = execfile(self.cmd_str)
                elif run_type == 'import':
                    import os
                    directory, module_name = os.path.split(self.cmd_str)
                    module_name = os.path.splitext(module_name)[0]

                    path = list(sys.path)
                    sys.path.insert(0, directory)
                    try:
                        module = __import__(module_name)
                        result = module.run(args)
                    finally:
                        sys.path[:] = path
            if result is not None:
                msg = result
                if result != '':
                    err = True
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()

        self.threadReturn(err, msg)


class WorkerBuiltin(AbstractWorker):
    def __init__(self):
        super(WorkerBuiltin, self).__init__()
        self.type = 'builtin'

    @staticmethod
    def check(cmd_str, userargs, xlog=KodiLogger.log):
        pass

    def run(self):
        err = False
        msg = ''
        args = ' %s' % ' '.join(self.runtimeargs)
        try:
            if len(self.runtimeargs) > 0:
                result = xbmc.executebuiltin('XBMC.RunScript(%s, %s)' % (self.cmd_str, args))
            else:
                result = xbmc.executebuiltin('XBMC.RunScript(%s)' % self.cmd_str)
            if result is not None:
                msg = result
                if result != '':
                    err = True
        except:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        self.threadReturn(err, msg)


class WorkerHTTP(AbstractWorker):
    def __init__(self):
        super(WorkerHTTP, self).__init__()
        self.type = 'http'
        self.runtimeargs = ''

    @staticmethod
    def check(cmd_str, userargs=None, xlog=KodiLogger.log):
        o = urlparse(cmd_str+userargs)
        if o.scheme != '' and o.netloc != '' and o.path != '':
            return True
        else:
            xlog(msg='Invalid url: %s' % cmd_str)
            return False

    def processUserargs(self, kwargs):
        if self.userargs == '':
            return []
        ret = self.userargs
        ret = ret.replace(r'%%', '{@literal%@}')
        try:
            varArgs = events.Player[self.topic.topic]['varArgs']
        except:
            pass
        else:
            for key in varArgs.keys():
                try:
                    kw = kwargs[varArgs[key]]
                    kw = kw.replace(" ", '%__')
                    ret = ret.replace(key, kw)
                except:
                    pass
        ret = ret.replace('%__', " ")
        ret = ret.replace('{@literal%@}', r'%')
        return ret

    def run(self):
        err = False
        msg = ''
        try:
            u = requests.get(self.cmd_str+self.runtimeargs, timeout=20)
            try:
                result = u.text
            except Exception as e:
                err = True
                result = ''
                msg = 'Error on url read'
                if hasattr(e, 'message'):
                    msg = msg + '\n' + (str(e.message))
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
            self.log(msg='Http Bad Status Line caught and passed')
            # pass - returned a status code that is not understood in the library
            # if u is not None:
            #     try:
            #         result = u.read()
            #         self.log(msg='Successful read after catching BadStatusLine')
            #     except Exception as e:
            #         err = True
            #         result = ''
            #         msg = 'Error on url read'
            #         if hasattr(e, 'message'):
            #             msg = msg + '\n' + (str(e.message))
            #     del u

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
        else:
            msg = str(result)
        self.threadReturn(err, msg)

