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
from resources.lib.publishers.log import LogPublisher
from resources.lib.publishers.loop import LoopPublisher
from resources.lib.publishers.monitor import MonitorPublisher
from resources.lib.publishers.player import PlayerPublisher
from resources.lib.publishers.watchdog import WatchdogPublisher
from resources.lib.pubsub import Dispatcher

from resources.lib.tests.stubs import *
from flexmock import flexmock

def printlog(msg, loglevel=0):
    print msg

flexmock(xbmc, log=printlog)

