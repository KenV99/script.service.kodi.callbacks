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

import threading
import time

import PubSub_Threaded


class MockPublisher(PubSub_Threaded.Publisher, threading.Thread):
    def __init__(self, dispatcher, topic, interval=1):
        PubSub_Threaded.Publisher.__init__(self, dispatcher)
        threading.Thread.__init__(self)
        self.interval = interval
        self.abort_evt = threading.Event()
        self.topic = topic

    def run(self):
        count = 1
        while not self.abort_evt.is_set():
            time.sleep(self.interval)
            msg = PubSub_Threaded.Message(self.topic, count=count)
            self.publish(msg)
            count += 1


class PrintTask(PubSub_Threaded.Task):
    def run(self):
        print 'Message Received %s: %s' % (self.topic.topic, str(self.kwargs))


if __name__ == '__main__':
    dispatch = PubSub_Threaded.Dispatcher()
    topics = [['test_topic1', 1], ['test_topic2', 2], ['test_topic3', 3]]
    subs = []
    pubs = []
    for t in topics:
        try:
            task = PrintTask  # NOTE: Not an instance
            tm = PubSub_Threaded.TaskManager(task, max_runs=3)
            subscriber = PubSub_Threaded.Subscriber()
            subscriber.addTaskManager(tm)
            subscriber.addTopic(PubSub_Threaded.Topic(t[0]))
            dispatch.addSubscriber(subscriber)
            subs.append(subscriber)
            pub = MockPublisher(dispatch, PubSub_Threaded.Topic(t[0]), interval=t[1])
            pubs.append(pub)
        except Exception as e:
            pass
    dispatch.start()
    for pub in pubs:
        pub.start()
    while True:
        pass

