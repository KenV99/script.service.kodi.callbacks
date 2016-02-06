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
import shlex
import subprocess
import traceback
from resources.lib.taskABC import AbstractTask, notify, KodiLogger
import xbmc
import xbmcvfs
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString
__ = kodipo.getLocalizedStringId

sysplat = sys.platform

class TaskScript(AbstractTask):
    tasktype = 'script'
    variables = [
        {
            'id':'scriptfile',
            'settings':{
                'default':'',
                'label':__('Script executable file'),
                'type':'sfile'
            }
        },
        {
            'id':'use_shell',
            'settings':{
                'default':'false',
                'label':__('Requires shell?'),
                'type':'bool'
            }
        },
        {
            'id':'waitForCompletion',
            'settings':{
                'default':'true',
                'label':__('Wait for script to complete?'),
                'type':'bool'
            }
        }
    ]


    def __init__(self):
        super(TaskScript, self).__init__()

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):

        tmpl = shlex.split(taskKwargs['scriptfile'])
        for tmp in tmpl:
            tmp = xbmc.translatePath(tmp).decode('utf-8')
            if xbmcvfs.exists(tmp) or os.path.exists(tmp):
                try:
                    mode = os.stat(tmp).st_mode
                    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                    os.chmod(tmp, mode)
                except OSError:
                    if sysplat.startswith('win') is False:
                        xlog(msg=_('Failed to set execute bit on script: %s') % tmp)
        return True

    def run(self):
        if self.taskKwargs['notify'] is True:
            notify(_('Task %s launching for event: %s') % (self.taskId, str(self.topic)))
        try:
            needs_shell = self.taskKwargs['use_shell']
        except KeyError:
            needs_shell = False
        try:
            wait = self.taskKwargs['waitForCompletion']
        except KeyError:
            wait = True
        # TODO: Fix this part
        tmpl = shlex.split(self.taskKwargs['scriptfile'])
        filefound = False
        basedir = None
        for i, tmp in enumerate(tmpl):
            tmp = xbmc.translatePath(tmp).decode('utf-8')
            tmp = os.path.expanduser(tmp)
            tmp = os.path.expandvars(tmp)
            if os.path.exists(tmp) and filefound is False:
                basedir, fn = os.path.split(tmp)
                tmpl[i] = fn
                filefound = True
            else:
                tmpl[i] = tmp

        cwd = os.getcwd()
        args =tmpl + self.runtimeargs
        if needs_shell:
            args = ' '.join(args)
        err = False
        msg = ''
        sys.exc_clear()
        try:
            if basedir is not None:
                os.chdir(basedir)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, shell=needs_shell, stderr=subprocess.STDOUT)
            if wait:
                stdoutdata, stderrdata = p.communicate()
                if stdoutdata is not None:
                    stdoutdata = str(stdoutdata).strip()
                    if stdoutdata != '':
                        msg = _('Process returned data: %s\n') % stdoutdata
                    else:
                        msg = _('Process returned no data\n')
                else:
                    msg = _('Process returned no data\n')
                if stderrdata is not None:
                    stderrdata = str(stderrdata).strip()
                    if stderrdata != '':
                        msg += _('Process returned error: %s') % stdoutdata
        except subprocess.CalledProcessError, e:
            err = True
            msg = e.output
        except Exception:
            e = sys.exc_info()[0]
            err = True
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        finally:
            os.chdir(cwd)
        self.threadReturn(err, msg)

