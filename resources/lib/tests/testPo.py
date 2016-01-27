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
from resources.lib.tests.stubs import *
from flexmock import flexmock
import resources.lib.utils.poutil as poutil
from resources.lib.utils.poutil import KodiPo


class mockaddon(object):
    def __init__(self, *args):
        # flexmock(poutil.xbmcaddon, Addon=self)
        self.podict = poutil.PoDict()
        self.podict.read_from_file(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\language\English\strings.po')

    def getAddonInfo(self, y):
        return r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks'

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

    def testGetMsgxtxt(self):
        x = _('Tasks')
        assert x == 'Tasks'

def testPoFileUpdate():
    up =  poutil.UpdatePo(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks',
                   r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\language\English\strings.po',
                   [r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\watchdog',
                    r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\lib\tests\stubs'])
    assert isinstance(up, poutil.UpdatePo)
    for i in xrange(1, 11):
        t = 'Task %s' % str(i)
        found, strid = up.podict.has_msgid(t)
        if found is False:
            up.podict.addentry(strid, t)
    for i in xrange(1, 11):
        t = 'Event %s' % str(i)
        found, strid = up.podict.has_msgid(t)
        if found is False:
            up.podict.addentry(strid, t)
    up.updateStringsPo()



