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
import stat
import subprocess
import traceback
from resources.lib.taskABC import AbstractTask, notify, KodiLogger
import xbmc
import xbmcvfs

sysplat = sys.platform

class TaskScript(AbstractTask):
    tasktype = 'script'
    variables = [
        {
            'id':'scriptfile',
            'settings':{
                'default':'',
                'label':'Script executable file',
                'type':'file'
            }
        },
        {
            'id':'use_shell',
            'settings':{
                'default':'false',
                'label':'Requires shell?',
                'type':'bool'
            }
        }
    ]


    def __init__(self):
        super(TaskScript, self).__init__()

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):

        tmp = taskKwargs['scriptfile']
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
        if self.taskKwargs['notify'] is True:
            notify('Task %s launching for event: %s' % (self.taskId, str(self.topic)))
        try:
            needs_shell = self.taskKwargs['use_shell']
        except:
            needs_shell = False
        args = self.runtimeargs
        args.insert(0, self.taskKwargs['scriptfile'])
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