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
import sys

import xbmcaddon
from resources.lib.pubsub import Publisher, Message, Topic
from resources.lib.events import Events

libs = os.path.join(xbmcaddon.Addon('service.watchdog').getAddonInfo('path'), 'lib', 'watchdog')
sys.path.append(libs)
libs = os.path.join(xbmcaddon.Addon('service.watchdog').getAddonInfo('path'), 'lib')
sys.path.append(libs)
try:
    from observers import Observer
    from events import PatternMatchingEventHandler
except Exception as e:
    pass

class EventHandler(PatternMatchingEventHandler):
    def __init__(self, patterns, ignore_patterns, ignore_directories, topic, publish):
        super(EventHandler, self).__init__(patterns=patterns, ignore_patterns=ignore_patterns, ignore_directories=ignore_directories)
        self.topic = topic
        self.publish = publish

    def on_any_event(self, event):
        msg = Message(self.topic, path=event._src_path, event=event.event_type)
        self.publish(msg)

class WatchdogPublisher(Publisher):
    publishes = Events().Watchdog.keys()

    def __init__(self, dispatcher, watchdogSettings):
        super(WatchdogPublisher, self).__init__(dispatcher)
        self.watchdogSettings = watchdogSettings
        self.event_handlers = []
        self.observers = []
        self.initialize()

    def initialize(self):
        for setting in self.watchdogSettings:
            try:
                eh = EventHandler(patterns=setting['patterns'], ignore_patterns=setting['ignore_patterns'],
                                ignore_directories=setting['ignore_directories'],
                                topic=Topic('onFileSystemChange', setting['key']), publish=self.publish)
                self.event_handlers.append(eh)
                observer = Observer()
                observer.schedule(eh, setting['folder'], recursive=setting['recursive'])
                self.observers.append(observer)
            except Exception as e:
                pass

    def start(self):
        for item in self.observers:
            assert isinstance(item, Observer)
            item.start()

    def abort(self, timeout=0):
        for item in self.observers:
            assert isinstance(item, Observer)
            item.stop()
        for item in self.observers:
            item.join(timeout)