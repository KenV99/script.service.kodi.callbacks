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
from resources.lib.utils.poutil import KodiPo, PoDict
kodipo = KodiPo()
kodipo.updateAlways = True
_ = kodipo.getLocalizedStringId
kl = KodiLogger()
log = kl.log
podict = PoDict()
pofile = os.path.join(xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('path'), 'resources', 'language', 'English', 'strings.po')
if pofile.startswith('resources'):
    pofile = r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\language\English\strings.po'
podict.read_from_file(pofile)


def generate_settingsxml(fn=None):
    podirty = False
    allevts = Events().AllEvents
    output = []
    ssp = '    <setting '
    evts = ['None']
    for evtkey in allevts.keys():
        evts.append(allevts[evtkey]['text'])
    evts.sort()
    evts = "|".join(evts)

    def getoffset(idx, lst):
        return str(idx-len(lst))

    output.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    output.append('<settings>\n')
    output.append('  <category label="%s">\n' % _('Tasks'))

    startnum = int(kodipo.getLocalizedStringId('Task 1')) - 1
    tasks = []
    for i in xrange(1,11):
        prefix = "T%s" % str(i)
        output.append('    <setting label="%s" type="lsep"/>\n'% str(startnum + i))
        tasks.append(str(startnum + i))
        idx = len(output)
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
        output.append('    <setting default="none" id="%s.type" label="%s" type="labelenum" lvalues="%s" />\n' % (prefix, _('Task'), ltaskchoices))
        output.append('    <setting default="-1" id="%s.maxrunning" label="%s" type="number" visible="!eq(-1,0)" />\n' % (prefix, _('Max num of this task running simultaneously (-1=no limit)')))
        output.append('    <setting default="-1" id="%s.maxruns" label="%s" type="number" visible="!eq(-2,0)" />\n' % (prefix, _('Max num of times this task runs (-1=no limit)')))
        output.append('    <setting default="-1" id="%s.refractory" label="%s" type="number" visible="!eq(-3,0)" />\n' % (prefix, _('Refractory period in secs (-1=none)')))
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
                    output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                  (varset['default'], prefix, var['id'], varset['label'], mytype, getoffset(idx,output), i1+1))
                else:
                    output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" option="%s" visible="eq(%s,%s)" />\n' %
                                  (varset['default'], prefix, var['id'], varset['label'], mytype, option, getoffset(idx,output), i1+1))
                if varset['type'] == 'sfile':
                    output.append('    <setting default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' %
                                  (varset['default'], prefix, var['id'], varset['label'], 'text', getoffset(idx,output), i1+1))

    output.append('  </category>\n\n')
    output.append('  <category label="%s">\n' % _('Events'))
    tasks = '|'.join(tasks)

    startnum = int(kodipo.getLocalizedStringId('Event 1')) - 1
    for i in xrange(1,11):
        prefix = 'E%s' % str(i)
        output.append(ssp + 'label="%s" type="lsep" />\n' % str(startnum + i))
        idx = len(output)
        output.append(ssp + 'default="None" id="%s.type" label="%s" type="select" values="%s" />\n' % (prefix, _('Type'), evts))
        output.append(ssp + 'default="Task 1" id="%s.task" label="%s" type="labelenum" visible="!eq(%s,None)" lvalues="%s" />\n' %(prefix, _('Task'), getoffset(idx,output),tasks))
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
                output.append(ssp + 'default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' % (req[2], prefix, req[0], kodipo.getLocalizedStringId(req[0]), mytype, getoffset(idx,output), evt['text'] ))
                if r1 == 'sfolder':
                    output.append(ssp + 'default="%s" id="%s.%s" label="%s" type="%s" visible="eq(%s,%s)" />\n' % (req[2], prefix, req[0], kodipo.getLocalizedStringId(req[0]), 'text', getoffset(idx,output), evt['text'] ))
            output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (_('Hint - variables can be subbed (%%=%, _%=space, _%%=,): '), getoffset(idx,output), evt['text']))
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
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), evt['text']))
                else:
                    x = vs.rfind(',', 0, brk)
                    found, strid =  podict.has_msgid(vs[:x])
                    if found is False:
                        podict.addentry(strid, vs[:x])
                        podirty = True
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), evt['text']))
                    found, strid =  podict.has_msgid(vs[x+1:])
                    if found is False:
                        podict.addentry(strid, vs[x+1:])
                        podirty = True
                    output.append(ssp + 'label="%s" type="lsep" visible="eq(%s,%s)" />\n' % (strid, getoffset(idx,output), evt['text']))
        output.append(ssp + 'default="" id="%s.userargs" label="%s" type="text" visible="!eq(%s,None)" />\n' % (prefix, _('Var subbed arg string'), getoffset(idx, output)))
        output.append(ssp + 'default="" id="%s.test" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, %s)" visible="!eq(%s,0)" />\n' % (prefix, _('Test Command (click OK to save changes first)'), prefix,getoffset(idx, output)))

    output.append('  </category>\n')
    output.append('  <category label="%s">\n' % _('General'))
    output.append('    <setting default="false" id="Notify" label="%s" type="bool" />\n' % _('Display Notifications when Tasks Run?'))
    output.append('    <setting default="500" id="LoopFreq" label="%s" type="number" />\n'% _('Loop Pooling Frequency (ms)'))
    output.append('    <setting default="500" id="LogFreq" label="%s" type="number" />\n' % _('Log Polling Frequency (ms)'))
    output.append('    <setting default="100" id="TaskFreq" label="%s" type="number" />\n' % _('Task Polling Frequency (ms)'))
    output.append('    <setting default="false" id="loglevel" label="%s" type="bool" />\n' % _('Show debugging info in normal log?'))
    output.append('    <setting id="regen" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, regen)" />\n' % _('Regenerate settings.xml'))
    output.append('    <setting id="test" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, test)" />\n' % _('Test addon native tasks (see log for output)'))
    output.append('  </category>\n')
    output.append('  <category label="%s">\n' % _('Update'))
    output.append('    <setting id="updatefromzip" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, updatefromzip)" />\n' % _('Update from downloaded zip'))
    output.append('    <setting id="restorebackup" label="%s" type="action" action="RunScript(script.service.kodi.callbacks, restorebackup)" />\n' % _('Restore from previous back up'))
    output.append('  </category>\n')
    output.append('</settings>')
    output = "".join(output)
    if fn is None:
        fn = os.path.join(xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('path'), 'resources', 'lib', 'tests')
    with open(fn, mode='w') as f:
        f.writelines(output)

    if podirty is True:
        podict.write_to_file(pofile)
    log(_('Settings.xml rewritten'))

if __name__ == '__main__':
    generate_settingsxml(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\settings.xml')