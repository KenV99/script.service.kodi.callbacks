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
from resources.lib.pubsub import Publisher, Topic, Message
from resources.lib.events import Events
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString

class PlayerPublisher(threading.Thread, Publisher):
    publishes = Events.Player.keys()
    def __init__(self, dispatcher, settings):
        assert settings is not None
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

    def abort(self, timeout=0):
        self._abortevt.set()
        if timeout > 0:
            self.join(timeout)
            if self.is_alive():
                xbmc.log(msg=_('Could not stop PlayerPublisher T:%i') % self.ident)

class Player(xbmc.Player):
    def __init__(self):
        super(Player, self).__init__()
        self.publish = None
        self.playingFile = ''
        self.playingTitle = ''
        self.playingType = ''
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
        except RuntimeError:
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
        except RuntimeError:
            fn = 'unknown'
        if fn is None:
            fn = 'Kodi returned playing file is none'
        return xbmc.translatePath(fn)

    @staticmethod
    def getAspectRatio():
        ar = xbmc.getInfoLabel("VideoPlayer.VideoAspect")
        if ar is None:
            ar = 'unknown'
        elif ar == '':
            ar = 'unknown'
        return str(ar)

    @staticmethod
    def getResoluion():
        vr = xbmc.getInfoLabel("VideoPlayer.VideoResolution")
        if vr is None:
            vr = 'unknown'
        elif vr == '':
            vr = 'unknown'
        return str(vr)

    def onPlayBackStarted(self):
        self.playingFile = self.getPlayingFileX()
        try:
            self.totalTime = self.getTotalTime()
        except RuntimeError:
            self.totalTime = -1
        self.playingType = self.playing_type()
        self.playingTitle = self.getTitle()
        topic = Topic('onPlayBackStarted')
        kwargs = {'mediaType':self.playingType, 'fileName':self.playingFile, 'title':self.playingTitle, 'aspectRatio':self.getAspectRatio(), 'resolution':self.getResoluion()}
        self.publish(Message(topic, **kwargs))

    def onPlayBackEnded(self):
        topic = Topic('onPlayBackEnded')
        try:
            tt = self.totalTime
            tp = self.playingTime
            pp = int(100 * tp/tt)
        except RuntimeError:
            pp=-1
        kwargs = {'mediaType':self.playingType, 'fileName':self.playingFile, 'title':self.playingTitle, 'percentPlayed':str(pp)}
        self.publish(Message(topic, **kwargs))
        self.playingTitle = ''
        self.playingFile = ''
        self.playingType = ''
        self.totalTime = -1.0
        self.playingTime = 0.0

    def onPlayBackStopped(self):
        self.onPlayBackEnded()

    def onPlayBackPaused(self):
        topic = Topic('onPlayBackPaused')
        kwargs = {'time':str(self.getTime()), 'mediaType':self.playingType}
        self.publish(Message(topic, **kwargs))

    def onPlayBackResumed(self):
        topic = Topic('onPlayBackResumed')
        kwargs = {'mediaType':self.playingType}
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

