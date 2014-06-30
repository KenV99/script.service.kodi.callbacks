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

debug = False
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
from default import Dispatcher, read_settings, __options__
from dialogtb import show_textbox

__options__['tester'] = True
__testpoint__ = sys.argv[1]


def format_results(result, ddict):
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


try:
    dispatcher = Dispatcher()
    read_settings(dispatcher.ddict)
    if __testpoint__ in dispatcher.ddict:
        result = dispatcher.dispatch(__testpoint__, [])
        output = format_results(result, dispatcher.ddict)
        show_textbox('Results', output)
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(32049), __language__(32050))
except Exception, e:
    pass



