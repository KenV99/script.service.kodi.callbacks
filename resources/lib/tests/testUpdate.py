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
import os
from resources.lib.utils.updateaddon import UpdateAddon
from resources.lib.utils.kodipathtools import translatepath
from nose.plugins.skip import SkipTest

def testBackup():
    ua = UpdateAddon('Kenv99', 'script.service.kodi.callbacks', 'master', silent=True)
    assert isinstance(ua, UpdateAddon)
    ua.createTimeStampJson(translatepath('special://addon'), dst=None, ignore=['.git/*', '.idea/*', '*.pyc', '*.pyo'])
    # result = ua.backup(translatepath('special://addon'), translatepath('special://addondata/backup'))
    # os.remove(os.path.join(translatepath('special://addon'), 'timestamp.json'))
    # assert result is True

@SkipTest
def testGHA_Detect():
     assert UpdateAddon.isGitHubArchive(translatepath('special://addon')) is False
     assert UpdateAddon.isGitHubArchive(r'C:\Temp\script.service.kodi.callbacks-master') is True

