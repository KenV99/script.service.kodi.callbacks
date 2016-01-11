#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 KenV99
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

import sys
import os
import traceback
import xbmc
import xbmcvfs
from resources.lib.taskABC import AbstractTask, KodiLogger, notify


class TaskPython(AbstractTask):
    tasktype = 'python'
    variables = [
        {
            'id':'pythonfile',
            'settings':{
                'default':'',
                'label':'Python file',
                'type':'file'
            }
        },
        {
            'id':'import',
            'settings':{
                'default':'false',
                'label':'Import and call run() (default=no)?',
                'type':'bool'
            }
        }
    ]

    def __init__(self):
        super(TaskPython, self).__init__()

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):
        tmp = xbmc.translatePath(taskKwargs['pythonfile']).decode('utf-8')
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
        if self.taskKwargs['notify'] is True:
            notify('Task %s launching for event: %s' % (self.taskId, str(self.topic)))
        err = False
        msg = ''
        args = self.runtimeargs
        try:
            useImport = self.taskKwargs['import']
        except:
            useImport = False
        result = None
        #TODO: implement options
        try:
            if len(self.runtimeargs) > 0:
                if useImport is False:
                    args = ' %s' % ' '.join(args)
                    result = xbmc.executebuiltin('XBMC.RunScript(%s, %s)' % (self.taskKwargs['pythonfile'], args))
                else:
                    import os
                    directory, module_name = os.path.split(self.taskKwargs['pythonfile'])
                    module_name = os.path.splitext(module_name)[0]

                    path = list(sys.path)
                    sys.path.insert(0, directory)
                    try:
                        module = __import__(module_name)
                        result = module.run(args)
                    finally:
                        sys.path[:] = path
            else:
                if useImport is False:
                    result = xbmc.executebuiltin('XBMC.RunScript(%s)' % self.taskKwargs['pythonfile'])
                else:
                    import os
                    directory, module_name = os.path.split(self.taskKwargs['pythonfile'])
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