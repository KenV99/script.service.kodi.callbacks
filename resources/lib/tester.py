# -*- coding: utf-8 -*-
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file LICENSE.txt.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *

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

sys.path.append(__cwd__)
sys.path.append(__resource__)
from default import Dispatcher, read_settings, __options__, __testerruntimeargs__
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
    output = ['Testing for event: %s\n' % __testpoint__, 'Command type: %s\n' % worker.type,
              'Command: %s\n' % worker.cmd_str]
    if len(rtargs) > 0:
        if type(rtargs) is str:
            output.append('User args: %s' % rtargs)
        else:
            for i in rtargs:
                output.append('Runtime arg: %s' % i)
    else:
        output.append('Runtime args: None')
    if len(worker.userargs) > 0:
        if type(worker.userargs) is str:
            output.append('User args: %s' % worker.userargs)
        else:
            for i in worker.userargs:
                output.append('User arg: %s' % i)
    else:
        output.append('User args: None')
    if result[0]:  # Error encountered
        output.append('Error Encountered')
        if len(result[1]) > 0:
            output.append('Error message: %s' % result[1])
        else:
            output.append('No further error info available')
    else:
        output.append('Command completed without error detection')
        if len(result[1]) > 0:
            output.append('Command output: %s' % result[1])
        else:
            output.append('Command did not produce output')
    return output


def simulateruntimeargs(worker):

    rtargs = []
    if __options__['arg_eventid']:
        rtargs.append('event=' + worker.event_id)
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
        show_textbox('Results', output)
    else:
        __testerruntimeargs__ = []
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(32049), __language__(32050))
except Exception, e:
    pass



