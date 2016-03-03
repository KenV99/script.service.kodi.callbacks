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
import resources.lib.kodisettings.struct as struct

def testStruct():
    settings = struct.Settings()
    settings.addCategory(struct.Category(u'General'))
    control = struct.Text(u'T1', u'Task 1')
    settings.addControl(u'General', control)
    conditional = struct.Conditional(struct.Conditional.OP_EQUAL, u'x', u'T1')
    control = struct.Text(u'T2', u'Task 2', visible=struct.Conditionals(conditional))
    settings.addControl(u'General', control)
    output = settings.render()
    print output
    pass
    pass

