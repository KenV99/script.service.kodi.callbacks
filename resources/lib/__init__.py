#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
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
import pkgutil
from resources.lib.taskABC import AbstractTask
import tasks

package = tasks
prefix = package.__name__ + "."
taskdict = {}
tasktypes = []
for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
    module = __import__(modname, fromlist="dummy")
    for name, cls in module.__dict__.items():
        try:
            if issubclass(cls, AbstractTask):
                if cls.tasktype != 'abstract':
                    if cls.tasktype not in tasktypes:
                        try:
                            taskdict[cls.tasktype] = {'class':cls, 'variables':cls.variables}
                            tasktypes.append(cls.tasktype)
                        except:
                            raise Exception('Error loading class for %s' % cls.tasktype)
        except TypeError:
            pass
