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
import json
import os
import re
import urllib2
import requests

import xbmcgui
import xbmcvfs
from resources.lib.utils.poutil import KodiPo
from resources.lib.kodilogging import KodiLogger
from resources.lib.utils.updateaddon import UpdateAddon

kodipo = KodiPo()
_ = kodipo.getLocalizedString
kl = KodiLogger()
log = kl.log

class GitHubTools(object):

    def __init__(self, ua):
        assert isinstance(ua, UpdateAddon)
        self.ua = ua

    def checkForDownload(self):
        try:
            ghversion = GitHubTools.getGHVersion(self.ua.addonxmlurl)
        except GitHubToolsException as e:
            log(msg=e.message)
            return False
        else:
            currentversion = self.ua.currentversion
            if UpdateAddon.is_v1_gt_v2(ghversion, currentversion):
                return True, ghversion, currentversion
            else:
                return False, ghversion, currentversion

    def promptForDownloadAndInstall(self, dryrun=False, updateonly=None):
        if self.checkForDownload()[0] is True:
            if self.ua.silent is False:
                if self.ua.prompt(_('A new version of %s is available\nDownload and install?') % self.ua.addonid) is False:
                    return
            else:
                log(msg='New version found on GitHub. Starting Download/Install.')
            self.downloadAndInstall(dryrun, updateonly)

    def downloadAndInstall(self, dryrun=False, updateonly=None):
        zipfn = os.path.join(self.ua.addondatadir, '%s.zip' % self.ua.addonid)
        try:
            GitHubTools.dlBinaryFile(self.ua.zipurl, zipfn)
        except GitHubToolsException as e:
            self.ua.notify(e.message)
            return
        else:
            self.ua.installFromZip(zipfn, dryrun, updateonly, deletezip=True)


    @staticmethod
    def getGHVersion(url):
        data = GitHubTools.readTextFile(url)
        version = re.findall(r'<addon id\w*=?.+version\w*=\w*"(.+?)"', data)[0]
        return version

    @staticmethod
    def readTextFile(url):
        try:
            f = urllib2.urlopen(url)
            data = f.read()
        except urllib2.HTTPError, urllib2.URLError:
            raise GitHubToolsException(message=_('GitHub Download Error - Error reading file'), iserror=True)
        else:
            return data

    @staticmethod
    def dlBinaryFile(url, destfn):
        u = None
        mprogress = None
        f = None
        if os.path.isfile(destfn):
            os.remove(destfn)
        destfolder = os.path.split(destfn)[0]
        if not os.path.isdir(destfolder):
            os.makedirs(destfolder)
        try:
            u = urllib2.urlopen(url)
            f = open(destfn, 'wb')
            meta = u.info()
            file_size = int(meta.getheaders("Content-Length")[0])
            mprogress = xbmcgui.DialogProgress()
            mprogress.create(_('Downloading %s bytes %s') % (os.path.basename(destfn), file_size))
            file_size_dl = 0
            block_sz = 8192
            while True and not mprogress.iscanceled():
                mbuffer = u.read(block_sz)
                if not mbuffer:
                    break
                file_size_dl += len(mbuffer)
                f.write(mbuffer)
                state = int(file_size_dl * 100. / file_size)
                mprogress.update(state)
            if mprogress.iscanceled():
                mprogress.close()
                try:
                    f.close()
                    os.remove(destfn)
                except OSError:
                    pass
                raise GitHubToolsException(_('Download Cancelled'))
            else:
                mprogress.close()
                f.close()
                del u
        except GitHubToolsException as e:
            raise e
        except Exception as e:
            if hasattr(e, 'message'):
                message = _('GitHub Download Error: %s') % e.message
            else:
                message = _('Unknown GitHub Download Error')
            try:
                if mprogress is not None:
                    mprogress.close()
                if f is not None:
                    f.close()
                if u is not None:
                    del u
            except Exception:
                pass
            if xbmcvfs.exists(destfn):
                try:
                    xbmcvfs.delete(destfn)
                except Exception:
                    pass
            raise GitHubToolsException(message, iserror=True)
        else:
            return True

    @staticmethod
    def dumpfiledatestojson(username, reponame, branch, output_fn, user, password):
        filedict = {}
        r = requests.get('https://api.github.com/repos/%s/%s/commits?per_page=100&sha=%s' % (username, reponame, branch), auth=(user, password))
        commits = r.json()
        while 'next' in r.links.keys():
            r = requests.get(r.links['next']['url'], auth=(user, password))
            commits = commits + r.json()
        for commit in commits:
            commitdate = commit['commit']['author']['date']
            r = requests.get(commit['url'], auth=(user, password))
            details = r.json()
            for xfile in details['files']:
                fn = xfile['filename']
                if fn in filedict.keys():
                    if commitdate > filedict[fn][0]:
                        filedict[fn] = [commitdate, xfile['status']]
                else:
                    filedict[fn] = [commitdate, xfile['status']]
        fd = {}
        for key in filedict.keys():
            if filedict[key][1] != u'removed':
                fd[key] = filedict[key][0]
        with open(output_fn, 'w') as f:
            json.dump(fd, f, ensure_ascii=False)

class GitHubToolsException(Exception):
    def __init__(self, message="Unknown GitHub Error", iserror=False):
        self.message = message
        self.iserror = iserror