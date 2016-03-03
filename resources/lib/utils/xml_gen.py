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
from resources.lib.events import Events
from resources.lib  import taskdict
from resources.lib.kodilogging import KodiLogger
import xbmcaddon
import os
import codecs
from resources.lib.utils.poutil import KodiPo, PoDict
kodipo = KodiPo()
kodipo.updateAlways = True
glsid = kodipo.getLocalizedStringId
__ = kodipo.podict.has_msgctxt
kl = KodiLogger()
log = kl.log
podict = PoDict()
pofile = os.path.join(xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('path').decode("utf-8"), 'resources', 'language', 'English', 'strings.po')
if pofile.startswith('resources'):
    pofile = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\language\English\strings.po'
podict.read_from_file(pofile)


def generate_settingsxml(fn=None):
    podirty = False
    allevts = Events().AllEvents
    output = []
    ssp = '    <setting '
    evts = []
    for evtkey in allevts.keys():
        evts.append(allevts[evtkey]['text'])
    evts.sort()
    evts.insert(0, 'None')
    levts = []
    for evt in evts:
        levts.append(glsid(evt))
    levts = "|".join(levts)

    def getoffset(idxx, lst):
        return str(idxx - len(lst))

    output.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    output.append('<settings>\n')
    output.append('  <category label="%s">\n' % glsid('Tasks'))

    startnum = int(kodipo.getLocalizedStringId('Task 1')) - 1
    tasks = []
    idx_prev = 0
    for i in xrange(1,11):
        prefix = "T%s" % str(i)

        tasks.append(str(startnum + i))

        taskchoices = ['none']
        for key in sorted(taskdict.keys()):
            taskchoices.append(key)
        ltaskchoices = []
        for taskchoice in taskchoices:
            found, strid = podict.has_msgid(taskchoice)
            if found is False:
                podict.addentry(strid, taskchoice)
                podirty = True
            ltaskchoices.append(strid)
        ltaskchoices = "|".join(ltaskchoices)
        if i == 1:
            output.append('    <setting label="%s" type="lsep" />\n' % str(startnum + i))
            idx = len(output)
            output.append('    <setting default="none" id="%s.type" label="%s" type="labelenum" lvalues="%s" />\n' % (prefix, glsid('Task'), ltaskchoices))
        else:
            output.append('    <setting label="%s" type="lsep" visible="!eq(%s,0)" />\n' % (str(startnum + i), str(getoffset(idx_prev, output))))
            idx = len(output)
            output.append('    <setting default="none" id="%s.type" label="%s" type="labelenum" lvalues="%s" visible="!eq(%s,0)" />\n' % (prefix, glsid('Task'), ltaskchoices, str(getoffset(idx_prev, output))))
        output.append('    <setting default="-1" id="%s.maxrunning" label="%s" type="number" visible="!eq(-1,0)" />\n' % (prefix, glsid('Max num of this task running simultaneously (-1=no limit)')))
        output.append('    <setting default="-1" id="%s.maxruns" label="%s" type="number" visible="!eq(-2,0)" />\n' % (prefix, glsid('Max num of times this task runs (-1=no limit)')))
        output.append('    <setting default="-1" id="%s.refractory" label="%s" type="number" visible="!eq(-3,0)" />\n' % (prefix, glsid('Refractory period in secs (-1=none)')))
        for i1, key in enumerate(sorted(taskdict.keys())):
            for var in taskdict[key]['variables']:
                varset = var['settings']
                if varset['type'] == 'sfile':
                    mytype = 'file'
                else:
                    mytype = varset['type']
                try:
                    option = varset['option']
                except KeyError:
                    if varset['type'] == 'sfile':
                        labelbrowse = glsid('%s - %s' % (__(varset['label'])[1], 'browse'))
                        labeledit = glsid('%s - %s' % (__(varset['label'])[1], 'edit'))
                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], labelbrowse, mytype, getoffset(idx,output), i1+1))

                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], labeledit, 'text', getoffset(idx,output), i1+1))
                    else:
                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], varset['label'], mytype, getoffset(idx,output), i1+1))
                else:
                    if varset['type'] == 'sfile':
                        labelbrowse = glsid('%s - %s' % (__(varset['label'])[1], 'browse'))
                        labeledit = glsid('%s - %s' % (__(varset['label'])[1], 'edit'))
                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" option="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], labelbrowse, mytype, option, getoffset(idx,output), i1+1))

                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], labeledit, 'text', getoffset(idx,output), i1+1))
                    else:
                        output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" option="%s" visible="eq(%s,%s)" />\n' %
                                      (varset['default'], prefix, var['id'], varset['label'], mytype, option, getoffset(idx,output), i1+1))
        idx_prev = idx
    output.append('  </category>\n\n')
    output.append('  <category label="%s">\n' % glsid('Events'))
    tasks = '|'.join(tasks)

    startnum = int(kodipo.getLocalizedStringId('Event 1')) - 1
    idx_prev = 0
    for i in xrange(1,11):
        prefix = 'E%s' % str(i)
        output.append(ssp + 'label="%s" type="lsep" visible="!eq(%s,%s)" />\n' % (str(startnum + i), getoffset(idx_prev, output), glsid('None')))
        # output.append(ssp + 'default="None" id="%s.type" label="%s" type="select" values="%s" />\n' % (prefix, _('Type'), evts))
        output.append(ssp + 'label="%s" type="action" action="RunScript(script.service.kodi.callbacks, lselector, id=%s.type, heading=%s, lvalues=%s)" visible="!eq(%s,%s)" />\n' % (glsid('Choose event type'), prefix, glsid('Choose event type'), levts, getoffset(idx_prev, output), glsid('None')))
        output.append(ssp + 'ldefault="%s" id="%s.type-v" label="%s" type="select" enable="false" lvalues="%s" visible="!eq(%s,%s)" />\n' % (glsid('None'), prefix, glsid('Event:'), levts, getoffset(idx_prev, output), glsid('None')))
        idx = len(output)
        output.append(ssp + 'default="%s" id="%s.type" label="" type="text" visible="false" />\n' % (glsid('None'), prefix))
        output.append(ssp + 'default="Task 1" id="%s.task" label="%s" type="labelenum" visible="!eq(%s,%s)" lvalues="%s" />\n' % (prefix, glsid('Task'), getoffset(idx, output), glsid('None'), tasks))
        for evtkey in allevts.keys():
            evt = allevts[evtkey]
            for req in evt['reqInfo']:
                r1 = req[1]
                if r1 in ['float', 'int']:
                    r1 = 'number'
                if r1 == 'sfolder':
                    mytype = 'folder'
                else:
                    mytype = r1
                if r1 == 'sfolder':
                    labelbrowse = glsid('%s - browse' % req[0])
                    labeledit = glsid('%s - edit' % req[0])
                    output.append(ssp + 'default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' % (req[2], prefix, req[0], labelbrowse, mytype, getoffset(idx,output), glsid(evt['text'])))
                    output.append(ssp + 'default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' % (req[2], prefix, req[0], labeledit, 'text', getoffset(idx,output), glsid(evt['text'])))
                else:
                    output.append(ssp + 'default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' % (req[2], prefix, req[0], glsid(req[0]), mytype, getoffset(idx, output), glsid(evt['text'])))
            output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (glsid('Hint - variables can be subbed (%%=%, _%=space, _%%=,): '), getoffset(idx, output), glsid(evt['text'])))
            try:
                vargs = evt['varArgs']
            except KeyError:
                vargs = {}
            vs = ''
            for key in vargs.keys():
                vs += '%s=%s,' % (key, vargs[key])
            vs = vs[:-1]
            brk = 60
            if len(vs) > 0:
                if len(vs) < brk:
                    found, strid =  podict.has_msgid(vs)
                    if found is False:
                        podict.addentry(strid, vs)
                        podirty = True
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), glsid(evt['text'])))
                else:
                    x = vs.rfind(',', 0, brk)
                    found, strid =  podict.has_msgid(vs[:x])
                    if found is False:
                        podict.addentry(strid, vs[:x])
                        podirty = True
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), glsid(evt['text'])))
                    found, strid =  podict.has_msgid(vs[x+1:])
                    if found is False:
                        podict.addentry(strid, vs[x+1:])
                        podirty = True
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), glsid(evt['text'])))
        output.append(ssp + 'default="" id="%s.userargs" label="%s" type="text" visible="!eq(%s,%s)" />\n' % (prefix, glsid('Var subbed arg string'), getoffset(idx, output), glsid('None')))
        output.append(ssp + 'default="" id="%s.test" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, %s)" visible="!eq(%s,%s)" />\n' % (prefix, glsid('Test Command (click OK to save changes first)'), prefix, getoffset(idx, output), glsid('None')))
        idx_prev = idx

    output.append('  </category>\n')
    output.append('  <category label="%s">\n' % glsid('General'))
    output.append('    <setting default="false" id="Notify" label="%s" type="bool" />\n' % glsid('Display Notifications when Tasks Run?'))
    output.append('    <setting default="500" id="LoopFreq" label="%s" type="number" />\n' % glsid('Loop Pooling Frequency (ms)'))
    output.append('    <setting default="500" id="LogFreq" label="%s" type="number" />\n' % glsid('Log Polling Frequency (ms)'))
    output.append('    <setting default="100" id="TaskFreq" label="%s" type="number" />\n' % glsid('Task Polling Frequency (ms)'))
    output.append('    <setting default="false" id="loglevel" label="%s" type="bool" />\n' % glsid('Show debugging info in normal log?'))
    output.append('    <setting id="logsettings" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, logsettings)" />\n' % glsid('Write Settings into Kodi log'))
    output.append('    <setting id="uploadlog" label="%s" type="action" action="RunScript(script.xbmc.debug.log)" visible="System.HasAddon(script.xbmc.debug.log)" />\n' % glsid('Upload Log'))
    output.append('    <setting id="regen" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, regen)" />\n' % glsid('Regenerate settings.xml'))
    output.append('    <setting id="test" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, test)" />\n' % glsid('Test addon native tasks (see log for output)'))
    output.append('  </category>\n')
    output.append('  <category label="%s">\n' % glsid('Update'))
    output.append('    <setting label="%s" type="lsep" />\n' % glsid('Before any installation, the current is backed up to userdata/addon_data'))
    output.append('    <setting default="nonrepo" id="installedbranch" label="%s" type="text" enable="false" />\n' % glsid('Currently installed branch'))
    output.append('    <setting default="nonrepo" id="repobranchname" label="%s" type="select" values="master" />\n' % glsid('Repository branch name for downloads'))
    output.append('    <setting default="false" id="autodownload" label="%s" type="bool" />\n' % glsid('Automatically download/install latest from GitHub on startup?'))
    output.append('    <setting default="false" id="silent_install" label="%s" type="bool" />\n' % glsid('Install without prompts?'))
    output.append('    <setting id="checkupdate" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, checkupdate)" />\n' % glsid('Check for update on GitHub'))
    output.append('    <setting id="updatefromzip" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, updatefromzip)" />\n' % glsid('Update from downloaded zip'))
    output.append('    <setting id="restorebackup" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, restorebackup)" />\n' % glsid('Restore from previous back up'))

    output.append('  </category>\n')
    output.append('</settings>')
    output = "".join(output)
    if fn is None:
        fn = os.path.join(xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('path').decode("utf-8"), 'resources', 'lib', 'tests')
    with codecs.open(fn, 'wb', 'UTF-8') as f:
        f.writelines(output)

    if podirty is True:
        podict.write_to_file(pofile)
    try:
        log(msg=glsid('Settings.xml rewritten'))
    except TypeError:
        pass

if __name__ == '__main__':
    generate_settingsxml(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\settings.xml')