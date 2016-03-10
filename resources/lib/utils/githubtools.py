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
import codecs
import json
import os
import re
import traceback
import urllib2

import requests

import xbmcaddon
import xbmcgui
from resources.lib.kodilogging import KodiLogger
from resources.lib.utils.kodipathtools import translatepath
from resources.lib.utils.poutil import KodiPo
from resources.lib.utils.updateaddon import UpdateAddon

kodipo = KodiPo()
_ = kodipo.getLocalizedString
kl = KodiLogger()
log = kl.log

dryrun = False
addonid = 'script.service.kodi.callbacks'
GHUser = 'KenV99'
reponame = addonid


def processargs(argv):
    if len(argv) > 1:
        if argv[1] == 'checkupdate':
            KodiLogger.setLogLevel(KodiLogger.LOGNOTICE)
            branchname = xbmcaddon.Addon().getSetting('repobranchname')
            downloadnew, ghversion, currentversion = GitHubTools.checkForDownload(GHUser, reponame, branchname, addonid)
            dialog = xbmcgui.Dialog()
            if downloadnew is True:
                answer = dialog.yesno(_('New version available for branch: %s' % branchname),
                                      line1=_('Current version: %s') % currentversion,
                                      line2=_('Available version: %s') % ghversion,
                                      line3=_('Download and install?'))
            else:
                answer = dialog.yesno(_('A new version is not available for branch: %s' % branchname),
                                      line1=_('Current version: %s') % currentversion,
                                      line2=_('Available version: %s') % ghversion,
                                      line3=_('Download and install anyway?'))
            if answer != 0:
                silent = (xbmcaddon.Addon().getSetting('silent_install') == 'true')
                GitHubTools.downloadAndInstall(GHUser, reponame, addonid, branchname, dryrun=dryrun,
                                               updateonly=downloadnew, silent=silent)
    else:
        GitHubTools.updateSettingsWithBranches('repobranchname', GHUser, reponame)
        if xbmcaddon.Addon().getSetting('autodownload') == 'true':
            silent = (xbmcaddon.Addon().getSetting('silent_install') == 'true')
            branchname = xbmcaddon.Addon().getSetting('repobranchname')
            GitHubTools.downloadAndInstall(GHUser, reponame, addonid, branchname, dryrun=dryrun, updateonly=True,
                                           silent=silent)


class GitHubTools(object):
    @staticmethod
    def checkForDownload(username, reponame, branch, addonid):
        addonxmlurl = r'https://raw.githubusercontent.com/%s/%s/%s/addon.xml' % (username, reponame, branch)
        try:
            ghversion = GitHubTools.getGHVersion(addonxmlurl)
        except GitHubToolsException as e:
            log(msg=e.message)
            return False
        else:
            currentversion = UpdateAddon.currentversion(addonid)
            if UpdateAddon.is_v1_gt_v2(ghversion, currentversion):
                return True, ghversion, currentversion
            else:
                return False, ghversion, currentversion

    @staticmethod
    def promptForDownloadAndInstall(username, reponame, addonid, branch, dryrun=False, updateonly=None):
        if GitHubTools.checkForDownload(username, reponame, branch, addonid)[0] is True:

            if UpdateAddon.prompt(_('A new version of %s is available\nDownload and install?') % addonid) is False:
                return
            else:
                log(msg='New version found on GitHub. Starting Download/Install.')
                GitHubTools.downloadAndInstall(username, reponame, addonid, branch, dryrun, updateonly)

    @staticmethod
    def downloadAndInstall(username, reponame, addonid, branch, updateonly=None, dryrun=False, silent=False):
        zipurl = r'https://github.com/%s/%s/archive/%s.zip' % (username, reponame, branch)
        zipfn = os.path.join(translatepath('special://addondata(%s)' % addonid), '%s.zip' % addonid)
        try:
            GitHubTools.dlBinaryFile(zipurl, zipfn)
        except GitHubToolsException as e:
            log(msg='GitHubTools Exception: %s' % e.message)
            if e.iserror:
                raise e
        else:
            ua = UpdateAddon(addonid, silent=silent)
            ua.installFromZip(zipfn, dryrun=dryrun, updateonly=updateonly, deletezip=True, silent=silent)

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
        except (urllib2.HTTPError, urllib2.URLError):
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
            cl = meta.getheaders("Content-Length")
            if isinstance(cl, list):
                file_size = int(cl[0])
            else:
                file_size = int(cl)
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
        except urllib2.HTTPError as e:
            raise GitHubToolsException(message='GitHubTools HTTPError - Code: %s' % e.code)
        except urllib2.URLError as e:
            raise GitHubToolsException(message='GitHubTools URLError: %s' % str(e.reason), iserror=True)
        except Exception as e:
            if hasattr(e, 'message'):
                message = _('GitHub Download Error: %s') % e.message
            else:
                message = _('Unknown GitHub Download Error')
            message += '\n' + traceback.format_exc()
            try:
                if mprogress is not None:
                    mprogress.close()
                if f is not None:
                    f.close()
                if u is not None:
                    del u
            except Exception:
                pass
            if os.path.exists(destfn):
                try:
                    os.remove(destfn)
                except OSError:
                    pass
            raise GitHubToolsException(message, iserror=True)
        else:
            return True

    @staticmethod
    def dumpfiledatestojson(username, reponame, branch, output_fn, user, password):
        filedict = {}
        r = requests.get(
            'https://api.github.com/repos/%s/%s/commits?per_page=100&sha=%s' % (username, reponame, branch),
            auth=(user, password))
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

    @staticmethod
    def getbranches(username, reponame):
        try:
            r = requests.get('https://api.github.com/repos/%s/%s/branches' % (username, reponame))
        except (requests.HTTPError, requests.ConnectionError) as e:
            msg = 'Get branches Error: %s' % str(e)
            log(msg=msg)
            raise GitHubToolsException(message=msg, iserror=True)
        else:
            branches = r.json()
            ret = []
            for branch in branches:
                ret.append(branch['name'])
            return ret

    @staticmethod
    def updateSettingsWithBranches(tag, username, reponame, addonid=None):
        if addonid is None:
            addonid = reponame
        try:
            branches = GitHubTools.getbranches(username, reponame)
        except GitHubToolsException:
            return False
        else:
            settingspath = translatepath('special://addon(%s)/resources/settings.xml' % addonid)
            branches = r'\g<1>%s\g<2>' % '|'.join(branches)
            pattern = r'(%s.+?values*=*\").+?(\")' % tag
            with codecs.open(settingspath, 'r', 'UTF-8') as f:
                lines = f.read()
            newlines = re.sub(pattern, branches, lines)
            if not newlines == lines:
                with codecs.open(settingspath, 'w', 'UTF-8') as f:
                    f.write(newlines)
                return True
            else:
                return False


class GitHubToolsException(Exception):
    def __init__(self, message="Unknown GitHub Error", iserror=False):
        self.message = message
        self.iserror = iserror
