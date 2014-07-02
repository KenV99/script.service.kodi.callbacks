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
"""
debug = False
remote = False
if debug:
    import sys
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

import xbmc
import xbmcgui
import xbmcaddon


class MessageDialog(xbmcgui.WindowXMLDialog):

    MESSAGE_ACTION_OK = 110
    MESSAGE_EXIT = 111
    MESSAGE_TITLE = 101
    MESSAGE_TEXT = 105

    def __init__(self, *args, **kwargs):
        self.msg = ''
        self.title = ''

    def set_text(self, title, msg):
        self.msg = msg
        self.title = title

    def onInit(self):
        self.getControl(self.MESSAGE_TITLE).setLabel(self.title)
        try:
            self.getControl(self.MESSAGE_TEXT).setText(self.msg)
        except Exception, e:
            pass

    def onAction(self, action):
        if action == 1010:
            self.close()

    def onClick(self, controlID):
        if controlID == self.MESSAGE_ACTION_OK or controlID == self.MESSAGE_EXIT:
            self.onAction(1010)

    def onFocus(self, controlID):
        pass


def show_textbox(title, msg):
    __addon__ = xbmcaddon.Addon('scripts.xbmc.callbacks2')
    __cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8')
    msgbox = MessageDialog("DialogTextBox.xml", __cwd__, "Default")
    msgbox.set_text(title, msg)
    msgbox.doModal()
    del msg

