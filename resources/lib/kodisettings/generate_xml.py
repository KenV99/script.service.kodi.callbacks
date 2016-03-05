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
from resources.lib.events import Events
from resources.lib  import taskdict
from resources.lib.kodisettings import struct
from resources.lib.kodilogging import KodiLogger
import xbmcaddon
import os
import codecs
from resources.lib.utils.poutil import KodiPo, PoDict
kodipo = KodiPo()
kodipo.updateAlways = False
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

    taskcontrols, tasks = createTasks()
    eventcontrols, podirty = createEvents(tasks)
    generalcontrols = createGeneral()
    updatecontrols = createUpdate()
    settings = struct.Settings()
    mysettings = [('Tasks', taskcontrols), ('Events', eventcontrols), ('General',generalcontrols), ('Update',updatecontrols)]
    for category, controls in mysettings:
        settings.addCategory(struct.Category(category))
        for control in controls:
            settings.addControl(category, control)

    output = settings.render()
    writetofile(fn, output)
    if podirty is True:
        podict.write_to_file(pofile)


def createTasks():
    taskchoices = ['none']
    for key in sorted(taskdict.keys()):
        taskchoices.append(key)
    tasks = []
    last_id = None
    taskcontrols = []
    for i in xrange(1, 11):
        tasks.append('Task %i' % i)
        prefix = "T%s" % str(i)
        curTaskType = '%s.type' % prefix
        if i == 1:

            taskcontrols.append(struct.Lsep('%s.div' % prefix, 'Task %i' % i))
            taskcontrols.append(struct.LabelEnum('%s.type' % prefix, 'Task', default='none', lvalues=taskchoices))
        else:
            conditional = struct.Conditional(struct.Conditional.OP_NOT_EQUAL, 'none', last_id)
            taskcontrols.append(struct.Lsep('%s.div' % prefix, 'Task %i' % i, visible=conditional))
            taskcontrols.append(struct.LabelEnum('%s.type' % prefix, 'Task', default='none', lvalues=taskchoices, visible=conditional))
        conditional = struct.Conditional(struct.Conditional.OP_NOT_EQUAL, 'none', curTaskType)
        taskcontrols.append(struct.Number('%s.maxrunning' % prefix, 'Max num of this task running simultaneously (-1=no limit)', default=-1, visible=conditional))
        taskcontrols.append(struct.Number('%s.maxruns' % prefix, 'Max num of times this task runs (-1=no limit)', default=-1, visible=conditional))
        taskcontrols.append(struct.Number('%s.refractory' % prefix, 'Refractory period in secs (-1=none)', default=-1, visible=conditional))

        for key in sorted(taskdict.keys()):
            for var in taskdict[key]['variables']:
                varset = var['settings']
                if varset['type'] == 'sfile':
                    mytype = 'browser'
                elif varset['type'] == 'file':
                    mytype = 'browser'
                else:
                    mytype = varset['type']
                try:
                    option = varset['option']
                except KeyError:
                    conditionals = struct.Conditional(struct.Conditional.OP_EQUAL, unicode(key), curTaskType)
                    if varset['type'] == 'sfile':
                        labelbrowse = u'%s - browse' % varset['label']
                        labeledit = u'%s - edit' % varset['label']
                        taskcontrols.append(struct.FileBrowser(u'%s.%s' % (prefix, var['id']), labelbrowse, default=varset['default'], fbtype=struct.FileBrowser.TYPE_FILE, visible=conditionals))
                        taskcontrols.append(struct.Text(u'%s.%s' % (prefix, var['id']), labeledit, default=varset['default'] , visible=conditionals))
                    else:
                        Control = struct.getControlClass[mytype]
                        taskcontrols.append(Control('%s.%s' % (prefix, var['id']), varset['label'], default=varset['default'], visible = conditionals))
                else:
                    conditionals = struct.Conditional(struct.Conditional.OP_EQUAL, unicode(key), curTaskType)
                    if varset['type'] == 'sfile':
                        labelbrowse = '%s - browse' % varset['label']
                        labeledit = '%s - edit' % varset['label']
                        taskcontrols.append(struct.FileBrowser('%s.%s' % (prefix, var['id']), labelbrowse, default=varset['default'], option=option, fbtype=struct.FileBrowser.TYPE_FILE, visible=conditionals))
                        taskcontrols.append(struct.Text('%s.%s' % (prefix, var['id']), labeledit, default=varset['default'] , visible=conditionals))
                    else:
                        Control = struct.getControlClass[mytype]
                        taskcontrols.append(Control('%s.%s' % (prefix, var['id']), varset['label'], default=varset['default'], option=option, visible = conditionals))
        last_id = curTaskType
    return taskcontrols, tasks

def createEvents(tasks):
    podirty = False
    allevts = Events().AllEvents
    evts = []
    for evtkey in allevts.keys():
        evts.append(allevts[evtkey]['text'])
    evts.sort()
    evts.insert(0, 'None')
    levts = []
    for evt in evts:
        levts.append(glsid(evt))
    levts = "|".join(levts)
    eventcontrols = []
    # Hidden copies of the Task types to reference below for only allowing to choose tasks that have been configured
    for i in xrange(1,11):
        eventcontrols.append(struct.Text('T%s.type' % str(i), '', visible=False, default='0', internal_ref='Tx%s.type' % str(i)))

    last_id = None
    for i in xrange(1,11):
        prefix = 'E%s' % str(i)
        curTaskType = '%s.type' % prefix
        action = 'RunScript(script.service.kodi.callbacks, lselector, id=%s.type, heading=%s, lvalues=%s)' % (prefix, glsid('Choose event type'), levts)
        if i == 1:
            eventcontrols.append(struct.Lsep('%s.lsep' % prefix, 'Event %i' % i))
            eventcontrols.append(struct.Action('%s.action' % prefix, 'Choose event type (click here)', action=action))
            eventcontrols.append(struct.Select('%s.type-v' % prefix, 'Event:', default='None', enable=False, lvalues=evts))
        else:
            conditionals = struct.Conditional(struct.Conditional.OP_NOT_EQUAL, glsid('None'), last_id)
            eventcontrols.append(struct.Lsep('%s.lsep' % prefix, 'Event %i' % i, visible=conditionals))
            eventcontrols.append(struct.Action('%s.action' % prefix, 'Choose event type', action=action, visible=conditionals))
            eventcontrols.append(struct.Select('%s.type-v' % prefix, 'Event:', default=glsid('None'), enable=False, lvalues=evts, visible=conditionals))
        conditionals = struct.Conditional(struct.Conditional.OP_NOT_EQUAL, glsid('None'), curTaskType)
        eventcontrols.append(struct.Text(curTaskType, '', default=glsid('None'), visible=False))

        # Conditionally show only the number of tasks configured
        conditional =  struct.Conditionals([struct.Conditional(struct.Conditional.OP_EQUAL, 'none', 'Tx1.type'), conditionals])
        eventcontrols.append(struct.LabelEnum('%s.task' % prefix, 'Task', default='Task 1', lvalues=['none'], enable=False, visible=conditional))
        for i1 in xrange(2, 11):
            conditional1 =  struct.Conditional(struct.Conditional.OP_NOT_EQUAL, 'none', 'Tx%s.type' % str(i1-1))
            conditional2 =  struct.Conditional(struct.Conditional.OP_EQUAL, 'none', 'Tx%s.type' % str(i1))
            conditional = struct.Conditionals([conditional1, conditional2, conditionals])
            eventcontrols.append(struct.LabelEnum('%s.task' % prefix, 'Task', default='Task 1', lvalues=tasks[:i1-1], visible=conditional))
        conditional =  struct.Conditionals([struct.Conditional(struct.Conditional.OP_NOT_EQUAL, 'none', 'Tx10.type'), conditionals])
        eventcontrols.append(struct.LabelEnum('%s.task' % prefix, 'Task', default='Task 1', lvalues=tasks, visible=conditional))

        for evtkey in allevts.keys():
            evt = allevts[evtkey]
            conditionals = struct.Conditional(struct.Conditional.OP_EQUAL, glsid(evt['text']), curTaskType)
            for req in evt['reqInfo']:
                r1 = req[1]
                if r1 in ['float', 'int']:
                    r1 = 'number'
                if r1 == 'sfolder':
                    mytype = 'browse'
                else:
                    mytype = r1

                if r1 == 'sfolder':
                    labelbrowse = '%s - browse' % req[0]
                    labeledit = '%s - edit' % req[0]
                    eventcontrols.append(struct.FileBrowser('%s.%s' %(prefix, req[0]), labelbrowse, struct.FileBrowser.TYPE_FOLDER, default=req[2], visible=conditionals))
                    eventcontrols.append(struct.Text('%s.%s' % (prefix, req[0]), labeledit, default=req[2], visible=conditionals))
                else:
                    Control = struct.getControlClass[mytype]
                    eventcontrols.append(Control(sid='%s.%s' % (prefix, req[0]), label=req[0], default=req[2], visible=conditionals))
            eventcontrols.append(struct.Lsep(label='Hint - variables can be subbed (%%=%, _%=space, __%=,):', visible=conditionals))
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
                    eventcontrols.append(struct.Lsep(label=vs, visible=conditionals))
                else:
                    x = vs.rfind(',', 0, brk)
                    found, strid =  podict.has_msgid(vs[:x])
                    if found is False:
                        podict.addentry(strid, vs[:x])
                        podirty = True
                    eventcontrols.append(struct.Lsep(label=vs[:x], visible=conditionals))
                    found, strid =  podict.has_msgid(vs[x+1:])
                    if found is False:
                        podict.addentry(strid, vs[x+1:])
                        podirty = True
                    eventcontrols.append(struct.Lsep(label=vs[x+1:], visible=conditionals))
        conditionals = struct.Conditional(struct.Conditional.OP_NOT_EQUAL, unicode(glsid('None')), curTaskType)
        eventcontrols.append(struct.Text('%s.userargs' % prefix, 'Var subbed arg string', default='', visible=conditionals))
        eventcontrols.append(struct.Action('%s.test' % prefix, 'Test Command (click OK to save changes first)', action='RunScript(script.service.kodi.callbacks, %s)' % prefix, visible=conditionals))
        last_id = curTaskType
    return eventcontrols, podirty

def createGeneral():
    generalcontrols = []
    generalcontrols.append(struct.Bool('Notify', 'Display Notifications when Tasks Run?', default=False))
    generalcontrols.append(struct.Number('LoopFreq', 'Loop Pooling Frequency (ms)', default=500))
    generalcontrols.append(struct.Number('LogFreq', 'Log Polling Frequency (ms)', default=500))
    generalcontrols.append(struct.Number('TaskFreq', 'Task Polling Frequency (ms)', default=100))
    generalcontrols.append(struct.Bool('loglevel', 'Show debugging info in normal log?', default=False))
    generalcontrols.append(struct.Action('logsettings', 'Write Settings into Kodi log', action='RunScript(script.service.kodi.callbacks, logsettings)'))
    generalcontrols.append(struct.Action('uploadlog', 'Upload Log', action='RunScript(script.xbmc.debug.log)',
                                     visible=struct.Conditionals(struct.Conditional(struct.Conditional.OP_HAS_ADDON, 'script.xbmc.debug.log'))))
    generalcontrols.append(struct.Action('regen', 'Regenerate settings.xml', action='RunScript(script.service.kodi.callbacks, regen)'))
    generalcontrols.append(struct.Action('test', 'Test addon native tasks (see log for output)', action='RunScript(script.service.kodi.callbacks, test)'))
    return generalcontrols

def createUpdate():
    updatecontrols = []
    updatecontrols.append(struct.Lsep(label='Before any installation, the current is backed up to userdata/addon_data'))
    updatecontrols.append(struct.Text('installed branch', 'Currently installed branch', default='nonrepo', enable=False))
    updatecontrols.append(struct.Select('repobranchname','Repository branch name for downloads', default='nonrepo', values=['master', 'nonrepo']))
    updatecontrols.append( struct.Bool('autodownload', 'Automatically download/install latest from GitHub on startup?', default=False))
    updatecontrols.append(struct.Bool('silent_install', 'Install without prompts?', default=False))
    updatecontrols.append(struct.Action('checkupdate', 'Check for update on GitHub', action='RunScript(script.service.kodi.callbacks, checkupdate)'))
    updatecontrols.append(struct.Action('updatefromzip', 'Update from downloaded zip', action='RunScript(script.service.kodi.callbacks, updatefromzip)'))
    updatecontrols.append(struct.Action('restorebackup', 'Restore from previous back up', action='RunScript(script.service.kodi.callbacks, restorebackup)'))
    return updatecontrols

def writetofile(fn, output):
    if fn is None:
        fn = os.path.join(xbmcaddon.Addon('script.service.kodi.callbacks').getAddonInfo('path').decode("utf-8"), 'resources', 'settings.xml')
    with codecs.open(fn, 'wb', 'UTF-8') as f:
        f.writelines(output)
    try:
        log(msg=glsid('Settings.xml rewritten'))
    except TypeError:
        pass

if __name__ == '__main__':
    generate_settingsxml(r'C:\Users\Ken User\AppData\Roaming\Kodi\addons\script.service.kodi.callbacks\resources\settings.xml')
