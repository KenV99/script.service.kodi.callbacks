#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2016 KenV99
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
# from resources.lib.tests.stubs import *
# import xbmcaddon
from flexmock import flexmock
import resources.lib.utils.poutil as poutil
from resources.lib.utils.poutil import KodiPo


class mockaddon(object):
    def __init__(self, *args):
        # flexmock(poutil.xbmcaddon, Addon=self)
        self.podict = poutil.PoDict()
        self.podict.read_from_file(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\language\English\strings.po')

    @staticmethod
    def getAddonInfo(y):
        if y is not None:
            return r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks'

    def getLocalizedString(self, strid):
        assert isinstance(strid, int)
        found, ret = self.podict.has_msgctxt(str(strid))
        if found:
            return ret
        else:
            return 'String Not Found'

flexmock(poutil.xbmcaddon, Addon=mockaddon)
kodipo = KodiPo()
_ = kodipo.getLocalizedString

class testPo(object):
    def __init__(self):
        pass

    @staticmethod
    def testGetMsgxtxt():
        x = _('Tasks')
        assert x == 'Tasks'

def testPoFileUpdate():
    up =  poutil.UpdatePo(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks',
                   r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\language\English\strings.po',
                   [r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\lib\watchdog',
                    r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\lib\pathtools',
                    r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\lib\helpers',
                    r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\lib\tests\Kodi_stubs'])
    assert isinstance(up, poutil.UpdatePo)
    up.updateStringsPo()

def moclog(msg=None):
    print msg

# def testPoFailure():
#     flexmock(poutil.klogger, log=moclog)
#     test = _('Non existent string')
#     assert test == 'Non existent string'




