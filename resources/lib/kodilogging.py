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
import xbmc

def log(loglevel=xbmc.LOGNOTICE, msg=''):
    if isinstance(msg, str):
        msg = msg.decode("utf-8")
    message = u"$$$ [%s] - %s" % ('kodi.callbacks', msg)
    xbmc.log(msg=message.encode("utf-8"), level=loglevel)

class KodiLogger(object):

    selfloglevel = xbmc.LOGNOTICE

    @staticmethod
    def setLogLevel(arg):
        KodiLogger.selfloglevel = arg

    @staticmethod
    def log(loglevel=xbmc.LOGNOTICE, msg=''):
        if isinstance(msg, str):
            msg = msg.decode("utf-8")
        message = u"$$$ [%s] - %s" % ('kodi.callbacks', msg)
        xbmc.log(msg=message.encode("utf-8"), level=loglevel)