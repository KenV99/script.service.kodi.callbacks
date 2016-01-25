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
import traceback
import xbmc
import xbmcaddon

__cwd__ = xbmcaddon.Addon('service.kodi.callbacks').getAddonInfo('path')

###############  OPTIONS  ###########################
root_directory_to_scan = __cwd__  # put whichever directory you want here
settings_xml = os.path.join(__cwd__, 'resources', 'settings.xml')
process_xml = False
comment_xml = False
exclude_files = ['poxbmc.py']
exclude_directories = ['localized']  # use 'subdir\\subberdir' to designate deeper
output_directory = os.path.join(__cwd__, 'localized')
current_working_English_strings_po = os.path.join(__cwd__, r'resources\language\English\strings.po')  # set to None
#  is there isn't one
option_add_commented_string_when_localizing = False
# option_verbose_report = True

# tag lines to look for quoted strings with '# @@' (only the part within the quotes)
# triple quoted multiline strings are NOT supported
# please ensure double quotes within strings are properly escaped with \"
# WARNING: all files in output_directory will be overwritted!

# String ID range:
# strings 30000 thru 30999 reserved for plugins and plugin settings
# strings 31000 thru 31999 reserved for skins
# strings 32000 thru 32999 reserved for scripts
# strings 33000 thru 33999 reserved for common strings used in add-ons

#####################################################
podict = None
report_v = []
report_py = []
report_xml = []

class KodiPo(object):

    def __init__(self):
        self.pofn =  os.path.join(xbmcaddon.Addon('service.kodi.callbacks').getAddonInfo('path'), r'resources\language\English\strings.po')
        if self.pofn[0] != 'C':
            self.pofn = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\service.kodi.callbacks\resources\language\English\strings.po'
        self.podict = PoDict()
        self.podict.read_from_file(self.pofn)

    def getLocalizedString(self, strToId):
        idFound, id = self.podict.has_msgid(strToId)
        if idFound:
            return xbmcaddon.Addon().getLocalizedString(int(id))
        else:
            return 'strToId'

    def getLocalizedStringId(self, strToId):
        idFound, id = self.podict.has_msgid(strToId)
        if idFound:
            return id
        else:
            return 'String not found'

class PoDict():

    def __init__(self):
        self.dict_msgctxt = dict()
        self.dict_msgid = dict()
        self.chkdict = dict()
        # self.mdict_msgctxt = dict()
        # self.mdict_msgid = dict()

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
        fo = open(url, 'w')
        self.write_po_header(fo)
        str_max = max(self.dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        str_min = min(self.dict_msgctxt.iteritems(), key=operator.itemgetter(0))[0]
        fo.write('#Add-on messages id=%s to %s\n\n' % (str_min, str_max))
        last = int(str_min) - 1
        for str_msgctxt in sorted(self.dict_msgctxt):
            if int(str_msgctxt) != last + 1:
                fo.write('#empty strings from id %s to %s\n\n' % (str(last + 1), str(int(str_msgctxt) - 1)))
            self.write_to_po(fo, str_msgctxt, self.format_string_forpo(self.dict_msgctxt[str_msgctxt]))
            last = int(str_msgctxt)
        fo.close()

    def format_string_forpo(self, mstr):
        out = ''
        for (i, x) in enumerate(mstr):
            if i == 1 and x == r'"':
                out += "\\" + x
            elif x == r'"' and mstr[i-1] != "\\":
                out += "\\" + x
            else:
                out += x
        return out

    def write_po_header(self, fo):
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

    def write_to_po(self, fileobject, int_num, str_msg):
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


def examinefile(pyin, pyout):
    global podict

    def match_fix(singmatch, dblmatch):
        matches = []
        dblchk = []
        if len(singmatch) > 0 and len(dblmatch) == 0:
            return singmatch
        elif len(dblmatch) > 0 and len(singmatch) == 0:
            return dblmatch
        elif len(dblmatch) == 0 and len(singmatch) == 0:
            return []
        else:
            for match1 in singmatch:
                for match2 in dblmatch:
                    if match1 == match2:
                        dblchk.append(match1)
                    elif match1 in match2:
                        match_append_chk(match2, matches)
                    elif match2 in match1:
                        match_append_chk(match1, matches)
                    else:
                        match_append_chk(match1, matches)
                        match_append_chk(match2, matches)
            matches2 = matches
            for match1 in dblchk:
                for match2 in matches:
                    if match1 in match2:
                        if len(match1) > len(match2):
                            matches2.append(match1)
            return matches2

    def match_append_chk(match, matches):
        if not (match in matches):
            matches.append(match)

    try:
        found_langfxn = False
        uses_langfxn = False
        match_btwn_singq = re.compile(r"'([^'\\]*(?:\\.[^'\\]*)*)'")
        match_btwn_dblq = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
        # match_both_quotes = re.compile(r'(?P<sing>[\']([^\'\\]*(?:\\.[^\'\\]*)*)[\'])|(?P<dbl>"([^"\\]*(?:\\.[^"\\]*)*)")')
        match_tag_examine = re.compile(r'# @@')
        match_tag_comment = re.compile(r'\# @.+')
        match_localized_txt = re.compile('__language__\(.+?\)')
        match_langfxn = re.compile('__language__.+?\.getLocalizedString')
        counter = 0
        triplequoteflag = False
        for line in pyin:
            counter += 1
            x = line.strip()
            if x[0:1] == "#" or x == '':
                pyout.write(line)
                continue
            if x == r'"""':
                pyout.write(line)
                if not triplequoteflag:
                    triplequoteflag = True
                else:
                    triplequoteflag = False
                continue
            if triplequoteflag:
                pyout.write(line)
                continue
            newline = line
            term = ''
            if match_langfxn.search(line) is not None:
                found_langfxn = True
            if match_tag_examine.search(line) is not None:
                singmatch = match_btwn_singq.findall(line)
                dblmatch = match_btwn_dblq.findall(line)
                matches = match_fix(singmatch, dblmatch)
                if len(matches) > 0:
                    uses_langfxn = True
                    for match in matches:
                        res = podict.has_msgid(match)
                        if res[0]:
                            outnum = res[1]
                            podict.chkdict[res[1]] = True
                        else:
                            outnum = res[1]
                            podict.addentry(outnum, match)
                            podict.chkdict[res[1]] = True
                        repl = '__language__(%s)' % outnum
                        if match in singmatch:
                            y = match_btwn_singq.sub(repl, newline, 1)
                        else:
                            y = match_btwn_dblq.sub(repl, newline, 1)
                        newline = y
                        x = newline.find('# @')
                        if x > 1:
                            newline = newline[0:x]
                            newline += '\n'
                        if option_add_commented_string_when_localizing:
                            term += '[%s] ' % match
                else:
                    report_py.append('Tagged but no string found at line %s in %s' % (counter, pyin.name))
            matches = match_localized_txt.findall(line)
            if len(matches) > 0:
                uses_langfxn = True
                for match in matches:
                    str_msgctxt = match[13:18]
                    p = podict.has_msgctxt(str_msgctxt)
                    if p[0]:
                        term += '[' + p[1] + '] '
                        podict.chkdict[str_msgctxt] = True
                    else:
                        report_py.append('Localized string #%s not found in po file at line %s in %s'
                                         % (str_msgctxt, counter, pyin.name))
                if option_add_commented_string_when_localizing:
                    if match_tag_comment.search(newline):
                        term = '# @' + term
                        newline2 = newline[0:newline.find('# @')].rstrip() + '  ' + term + '\n'
                        newline = newline2
                    else:
                        newline = newline[0:int(len(newline)-1)].rstrip()
                        newline += '  # @' + term + '\n'
                pyout.write(newline)
            else:
                if term != '':
                    newline = newline[0:int(len(newline)-1)].rstrip()
                    newline += '  # @' + term + '\n'
                pyout.write(newline)
        if (not found_langfxn) and uses_langfxn:
            report_py.append('Language localization function not found in: %s' % pyin.name)
        pyout.close()
        pyin.close()
    except Exception, e:
        l = traceback.format_exc()
        pass


def examine_xml(xmlin, xmlout):
    """
    @param xmlin:
    @param xmlout:
    @return:
    """
    findlocalized_label = re.compile(r'label=\"\d{5}?\"')
    findlocalized_lvalues = re.compile(r'lvalues=\"(\d+(\|)*)+\"')
    findnonlocalized_label = re.compile(r'label="[^"\\]*(?:\\.[^"\\]*)*"')
    findnonlocalized_lvalues = re.compile(r'lvalues="([^"\\]*(?:\\.[^"\\]*)*)"')
    findcomment = re.compile(r'<!--.+?-->')
    counter = 0
    for line in xmlin:
        counter += 1
        term = ''
        newline = line
        lbmatchesl = findlocalized_label.search(line)
        if lbmatchesl:
            match = lbmatchesl.group()
            if type(match) is str:
                msgctxt = re.search(r'\d{5}?', match).group()
                res = podict.has_msgctxt(msgctxt)
                if res[0]:
                    podict.chkdict[msgctxt] = True
                    term += '[%s]' % res[1]
                else:
                    report_xml.append('Localized string #%s not found in xml file at line %s in %s'
                                      % (msgctxt, counter, xmlin.name))
        lbmatchesnl = findnonlocalized_label.search(line)
        if lbmatchesnl:
            skip = False
            match = lbmatchesnl.group()
            if lbmatchesl is not None:
                if match in lbmatchesl.group():
                    skip = True
            if not skip:
                tmp = re.search(r'"[^"\\]*(?:\\.[^"\\]*)*"', match).group()
                msgid = tmp[1:len(tmp)-1]
                res = podict.has_msgid(msgid)
                if res[0]:
                    outnum = res[1]
                    podict.chkdict[res[1]] = True
                else:
                    outnum = res[1]
                    podict.addentry(outnum, msgid)
                    podict.chkdict[res[1]] = True
                repl = 'label="%s"' % outnum
                newline = re.sub(re.escape(match), repl, line)
                term += '[%s]' % msgid
        lvmatchesl = findlocalized_lvalues.search(line)
        if lvmatchesl:
            match = lvmatchesl.group()
            tmp = re.search(r'\"(\d+(\|)*)+\"', match).group()
            tmp = tmp[1:len(tmp)-1]
            parsed = tmp.split('|')
            for msgctxt in parsed:
                res = podict.has_msgctxt(msgctxt)
                if res[0]:
                    podict.chkdict[msgctxt] = True
                    term += '[%s]' % res[1]
                else:
                    report_xml.append('Localized string #%s not found in xml file at line %s in %s'
                                      % (msgctxt, counter, xmlin.name))
        lvmatchesnl = findnonlocalized_lvalues.search(line)
        if lvmatchesnl:
            match = lvmatchesnl.group()
            tmp = re.search(r'"[^"\\]*(?:\\.[^"\\]*)*"', match).group()
            tmp = tmp[1:len(tmp)-1]
            execute = True
            if lvmatchesl:
                if tmp in lvmatchesl.group():
                    execute = False
            if execute:
                parsed = tmp.split('|')
                for msgid in parsed:
                    outnum = []
                    res = podict.has_msgid(msgid)
                    if res[0]:
                        outnum.append(res[1])
                        podict.chkdict[res[1]] = True
                    else:
                        outnum.append(res[1])
                        podict.addentry(res[1], msgid)
                        podict.chkdict[res[1]] = True
                    repl = res[1]
                    x = re.sub(re.escape(msgid), repl, newline)
                    newline = x
                    term += '[%s]' % msgid

        if comment_xml and term != '':
            term = '<!--%s-->' % term
            matchescom = findcomment.findall(line)
            if len(matchescom) > 0:
                match = matchescom[len(matchescom)-1]
                x = re.sub(re.escape(match), term, newline)
            else:
                x = newline[0:len(newline)-1] + term + '\n'
            newline = x
        xmlout.write(newline)

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

    def scanFilesForStrings(self):
        files = self.getFileList()
        lstrings = []
        for file in files:
            with open(file, 'r') as f:
                lines = ''.join(f.readlines())
            try:
                finds = re.findall(r"_\('(.+?)'\)", lines)
            except Exception as e:
                finds = []
            lstrings += finds
        return lstrings

    def updateStringsPo(self):
        lstrings = self.scanFilesForStrings()
        for s in lstrings:
            found, strid = self.podict.has_msgid(s)
            if found is False:
                self.podict.addentry(strid, s)
        self.podict.write_to_file(self.current_working_English_strings_po)
        pass
        pass




def main():

    global podict
    podict = PoDict()
    podict.read_from_file(current_working_English_strings_po)

    output_root_dir = os.path.join(root_directory_to_scan, 'localized')
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)
    output_po_dir = os.path.join(output_root_dir, 'resources', 'language', 'English')
    if not os.path.exists(output_po_dir):
        os.makedirs(output_po_dir)
    outputfnpofull = os.path.join(output_po_dir, 'strings.po')
    if os.path.exists(outputfnpofull):
        os.remove(outputfnpofull)

    if process_xml:
        xmloutfullfn = os.path.join(__cwd__, 'localized', 'resources', 'settings.xml')
        xmlin = open(settings_xml, 'r')
        xmlout = open(xmloutfullfn, 'w')
        examine_xml(xmlin, xmlout)
        xmlout.close()
        xmlin.close()

    files_to_scan = []
    exclusions = []
    for direct in exclude_directories:
        for root, dirname, filenames in os.walk(os.path.join(root_directory_to_scan, direct)):
            for filename in filenames:
                exclusions.append(os.path.join(root, filename))
    for root, dirnames, filenames in os.walk(root_directory_to_scan):
        for filename in fnmatch.filter(filenames, '*.py'):
            x = os.path.relpath(root, root_directory_to_scan)
            if os.path.split(filename)[1] in exclude_files:
                continue
            elif os.path.join(root, filename) in exclusions:
                continue
            else:
                if x != '.':
                    outpath = os.path.join(output_root_dir, x)
                    if not os.path.exists(outpath):
                        os.makedirs(outpath)
                else:
                    outpath = output_root_dir
                files_to_scan.append([os.path.join(root, filename), os.path.join(outpath, filename)])

    for mfile in files_to_scan:

        inputfnfull = mfile[0]
        outputfnpyfull = mfile[1]
        if os.path.exists(outputfnpyfull):
            os.remove(outputfnpyfull)
        pyin = open(inputfnfull, 'r')
        pyout = open(outputfnpyfull, 'w')
        try:
            examinefile(pyin, pyout)
        except Exception, e:
            l = traceback.format_exc()
            pass
        pyout.close()
        pyin.close()
    podict.write_to_file(outputfnpofull)
    report = 'Settings.xml report:\n    '
    sreport = '\n    '.join(report_xml)
    if sreport == '':
        sreport = 'All settings were able to be localized with no errors\n'
    report += sreport + '\n\n' + 'Python files report:\n    '
    preport = '\n    '.join(report_py)
    if preport == '':
        preport = 'All python files were localized with no errors\n'
    report += preport + '\n\n' + 'English strings.po report:\n    '
    poreport = podict.createreport()
    if poreport == '':
        poreport = 'Strings.po file scanned with no errors\n'
    report += poreport
    reportfn = os.path.join(__cwd__, "localized", 'report.txt')
    fo = open(reportfn, 'w')
    fo.write(report)
    fo.close()

if __name__ == '__main__':
    main()