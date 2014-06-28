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
        sys.path.append(r'C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\script.ambibox\\resources\\lib\\pycharm-debug.py3k\\')
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
from default import Dispatcher, read_settings, __options__

__options__['tester'] = True
__testpoint__ = sys.argv[1]
try:
    dispatcher = Dispatcher()
    read_settings(dispatcher.ddict)
    if __testpoint__ in dispatcher.ddict:
        result = dispatcher.dispatch(__testpoint__, [])
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(32049), __language__(32050))
except Exception, e:
    pass
