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
import shutil
import fnmatch
import stat
import itertools

def copyToDir(src, dst, updateonly=True, symlinks=True, ignore=None, forceupdate=None, dryrun=False):

    def copySymLink(srclink, destlink):
        if os.path.lexists(destlink):
            os.remove(destlink)
        os.symlink(os.readlink(srclink), destlink)
        try:
            st = os.lstat(srclink)
            mode = stat.S_IMODE(st.st_mode)
            os.lchmod(destlink, mode)
        except OSError:
            pass  # lchmod not available
    fc = []
    if not os.path.exists(dst) and not dryrun:
        os.makedirs(dst)
        shutil.copystat(src, dst)
    if ignore is not None:
        ignorepatterns = [os.path.join(src, *x.split('/')) for x in ignore]
    else:
        ignorepatterns = []
    if forceupdate is not None:
        forceupdatepatterns = [os.path.join(src, *x.split('/')) for x in forceupdate]
    else:
        forceupdatepatterns = []
    srclen = len(src)
    for root, dirs, files in os.walk(src):
        fullsrcfiles = [os.path.join(root, x) for x in files]
        t = root[srclen+1:]
        dstroot = os.path.join(dst, t)
        fulldstfiles = [os.path.join(dstroot, x) for x in files]
        excludefiles = list(itertools.chain.from_iterable([fnmatch.filter(fullsrcfiles, pattern) for pattern in ignorepatterns]))
        forceupdatefiles = list(itertools.chain.from_iterable([fnmatch.filter(fullsrcfiles, pattern) for pattern in forceupdatepatterns]))
        for directory in dirs:
            fullsrcdir = os.path.join(src, directory)
            fulldstdir = os.path.join(dstroot, directory)
            if os.path.islink(fullsrcdir):
                if symlinks and dryrun is False:
                    copySymLink(fullsrcdir, fulldstdir)
            else:
                if not os.path.exists(fulldstdir) and dryrun is False:
                    os.makedirs(fulldstdir)
                    shutil.copystat(src, dst)
        for s,d in zip(fullsrcfiles, fulldstfiles):
            if s not in excludefiles:
                if updateonly:
                    go = False
                    if os.path.isfile(d):
                        srcdate = os.stat(s).st_mtime
                        dstdate = os.stat(d).st_mtime
                        if srcdate > dstdate:
                            go = True
                    else:
                        go = True
                    if s in forceupdatefiles:
                        go = True
                    if go is True:
                        fc.append(d)
                        if not dryrun:
                            if os.path.islink(s) and symlinks is True:
                                copySymLink(s, d)
                            else:
                                shutil.copy2(s, d)
                else:
                    fc.append(d)
                    if not dryrun:
                        if os.path.islink(s) and symlinks is True:
                            copySymLink(s, d)
                        else:
                            shutil.copy2(s, d)
    return fc
#
# def copyToDirOld(src, dst, updateonly=True, ignore=None, forceupdate=None, symlinks=True, dryrun=False, _depth=0):
#     def getFullFromRel(srcdir, filelist, filterlist, depth):
#         root = srcdir
#         for _ in xrange(0, depth):
#             root = os.path.split(root)[0]
#         ret = []
#         for relativepattern in filterlist:
#             pattern = os.path.join(root, *relativepattern.split('/'))
#             ret = ret + (fnmatch.filter([os.path.join(srcdir, x) for x in filelist], pattern))
#         return ret
#     fc = []
#     if not os.path.exists(dst) and not dryrun:
#         os.makedirs(dst)
#         shutil.copystat(src, dst)
#     lst = os.listdir(src)
#     if ignore:
#         excl = getFullFromRel(src, lst, ignore, _depth)
#     else:
#         excl = []
#     if forceupdate:
#         forcelst = getFullFromRel(src, lst, forceupdate, _depth)
#     else:
#         forcelst = []
#     for item in lst:
#         s = os.path.join(src, item)
#         d = os.path.join(dst, item)
#         if symlinks and os.path.islink(s) and dryrun is False:
#             if os.path.lexists(d):
#                 os.remove(d)
#             os.symlink(os.readlink(s), d)
#             try:
#                 st = os.lstat(s)
#                 mode = stat.S_IMODE(st.st_mode)
#                 os.lchmod(d, mode)
#             except OSError:
#                 pass  # lchmod not available
#         elif os.path.isdir(s):
#             fc = fc + copyToDirOld(s, d, updateonly, ignore, forceupdate, symlinks, dryrun, _depth=_depth + 1)
#         else:
#             if s not in excl:
#                 if updateonly:
#                     go = False
#                     if os.path.isfile(d):
#                         srcdate = os.stat(s).st_mtime
#                         dstdate = os.stat(d).st_mtime
#                         if srcdate > dstdate:
#                             go = True
#                     else:
#                         go = True
#                     if s in forcelst:
#                         go = True
#                     if go is True:
#                         fc.append(d)
#                         if not dryrun:
#                             shutil.copy2(s, d)
#                 else:
#                     fc.append(d)
#                     if not dryrun:
#                         shutil.copy2(s, d)
#     return fc
#
# def testCTDOld():
#     path = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks'
#     fc = copyToDirOld(path, r'C:\Temp', ignore=['.git/*', '.idea/*', '*.pyc', '*.pyo'], dryrun=True)
#     assert isinstance(fc, list)
#
#
# def testCTD():
#     path = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks'
#     fc = copyToDir(path, r'C:\Temp', ignore=['.git/*', '.idea/*', '*.pyc', '*.pyo'], dryrun=True)
#     assert isinstance(fc, list)
#
# if __name__ == '__main__':
#         testCTD()