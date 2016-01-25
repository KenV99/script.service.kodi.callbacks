#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 KenV99
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

import sys
import traceback
import requests as requests
import urllib2
import httplib
from urlparse import urlparse
import socket
from resources.lib.taskABC import AbstractTask, KodiLogger, notify, events
from resources.lib.utils.poutil import KodiPo
kodipo = KodiPo()
_ = kodipo.getLocalizedString
__ = kodipo.getLocalizedStringId

class TaskHttp(AbstractTask):
    tasktype = 'http'
    variables = [
        {
            'id':'http',
            'settings':{
                'default':'',
                'label':__('HTTP string (without parameters)'),
                'type':'text'
            }
        },
        {
            'id':'user',
            'settings':{
                'default':'',
                'label':__('user for Basic Auth (optional)'),
                'type':'text'
            }
        },
        {
            'id':'pass',
            'settings':{
                'default':'',
                'label':__('password for Basic Auth (optional)'),
                'type':'text',
                'option':'hidden'
            }
        }
    ]

    def __init__(self):
        super(TaskHttp, self).__init__()
        self.runtimeargs = ''

    @staticmethod
    def validate(taskKwargs, xlog=KodiLogger.log):
        o = urlparse(taskKwargs['http'])
        if o.scheme != '' and o.netloc != '':
            return True
        else:
            xlog(msg=_('Invalid url: %s') % taskKwargs['http'])
            return False

    def processUserargs(self, kwargs):
        if self.userargs == '':
            return []
        ret = self.userargs
        ret = ret.replace(r'%%', '{@literal%@}')
        try:
            varArgs = events.Player[self.topic.topic]['varArgs']
        except:
            pass
        else:
            for key in varArgs.keys():
                try:
                    kw = kwargs[varArgs[key]]
                    kw = kw.replace(" ", '%__')
                    ret = ret.replace(key, kw)
                except:
                    pass
        ret = ret.replace('%__', " ")
        ret = ret.replace('{@literal%@}', r'%')
        return ret

    def run(self):
        if self.taskKwargs['notify'] is True:
            notify(_('Task %s launching for event: %s') % (self.taskId, str(self.topic)))
        err = False
        msg = ''
        try:
            if self.taskKwargs['user'] != '' and self.taskKwargs['pass'] != '':
                u = requests.get(self.taskKwargs['http']+self.runtimeargs, auth=(self.taskKwargs['user'], self.taskKwargs['pass']), timeout=20)
            else:
                u = requests.get(self.taskKwargs['http']+self.runtimeargs, timeout=20)
            try:
                result = u.text
            except Exception as e:
                err = True
                result = ''
                msg = _('Error on url read')
                if hasattr(e, 'message'):
                    msg = msg + '\n' + (str(e.message))
            msg = str(result)
        except requests.ConnectionError:
            err = True
            msg = _('Requests Connection Error')
        except requests.HTTPError:
            err = True
            msg = _('Requests HTTPError')
        except requests.URLRequired:
            err = True
            msg = _('Requests URLRequired Error')
        except requests.Timeout:
            err = True
            msg = _('Requests Timeout Error')
        except requests.RequestException:
            err = True
            msg = _('Generic Requests Error')
        except urllib2.HTTPError, e:
            err = True
            msg = _('HTTPError = ') + str(e.code)
        except urllib2.URLError, e:
            err = True
            msg = _('URLError\n') + e.reason
        except httplib.BadStatusLine, e:
            err = False
            self.log(msg=_('Http Bad Status Line caught and passed'))

        except httplib.HTTPException, e:
            err = True
            msg = _('HTTPException')
            if hasattr(e, 'message'):
                msg = msg + '\n' + e.message
        except socket.timeout, e:
            err = True
            msg = _('The request timed out, host unreachable')
        except Exception:
            err = True
            e = sys.exc_info()[0]
            if hasattr(e, 'message'):
                msg = str(e.message)
            msg = msg + '\n' + traceback.format_exc()
        else:
            msg = str(result)
        self.threadReturn(err, msg)
