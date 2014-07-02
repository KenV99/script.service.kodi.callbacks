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

######################################################################
#
#  Runs as a script from the settings page to test scripts
#
######################################################################
"""
debug = True
remote = False
if debug:
    if remote:
        sys.path.append(r'C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\script.ambibox\\resources\\lib\\'
                        r'pycharm-debug.py3k\\')
        import pydevd
        pydevd.settrace('192.168.1.103', port=51234, stdoutToServer=True, stderrToServer=True)
    else:
        sys.path.append('C:\Program Files (x86)\JetBrains\PyCharm 3.1.3\pycharm-debug-py3k.egg')
        import pydevd
        pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True)
"""

import sys
import os
import xbmc
import xbmcgui
import xbmcaddon

__addon__ = xbmcaddon.Addon('script.xbmc.callbacks2')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8')
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')).decode('utf-8')
__language__ = __addon__.getLocalizedString
xbmc.log('$$$ xbmc.callbacks2 - Starting tester.py from cwd: %s' % __cwd__)

from default import Dispatcher, read_settings, __options__
from dialogtb import show_textbox

__options__['tester'] = True
__testpoint__ = sys.argv[1]


def format_results(result, ddict, rtargs):
    """
    @param result: Return from dispatcher
    @type result: list
    @param ddict: dispatcher.ddict
    @type ddict: Dispatcher.ddict
    @return: Results as string
    @rtype: list
    """
    worker = ddict[__testpoint__]
    output = [__language__(32054) % __testpoint__, __language__(32055) % worker.type,  # [Testing for event: %s\n] [Command type: %s\n] 
              __language__(32056) % worker.cmd_str]  # [Command: %s\n] 
    # output = ['Testing for event: %s\n' % __testpoint__, 'Command type: %s\n' % worker.type,
    #           'Command: %s\n' % worker.cmd_str]
    if len(rtargs) > 0:
        xt = type(rtargs)
        if xt is str or xt is unicode:
            output.append(__language__(32057) % rtargs)  # [Runtime args: %s] 
        else:
            for i in rtargs:
                output.append(__language__(32058) % i)  # [Runtime arg: %s] 
    else:
        output.append(__language__(32059))  # [Runtime args: None] 
    if len(worker.userargs) > 0:
        xt = type(worker.userargs)
        if xt is str or xt is unicode:
            output.append(__language__(32060) % worker.userargs)  # [User args: %s] 
        else:
            for i in worker.userargs:
                output.append(__language__(32061) % i) # [User arg: %s] 
    else:
        output.append(__language__(32062))  # [User args: None] 
    if result[0]:
        output.append(__language__(32063))  # [Error Encountered] 
        if len(result[1]) > 0:
            output.append(__language__(32064) % result[1])  # [Error message: %s] 
        else:
            output.append(__language__(32065))  # [No further error info available] 

    else:
        output.append(__language__(32066))  # [Command completed without error detection] 
        if len(result[1]) > 0:
            output.append(__language__(32067) % result[1])  # [Command output: %s] 
        else:
            output.append(__language__(32068))  # [Command did not produce output] 
    return output


def simulateruntimeargs(worker):

    rtargs = []
    if worker.type == 'script' or worker.type == 'python':
        if worker.event_id == 'onPlaybackStarted':
            if __options__['arg_mediatype']:
                rtargs.append('media=unknown')
            if __options__['arg_filename']:
                rtargs.append('file=\\path\\file name.ext')
            if __options__['arg_title']:
                rtargs.append('title=Star Wars Episode IV: A New Hope')
            if __options__['arg_aspectratio']:
                rtargs.append('aspectratio=2.40')
            if __options__['arg_resolution']:
                rtargs.append('resolution=1080')
        elif worker.event_id == 'onStereoModeChange':
            if __options__['arg_stereomode']:
                rtargs.append('stereomode=monoscopic')
        elif worker.event_id == 'onProfileChange':
            if __options__['arg_profilepath']:
                rtargs.append('profilepath=\\xbmc\\userdate\\profiles\\asmallchild\\')
    return rtargs

try:
    dispatcher = Dispatcher()
    read_settings(dispatcher.ddict)
    if __testpoint__ in dispatcher.ddict:
        rtargs = simulateruntimeargs(dispatcher.ddict[__testpoint__])
        result = dispatcher.dispatch(__testpoint__, rtargs)
        output = format_results(result, dispatcher.ddict, rtargs)
        show_textbox(__language__(32069), output)  # [Results]
    else:
        # TODO: Needs more feedback about why failed
        __testerruntimeargs__ = []
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(32049), __language__(32050))
except Exception, e:
    pass



