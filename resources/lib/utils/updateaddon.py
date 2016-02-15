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
import contextlib
import datetime
import fnmatch
import json
import os
import re
import shutil
import stat
import time
import zipfile
from stat import S_ISREG, ST_MTIME, ST_MODE
from time import strftime

import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.kodilogging import KodiLogger
from resources.lib.utils.kodipathtools import translatepath
from resources.lib.utils.poutil import KodiPo

kodipo = KodiPo()
_ = kodipo.getLocalizedString

kl = KodiLogger()
log = kl.log

debug = True

class UpdateAddon(object):
    def __init__(self, username, reponame, branch='master', src_root=None, addonid=None, silent=False, numbackups=5):
        self.username = username
        self.reponame = reponame
        self.branch = branch
        self.zipurl = r'https://github.com/%s/%s/archive/%s.zip' % (username, reponame, branch)
        if src_root is None:
            self.addonxmlurl = r'https://raw.githubusercontent.com/%s/%s/%s/addon.xml' % (username, reponame, branch)
        else:
            self.addonxmlurl = r'https://raw.githubusercontent.com/%s/%s/%s/%s/addon.xml' % (username, reponame, branch, src_root)
        if addonid is None:
            self.addonid = reponame
        else:
            self.addonid = addonid
        self.addondir = translatepath('special://addon(%s)' % self.addonid)
        self.addondatadir = translatepath('special://addondata(%s)' % self.addonid)
        self.tmpdir = translatepath('%s/temp' % self.addondatadir)
        self.backupdir = translatepath('%s/backup' % self.addondatadir)
        self.currentversion = xbmcaddon.Addon(self.addonid).getAddonInfo('version')
        if self.currentversion == u'':  # Running stub
            self.currentversion = '0.9.0'
        self.silent = silent
        self.numbackups = numbackups

    def prompt(self, strprompt, force=False):
        if not self.silent or force:
            ddialog = xbmcgui.Dialog()
            if ddialog.yesno(self.addonid, strprompt):
                return True
            else:
                return False

    def notify(self, message, force=False):
        log(msg=message)
        if not self.silent or force:
            ddialog = xbmcgui.Dialog()
            ddialog.ok(self.addonid, message)

    def cleartemp(self, recreate=True):
        if os.path.exists(os.path.join(self.tmpdir, '.git')):
            shutil.rmtree(os.path.join(self.tmpdir, '.git'))
        if os.path.exists(self.tmpdir):
            try:
                shutil.rmtree(self.tmpdir, ignore_errors=True)
            except OSError:
                return False
            else:
                if recreate is True:
                    os.mkdir(self.tmpdir)
                    return True
        else:
            if recreate is True:
                os.mkdir(self.tmpdir)
                return True

    @staticmethod
    def unzip(source_filename, dest_dir):
        try:
            with contextlib.closing(zipfile.ZipFile(source_filename , "r")) as zf:
                zf.extractall(dest_dir)
        except zipfile.BadZipfile:
            log(msg='Zip File Error')
            return False
        return True

    @staticmethod
    def zipdir(dest, srcdir):
        dest = '%s.zip' % dest
        zipf = ZipArchive(dest, 'w', zipfile.ZIP_DEFLATED)
        zipf.addDir(srcdir, srcdir)
        zipf.close()


    def backup(self, src=None, destdir=None, numbackups=5):
        if src is None:
            src = self.addondir
        if destdir is None:
            destdir = self.backupdir
        ts = strftime("%Y-%m-%d-%H-%M-%S")
        destname = os.path.join(destdir, '%s-%s' % (ts, self.addonid))
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        else:
            if os.path.exists(destname):
                os.remove(destname)
        self.cleartemp(recreate=True)
        archivedir = os.path.join(self.tmpdir, '%s-%s' % (os.path.split(src)[1], self.branch))
        shutil.copytree(src, archivedir, ignore=shutil.ignore_patterns('*.pyc', '*.pyo', '.git', '.idea'))
        self.zipdir(destname, self.tmpdir)
        self.cleartemp(recreate=False)
        sorteddir = self.datesorteddir(destdir)
        num = len(sorteddir)
        if num > numbackups:
            for i in xrange(0, num-numbackups):
                try:
                    os.remove(sorted(sorteddir)[i][2])
                except OSError:
                    raise
        return True

    @staticmethod
    def datesorteddir(sortdir):  # oldest first
        # returns list of tuples: (index, date, path)

        # get all entries in the directory w/ stats
        entries = (os.path.join(sortdir, fn) for fn in os.listdir(sortdir))
        entries = ((os.stat(path), path) for path in entries)

        # leave only regular files, insert creation date
        entries = ((stat[ST_MTIME], path)
                   for stat, path in entries if S_ISREG(stat[ST_MODE]))
        entrylist = []
        i = 0
        for cdate, path in sorted(entries):
            entrylist.append((i, cdate, path))
            i = i + 1
        return entrylist

    @staticmethod
    def is_v1_gt_v2(version1, version2):
        def normalize(v):
            return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
        result = cmp(normalize(version1), normalize(version2))
        if result == 1:
            return True
        else:
            return False

    @staticmethod
    def getFullFromRelativePath(src, lst, depth):
        srcsplit = os.path.split(src)[1]
        ret = []
        for item in lst:
            splt = item.split('/')
            if len(splt) == depth + 1:
                if srcsplit == splt[-2]:
                    ret.append(os.path.join(src, *splt[depth:]))
            elif depth == 0 and len(splt) ==1:
                ret.append(os.path.join(src, *splt))
        return ret

    @staticmethod
    def copyToDir(src, dst, updateonly=True, ignore=None, forceupdate=None, symlinks=True, dryrun=False, _depth=0):
        def getFullFromRel(src, lst, depth):
            srcsplit = os.path.split(src)[1]
            ret = []
            for item in lst:
                splt = item.split('/')
                if len(splt) == depth + 1:
                    if srcsplit == splt[-2]:
                        ret.append(os.path.join(src, *splt[depth:]))
                elif depth == 0 and len(splt) ==1:
                    ret.append(os.path.join(src, *splt))
            return ret
        fc = []
        if not os.path.exists(dst) and not dryrun:
            os.makedirs(dst)
            shutil.copystat(src, dst)
        lst = os.listdir(src)
        if ignore:
            excl = getFullFromRel(src, ignore, _depth)
        else:
            excl = []
        if forceupdate:
            forcelst = getFullFromRel(src, forceupdate, _depth)
        else:
            forcelst = []
        for item in lst:
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if symlinks and os.path.islink(s) and dryrun is False:
                if os.path.lexists(d):
                    os.remove(d)
                os.symlink(os.readlink(s), d)
                try:
                    st = os.lstat(s)
                    mode = stat.S_IMODE(st.st_mode)
                    os.lchmod(d, mode)
                except OSError:
                    pass  # lchmod not available
            elif os.path.isdir(s):
                fc = fc + UpdateAddon.copyToDir(s, d, updateonly, ignore, forceupdate, symlinks, dryrun, _depth=_depth + 1)
            else:
                if not UpdateAddon.checkfilematch(s, excl):
                    if updateonly:
                        go = False
                        if os.path.isfile(d):
                            srcdate = os.stat(s).st_mtime
                            dstdate = os.stat(d).st_mtime
                            if srcdate > dstdate:
                                go = True
                        else:
                            go = True
                        if UpdateAddon.checkfilematch(s, forcelst):
                            go = True
                        if go is True:
                            fc.append(d)
                            if not dryrun:
                                shutil.copy2(s, d)
                    else:
                        fc.append(d)
                        if not dryrun:
                            shutil.copy2(s, d)
        return fc

    @staticmethod
    def checkfilematch(fn, lst):
        ret = False
        for item in lst:
            if fn == item:
                ret =  True
            elif fnmatch.fnmatchcase(fn, item):
                ret =  True
        return ret

    def installFromZip(self, zipfn, dryrun=False, updateonly=None, deletezip=False):
        if os.path.split(os.path.split(zipfn)[0])[1] == 'backup':
            log(msg='Installing from backup')
            isBackup = True
        else:
            isBackup = False
        unzipdir = os.path.join(self.addondatadir, 'tmpunzip')
        if self.unzip(zipfn, unzipdir) is False:
            self.notify(_('Downloaded file could not be extracted'))
            try:
                os.remove(zipfn)
            except OSError:
                pass
            try:
                shutil.rmtree(unzipdir)
            except OSError:
                pass
            return
        else:
            if deletezip:
                os.remove(zipfn)
        if not isBackup:
            if self.backup(self.addondir, self.backupdir, self.numbackups) is False:
                self.notify(_('Backup failed, update aborted'))
                return
            else:
                log(msg='Backup succeeded.')
        archivedir = os.path.join(unzipdir, '%s-%s' %(self.reponame, self.branch))
        addonisGHA = self.isGitHubArchive(self.addondir)
        if os.path.isfile(os.path.join(archivedir, 'timestamp.json')) and not isBackup:
            fd = self.loadfiledates(os.path.join(archivedir, 'timestamp.json'))
            path = os.path.join(unzipdir, '%s-%s' %(self.addonid, self.branch))
            self.setfiledates(path, fd)
            log(msg='File timestamps updated')
            if updateonly is None:
                updateonly = True
            ziptimestamped = True
        else:
            ziptimestamped = False
            if updateonly is None:
                updateonly = False
        if updateonly is True and addonisGHA:
            updateonly = False
        if updateonly is True and ziptimestamped is False and isBackup is False:
            updateonly = False
        install_root = self.getAddonxmlPath(archivedir)
        if install_root != '':
            try:
                fc = self.copyToDir(install_root, self.addondir, updateonly=updateonly, dryrun=dryrun)
            except OSError as e:
                self.notify(_('Error encountered copying to addon directory: %s') % str(e))
                shutil.rmtree(unzipdir)
                self.cleartemp(recreate=False)
            else:
                if len(fc) > 0:
                    self.cleartemp(recreate=False)
                    shutil.rmtree(unzipdir)
                    if self.silent is False:
                        msg = _('New version installed')
                        if not isBackup:
                            msg += _('\nPrevious installation backed up')
                        self.notify(msg)
                        log(msg='The following files were updated: %s' % str(fc))
                        if self.prompt(_('Attempt to restart addon now?')):
                            restartpath = translatepath('special://addon{%s)/restartaddon.py' % self.addonid)
                            if not os.path.isfile(restartpath):
                                self.createRestartPy(restartpath)
                            xbmc.executebuiltin('RunScript(%s, %s)' % (restartpath, self.addonid))
                else:
                    self.notify(_('All files are current'))
                    self.cleartemp(recreate=False)
                    shutil.rmtree(unzipdir)
        else:
            self.notify(_('Could not find addon.xml\nInstallation aborted'))

    @staticmethod
    def getAddonxmlPath(path):
        ret = ''
        for root, dirs, files in os.walk(path):
            if 'addon.xml' in files:
                ret = root
                break
        return ret

    @staticmethod
    def getTS(strtime):
        t_struct = time.strptime(strtime, '%Y-%m-%dT%H:%M:%SZ')
        ret = time.mktime(t_struct)
        return ret

    @staticmethod
    def setTime(path, strtime):
        ts = UpdateAddon.getTS(strtime)
        os.utime(path, (ts,ts))

    @staticmethod
    def loadfiledates(path):
        if os.path.isfile(path):
            with open(path, 'r') as f:
                try:
                    ret = json.load(f)
                except:
                    raise
                else:
                    return ret
        else:
            return {}

    @staticmethod
    def setfiledates(rootpath, filedict):
        for key in filedict.keys():
            fl = key.split(r'/')
            path = os.path.join(rootpath, *fl)
            if os.path.isfile(path):
                UpdateAddon.setTime(path, filedict[key])

    @staticmethod
    def createRestartPy(path):
        output = []
        output.append('import xbmc')
        output.append('import sys')
        output.append('addonid = sys.argv[1]')
        output.append('xbmc.executeJSONRPC(\'{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled", "params":{"addonid":"%s","enabled":"toggle"},"id":1}\' % addonid)')
        output.append('xbmc.log(msg=\'***** Toggling addon enabled 1: %s\' % addonid)')
        output.append('xbmc.sleep(1000)')
        output.append('xbmc.executeJSONRPC(\'{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled", "params":{"addonid":"%s","enabled":"toggle"},"id":1}\' % addonid)')
        output.append('xbmc.log(msg=\'***** Toggling addon enabled 2: %s\' % addonid)')
        output = '\n'.join(output)
        with open(path, 'w') as f:
            f.writelines(output)

    @staticmethod
    def getFileModTime(path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def createTimeStampJson(src, dst=None, ignore=None):
        if ignore is None:
            ignore = []
        fd = {}
        if dst is None:
            dst = os.path.join(src, 'timestamp.json')
        for root, dirs, files in os.walk(src):
            for fn in files:
                ffn = os.path.join(root, fn)
                relpath = os.path.relpath(ffn, src).replace('\\', '/')
                if not UpdateAddon.checkfilematch(relpath, ignore):
                    fd[relpath] = UpdateAddon.getFileModTime(ffn)
        if os.path.dirname(dst) == src:
            fd[os.path.relpath(dst,src)] = strftime('%Y-%m-%dT%H:%M:%SZ')
        with open(dst, 'w') as f:
            json.dump(fd, f, ensure_ascii=False)

    @staticmethod
    def isGitHubArchive(path):
        filelist = []
        vals = []
        ignoreDirs = ['.git', '.idea']
        ignoreExts = ['.pyo', '.pyc']
        ignoredRoots = []
        for root, dirs, files in os.walk(path):
            dirName = os.path.basename(root)
            if ignoreDirs.count(dirName) > 0:
                ignoredRoots += [root]
                continue
            ignore = False
            for ignoredRoot in ignoredRoots:
                if root.startswith(ignoredRoot):
                    ignore = True
                    break
            if ignore:
                continue
            # add files
            for file in files:
                if os.path.splitext(file)[1] not in ignoreExts:
                    vals.append(os.path.getmtime(os.path.join(root, file)))
                    filelist.append(os.path.join(root, file))
        vals.sort()
        vals = vals[5:-5]
        n = len(vals)
        mean = sum(vals)/n
        stdev = ((sum((x-mean)**2 for x in vals))/n)**0.5
        if stdev/60.0 < 1.0:
            return True
        else:
            return False



class ZipArchive(zipfile.ZipFile):

    verbose = False

    showDebugInfo = False

    def __init__(self, *args, **kwargs):

        self.verbose = kwargs.pop('verbose', self.verbose)
        zipfile.ZipFile.__init__(self, *args, **kwargs)

    def addEmptyDir(self, path, baseToRemove="", inZipRoot=None):

        inZipPath = os.path.relpath(path, baseToRemove)
        if inZipPath == ".":  # path == baseToRemove (but still root might be added
            inZipPath = ""

        if inZipRoot is not None:
            inZipPath = os.path.join(inZipRoot, inZipPath)

        if inZipPath == "":  # nothing to add
            return

        if self.verbose:
            print "Adding dir entry: " + inZipPath
        zipInfo = zipfile.ZipInfo(os.path.join(inZipPath, ''))
        self.writestr(zipInfo, '')

    def addFile(self, filePath, baseToRemove="", inZipRoot=None):

        inZipPath = os.path.relpath(filePath, baseToRemove)

        if inZipRoot is not None:
            inZipPath = os.path.join(inZipRoot, inZipPath)

        if self.verbose:
            print "Adding file: " + filePath
            print "	Under path: " + inZipPath
        self.write(filePath, inZipPath)

    def addDir(self, path, baseToRemove="", ignoreDirs=None, inZipRoot=None):

        if ignoreDirs is None:
            ignoreDirs = []
        ignoredRoots = []
        for root, dirs, files in os.walk(path):
            # ignore e.g. special folders
            dirName = os.path.basename(root)
            if ignoreDirs.count(dirName) > 0:
                ignoredRoots += [root]
                if self.showDebugInfo:
                    print "ignored: " + root
                continue
            # ignore descendants of folders ignored above
            ignore = False
            for ignoredRoot in ignoredRoots:
                if root.startswith(ignoredRoot):
                    ignore = True
                    break
            if ignore:
                continue

            # add dir itself (needed for empty dirs)
            if len(files) <= 0:
                if self.showDebugInfo:
                    print "(root, baseToRemove, inZipRoot) = "
                    print (root, baseToRemove, inZipRoot)
                self.addEmptyDir(root, baseToRemove, inZipRoot)

            # add files
            for file in files:
                self.addFile(os.path.join(root, file), baseToRemove, inZipRoot)
