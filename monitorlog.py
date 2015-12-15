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

import threading
from Queue import Queue
import json
import re

if not debug:
    import xbmc
    logfn = xbmc.translatePath(r'special://home\Kodi.log')
    def sleep(ms):
        xmbc.sleep(ms)
else:
    logfn = r"C:\Users\Ken User\AppData\Roaming\Kodi\kodi.log"
    import time
    def sleep(ms):
        time.sleep(ms/1000)

class LogMonitor(threading.Thread):
    def __init__(self, interval=100):
        super(LogMonitor, self).__init__()
        self.logfn = logfn
        self.__abort_evt = threading.Event()
        self.__abort_evt.clear()
        self.ouputq = Queue()
        self.interval = interval

    def run(self):
        f = open(self.logfn, 'r')
        f.seek(0, 2)           # Seek @ EOF
        fsize_old = f.tell()
        while not self.__abort_evt.is_set():
            f.seek(0, 2)           # Seek @ EOF
            fsize = f.tell()        # Get Size
            if fsize > fsize_old:
                f.seek(fsize_old, 0)
                lines = f.readlines()       # Read to end
                for line in lines:
                    self.ouputq.put(line, False)
                fsize_old = f.tell()
            sleep(self.interval)

    def abort(self):
        self.__abort_evt.set()

class LogChecker(threading.Thread):
    def __init__(self, interval_checker=100, interval_monitor=100):
        super(LogChecker, self).__init__()
        self._checks_simple = []
        self._checks_regex = []
        self.__abort_evt = threading.Event()
        self.__abort_evt.clear()
        self.interval_checker = interval_checker
        self.interval_monitor = interval_monitor

    def add_simple_check(self, match, nomatch, callback, param):
        self._checks_simple.append(LogCheckSimple(match, nomatch, callback, param))

    def add_re_check(self, match, nomatch, callback, param):
        self._checks_regex.append(LogCheckRegex(match, nomatch, callback, param))

    def run(self):
        lm = LogMonitor(interval=self.interval_monitor)
        lm.start()
        for chk in self._checks_simple:
            chk.start()
        for chk in self._checks_regex:
            chk.start()
        while not self.__abort_evt.is_set():
            while not lm.ouputq.empty():
                line = lm.ouputq.get_nowait()
                for chk in self._checks_simple:
                    chk.queue.put(line, False)
                for chk in self._checks_regex:
                    chk.queue.put(line, False)
                sleep(self.interval_checker)
        for chk in self._checks_simple:
            chk.abort()
        for chk in self._checks_regex:
            chk.abort()
        lm.abort()

    def abort(self):
        self.__abort_evt.set()

class LogCheck(object):
    def __init__(self, match, nomatch, callback, param):
        self.match = match
        self.nomatch = nomatch
        self.callback = callback
        self.param = param

class LogCheckSimple(threading.Thread):
    def __init__(self, match, nomatch, callback, param):
        super(LogCheckSimple, self).__init__()
        self.match = match
        self.nomatch = nomatch
        self.callback = callback
        self.param = param
        self.queue = Queue()
        self._abort_evt = threading.Event()
        self._abort_evt.clear()

    def run(self):
        while not self._abort_evt.is_set():
            while not self.queue.empty():
                line = self.queue.get_nowait()
                if self.match in line:
                    if self.nomatch != '':
                        if (self.nomatch in line) is not True:
                            self.callback([line, self.param])
                    else:
                        self.callback([line, self.param])

    def abort(self):
        self._abort_evt.set()

class LogCheckRegex(threading.Thread):
    def __init__(self, match, nomatch, callback, param):
        super(LogCheckRegex, self).__init__()
        try:
            re_match = re.compile(match)
        except Exception as e:
            raise
        if nomatch != '':
            try:
                re_nomatch = re.compile(nomatch)
            except Exception as e:
                raise
        else:
            re_nomatch = None
        self.match = re_match
        self.nomatch = re_nomatch
        self.callback = callback
        self.param = param
        self.queue = Queue()
        self._abort_evt = threading.Event()
        self._abort_evt.clear()

    def run(self):
        while not self._abort_evt.is_set():
            while not self.queue.empty():
                line = self.queue.get_nowait()
                if self.match.search(line):
                    if self.nomatch is not None:
                        if (self.nomatch.search(line)) is None:
                            self.callback(self.param)
                    else:
                        self.callback(self.param)

    def abort(self):
        self._abort_evt.set()


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

def printme(params):
    print params[0]

# if __name__ == '__main__':
#     lc = LogChecker()
#     lc.add_simple_check('AmbiBox', '', printme, 'AmbiBox!')
#     lc.start()
#     cnt = 0
#     while cnt < 60:
#         sleep(1000)
#         cnt = cnt + 1
#     try:
#         lc.abort()
#     except Exception as e:
#         pass