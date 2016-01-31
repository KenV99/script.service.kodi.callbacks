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

from resources.lib.publishers.log import LogPublisher
from resources.lib.publishers.loop import LoopPublisher
from resources.lib.publishers.monitor import MonitorPublisher
from resources.lib.publishers.player import PlayerPublisher
try:
    from resources.lib.publishers.watchdog import WatchdogPublisher
except ImportError:
    from resources.lib.publishers.dummy import WatchdogPublisherDummy as WatchdogPublisher
from resources.lib.kodilogging import KodiLogger
from resources.lib.utils.poutil import KodiPo

kl = KodiLogger()
log = kl.log
kodipo = KodiPo()
_ = kodipo.getLocalizedString

class PublisherFactory(object):

    def __init__(self, settings, topics, dispatcher, logger, debug=False):
        self.settings = settings
        self.logger = logger
        self.topics = topics
        self.debug = debug
        self.dispatcher = dispatcher
        self.publishers = {LogPublisher:'Log Publisher initialized',
                           LoopPublisher:'Loop Publisher initialized',
                           MonitorPublisher:'Monitor Publisher initialized',
                           PlayerPublisher:'Player Publisher initialized',
                           WatchdogPublisher:'Watchdog Publisher initialized'
                           }
        self.ipublishers = []

    def createPublishers(self):
        for publisher in self.publishers.keys():
            if not set(self.topics).isdisjoint(publisher.publishes) or self.debug is True:
                ipublisher = publisher(self.dispatcher, self.settings)
                self.ipublishers.append(ipublisher)
                self.logger.log(msg=_(self.publishers[publisher]))


