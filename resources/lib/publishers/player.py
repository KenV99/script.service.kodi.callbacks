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
import xbmc
from resources.lib.PubSub_Threaded import Publisher, Topic, Message
from resources.lib.events import Events

class PlayerPublisher(Publisher, threading.Thread):
    publishes = Events.Player.keys()
    def __init__(self, dispatcher):
        Publisher.__init__(self, dispatcher)
        threading.Thread.__init__(self, name='PlayerPublisher')
        self.dispatcher = dispatcher
        self.publishes = Events.Player.keys()
        self._abortevt = threading.Event()
        self._abortevt.clear()

    def run(self):
        publish = super(PlayerPublisher, self).publish
        player = Player()
        player.publish = publish
        while not self._abortevt.is_set():
            if player.isPlaying():
                player.playingTime = player.getTime()
            xbmc.sleep(500)
        del player

    def abort(self):
        self._abortevt.set()

class Player(xbmc.Player):
    def __init__(self):
        super(Player, self).__init__()
        self.publish = None
        self.playingFile = ''
        self.totalTime = -1
        self.playingTime = 0

    def playing_type(self):
        """
        @return: [music|movie|episode|stream|liveTV|recordedTV|PVRradio|unknown]
        """
        substrings = ['-trailer', 'http://']
        isMovie = False
        if self.isPlayingAudio():
            return "music"
        else:
            if xbmc.getCondVisibility('VideoPlayer.Content(movies)'):
                isMovie = True
        try:
            filename = self.getPlayingFile()
        except:
            filename = ''
        if filename != '':
            if filename[0:3] == 'pvr':
                if xbmc.getCondVisibility('Pvr.IsPlayingTv'):
                    return 'liveTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRecording'):
                    return 'recordedTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
                    return 'PVRradio'
                else:
                    for string in substrings:
                        if string in filename:
                            isMovie = False
                            break
        if isMovie:
            return "movie"
        elif xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
            # Check for tv show title and season to make sure it's really an episode
            if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                return "episode"
        elif xbmc.getCondVisibility('Player.IsInternetStream'):
            return 'stream'
        else:
            return 'unknown'

    def getTitle(self):
        if self.isPlayingAudio():
            while xbmc.getInfoLabel('MusicPlayer.Title') is None:
                xbmc.sleep(250)
            return xbmc.getInfoLabel('MusicPlayer.Title')
        elif self.isPlayingVideo():
            while xbmc.getInfoLabel('VideoPlayer.Title') is None:
                xbmc.sleep(250)
            if xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
                if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                    return (xbmc.getInfoLabel('VideoPlayer.TVShowTitle') + '-Season ' +
                            xbmc.getInfoLabel('VideoPlayer.Season') + '-' + xbmc.getInfoLabel('VideoPlayer.Title'))
            else:
                return xbmc.getInfoLabel('VideoPlayer.Title')
        else:
            return 'Kodi cannot detect title'


    def getPlayingFileX(self):
        try:
            fn = self.getPlayingFile()
        except:
            fn = 'unknown'
        if fn is None:
            fn = 'Kodi returned playing file is none'
        return xbmc.translatePath(fn)

    def getAspectRatio(self):
        try:
            ar = xbmc.getInfoLabel("VideoPlayer.VideoAspect")
        except:
            ar = 'unknown'
        if ar is None:
            ar = 'unknown'
        return str(ar)

    def getResoluion(self):
        try:
            vr = xbmc.getInfoLabel("VideoPlayer.VideoResolution")
        except:
            vr = 'unknown'
        if vr is None:
            vr = 'unknown'
        return str(vr)

    def onPlayBackStarted(self):
        self.playingFile = self.getPlayingFileX()
        try:
            self.totalTime = self.getTotalTime()
        except:
            self.totalTime = -1
        topic = Topic('onPlayBackStarted')
        kwargs = {'mediaType':self.playing_type(), 'fileName':self.getPlayingFileX(), 'title':self.getTitle(), 'aspectRatio':self.getAspectRatio(), 'resolution':self.getResoluion()}
        self.publish(Message(topic, **kwargs))

    def onPlayBackEnded(self):
        topic = Topic('onPlayBackEnded')
        try:
            tt = self.totalTime
            tp = self.playingTime
            pp = int(100 * tp/tt)
        except Exception as e:
            pp=-1
        kwargs = {'fileName':self.playingFile, 'percentPlayed':str(pp)}
        self.publish(Message(topic, **kwargs))

    def onPlayBackStopped(self):
        self.onPlayBackEnded()

    def onPlayBackPaused(self):
        topic = Topic('onPlayBackPaused')
        kwargs = {'time':str(self.getTime())}
        self.publish(Message(topic, **kwargs))

    def onPlayBackResumed(self):
        topic = Topic('onPlayBackResumed')
        kwargs = {}
        self.publish(Message(topic, **kwargs))

    def onPlayBackSeek(self, time, seekOffset):
        topic = Topic('onPlayBackSeek')
        kwargs = {'time':str(time)}
        self.publish(Message(topic, **kwargs))

    def onPlayBackSeekChapter(self, chapter):
        topic = Topic('onPlayBackSeekChapter')
        kwargs = {'chapter':str(chapter)}
        self.publish(Message(topic, **kwargs))

    def onPlayBackSpeedChanged(self, speed):
        topic = Topic('onPlayBackSpeedChanged')
        kwargs = {'speed':str(speed)}
        self.publish(Message(topic, **kwargs))

    def onQueueNextItem(self):
        topic = Topic('onQueueNextItem')
        kwargs = {}
        self.publish(Message(topic, **kwargs))

