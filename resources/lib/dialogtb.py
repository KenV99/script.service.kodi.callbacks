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

import textwrap

import xbmc
import xbmcaddon
import xbmcgui


class MessageDialog(xbmcgui.WindowXMLDialog):
    MESSAGE_TITLE = 1
    MESSAGE_TEXT = 5

    def __init__(self, *args, **kwargs):
        super(MessageDialog, self).__init__(*args, **kwargs)
        self.msg = ''
        self.title = ''

    def set_text(self, title, msg):
        self.msg = msg
        self.title = title

    def onInit(self):
        self.getControl(self.MESSAGE_TITLE).setLabel(self.title)
        # noinspection PyBroadException
        try:
            self.getControl(self.MESSAGE_TEXT).setText(self.msg)
        except Exception:
            pass


def show_textbox(title, msg):
    _addon_ = xbmcaddon.Addon('script.service.kodi.callbacks')
    _cwd_ = xbmc.translatePath(_addon_.getAddonInfo('path'))
    msgbox = MessageDialog(u"DialogTextViewer.xml", _cwd_, u"Default")
    xt = type(msg)
    if xt is str or xt is unicode:
        wmsg = u'\n'.join(textwrap.wrap(msg, 88))
    elif xt is list:
        tmsg = []
        for i in msg:
            omsg = textwrap.wrap(i, width=88, break_long_words=True)
            l1 = []
            for i1 in omsg:
                l1.append(u'i=%s, len=%s' % (i1, len(i1)))
            nmsg = u'\n'.join(omsg) + u'\n'
            tmsg.append(nmsg)
        wmsg = u''.join(tmsg)
    else:
        wmsg = u''
    msgbox.set_text(title, wmsg)
    msgbox.doModal()
    del msg
