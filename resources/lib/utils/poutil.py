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
import fnmatch
import re
import operator
import xbmcaddon

class KodiPo(object):

    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(KodiPo, cls).__new__(cls)
            KodiPo.cls_init(cls)
        return cls._instance

    @staticmethod
    def cls_init(cls):
        try:
            isStub = xbmcaddon.isStub
        except:
            isStub = False
        if isStub is False:
            cls.pofn =  os.path.join(xbmcaddon.Addon('service.kodi.callbacks').getAddonInfo('path'), r'resources\language\English\strings.po')
        else:
            cls.pofn = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\language\English\strings.po'
        cls.podict = PoDict()
        cls.podict.read_from_file(cls.pofn)
        cls.updateAlways = False


    def __init__(self):
        pass

    def getLocalizedString(self, strToId, update=False):
        strToId = strToId.replace('\n', '\\n')
        idFound, strid = self.podict.has_msgid(strToId)
        if idFound:
            return xbmcaddon.Addon().getLocalizedString(int(strid))
        else:
            if update is True or self.updateAlways is True:
                self.updatePo(strid, strToId)
        return strToId

    def getLocalizedStringId(self, strToId, update=False):
        idFound, strid = self.podict.has_msgid(strToId)
        if idFound:
            return strid
        else:
            if update is True or self.updateAlways is True:
                self.updatePo(strid, strToId)
                return strid
            else:
                return 'String not found'

    def updatePo(self, strid, txt):
        self.podict.addentry(strid, txt)
        self.podict.write_to_file(self.pofn)

class PoDict(object):
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(PoDict, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.dict_msgctxt = dict()
        self.dict_msgid = dict()
        self.chkdict = dict()

    def get_new_key(self):
        if len(self.dict_msgctxt) > 0:
            mmax = max(self.dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        else:
            mmax = '32000'
        try:
            int_key = int(mmax)
        except ValueError:
            int_key = -1
        return int_key + 1

    def addentry(self, str_msgctxt, str_msgid):
        self.dict_msgctxt[str_msgctxt] = str_msgid
        self.dict_msgid[str_msgid] = str_msgctxt

    def has_msgctxt(self, str_msgctxt):
        if str_msgctxt in self.dict_msgctxt:
            return [True, self.dict_msgctxt[str_msgctxt]]
        else:
            return [False, None]

    def has_msgid(self, str_msgid):
        if str_msgid in self.dict_msgid:
            return [True, self.dict_msgid[str_msgid]]
        else:
            return [False, str(self.get_new_key())]

    def read_from_file(self, url):
        if url is None:
            return
        if os.path.exists(url):
            with open(url, 'r') as f:
                poin = f.readlines()
            i = 0
            while i < len(poin):
                line = poin[i]
                if line[0:7] == 'msgctxt':
                    t = re.findall(r'".+"', line)
                    str_msgctxt = t[0][2:7]
                    i += 1
                    line2 = poin[i]
                    str_msgid = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line2)[0]
                    self.dict_msgctxt[str_msgctxt] = str_msgid
                    self.dict_msgid[str_msgid] = str_msgctxt
                    self.chkdict[str_msgctxt] = False
                i += 1

    def write_to_file(self, url):
        self._write_to_file(self.dict_msgctxt, url)

    @staticmethod
    def _write_to_file(dict_msgctxt, url):
        fo = open(url, 'w')
        PoDict.write_po_header(fo)
        str_max = max(dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        str_min = min(dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        fo.write('#Add-on messages id=%s to %s\n\n' % (str_min, str_max))
        last = int(str_min) - 1
        for str_msgctxt in sorted(dict_msgctxt):
            if int(str_msgctxt) != last + 1:
                fo.write('#empty strings from id %s to %s\n\n' % (str(last + 1), str(int(str_msgctxt) - 1)))
            PoDict.write_to_po(fo, str_msgctxt, PoDict.format_string_forpo(dict_msgctxt[str_msgctxt]))
            last = int(str_msgctxt)
        fo.close()

    @staticmethod
    def format_string_forpo(mstr):
        out = ''
        for (i, x) in enumerate(mstr):
            if i == 1 and x == r'"':
                out += "\\" + x
            elif x == r'"' and mstr[i-1] != "\\":
                out += "\\" + x
            else:
                out += x
        return out

    @staticmethod
    def write_po_header(fo):
        fo.write('# XBMC Media Center language file\n')
        fo.write('# Addon Name: Kodi Callbacks\n')
        fo.write('# Addon id: service.kodi.callbacks\n')
        fo.write('# Addon Provider: KenV99\n')
        fo.write('msgid ""\n')
        fo.write('msgstr ""\n')
        fo.write('"Project-Id-Version: XBMC Addons\\n"\n')
        fo.write('"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
        fo.write('"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
        fo.write('"MIME-Version: 1.0\\n"\n')
        fo.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        fo.write('"Content-Transfer-Encoding: 8bit\\n"\n')
        fo.write('"Language: en\\n"')
        fo.write('"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n\n')

    @staticmethod
    def write_to_po(fileobject, int_num, str_msg):
        w = r'"#' + str(int_num) + r'"'
        fileobject.write('msgctxt ' + w + '\n')
        fileobject.write('msgid ' + r'"' + str_msg + r'"' + '\n')
        fileobject.write('msgstr ' + r'""' + '\n')
        fileobject.write('\n')

    def createreport(self):
        cnt = 0
        reportpo = []
        for x in self.chkdict:
            if not self.chkdict[x]:
                if cnt == 0:
                    reportpo = ['No usage found for the following pairs:']
                msgid = self.dict_msgctxt[x]
                reportpo.append('    %s:%s' % (x, msgid))
                cnt += 1
        ret = '\n    '.join(reportpo)
        return ret


class UpdatePo(object):

    def __init__(self, root_directory_to_scan, current_working_English_strings_po, exclude_directories=None, exclude_files=None):
        if exclude_directories is None:
            exclude_directories = []
        if exclude_files is None:
            exclude_files = []
        self.root_directory_to_scan = root_directory_to_scan
        self.current_working_English_strings_po = current_working_English_strings_po
        self.podict = PoDict()
        self.podict.read_from_file(self.current_working_English_strings_po)
        self.exclude_directories = exclude_directories
        self.exclude_files = exclude_files

    def getFileList(self):
        files_to_scan = []
        exclusions = []
        for direct in self.exclude_directories:
            for root, dirname, filenames in os.walk(os.path.join(self.root_directory_to_scan, direct)):
                for filename in filenames:
                    exclusions.append(os.path.join(root, filename))
        for root, dirnames, filenames in os.walk(self.root_directory_to_scan):
            for filename in fnmatch.filter(filenames, '*.py'):
                if os.path.split(filename)[1] in self.exclude_files:
                    continue
                elif os.path.join(root, filename) in exclusions:
                    continue
                else:
                    files_to_scan.append(os.path.join(root, filename))
        return files_to_scan

    def scanPyFilesForStrings(self):
        files = self.getFileList()
        lstrings = []
        for myfile in files:
            with open(myfile, 'r') as f:
                lines = ''.join(f.readlines())
            try:
                finds = re.findall(r"_\('(.+?)'\)", lines)
            except re.error:
                finds = []
            lstrings += finds
        return lstrings

    def updateStringsPo(self):
        lstrings = self.scanPyFilesForStrings()
        for s in lstrings:
            found, strid = self.podict.has_msgid(s)
            if found is False:
                self.podict.addentry(strid, s)
        self.podict.write_to_file(self.current_working_English_strings_po)


