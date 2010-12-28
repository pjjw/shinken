#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import time, calendar, re
try:
    from ClusterShell.NodeSet import NodeSet
except ImportError:
    NodeSet = None

from shinken.macroresolver import MacroResolver
#from memoized import memoized


################################### TIME ##################################
#@memoized
def get_end_of_day(year, month_id, day):
    end_time = (year, month_id, day, 23, 59, 59, 0, 0, -1)
    end_time_epoch = time.mktime(end_time)
    return end_time_epoch


#@memoized
def print_date(t):
    return time.asctime(time.localtime(t))


#@memoized
def get_day(t):
    return int(t - get_sec_from_morning(t))


#@memoized
def get_sec_from_morning(t):
    t_lt = time.localtime(t)
    h = t_lt.tm_hour
    m = t_lt.tm_min
    s = t_lt.tm_sec
    return h * 3600 + m * 60 + s


#@memoized
def get_start_of_day(year, month_id, day):
    start_time = (year, month_id, day, 00, 00, 00, 0, 0, -1)
    start_time_epoch = time.mktime(start_time)
    return start_time_epoch


#change a time in seconds like 3600 into a format : 0d 1h 0m 0s
def format_t_into_dhms_format(t):
    s = t
    m,s=divmod(s,60)
    h,m=divmod(m,60)
    d,h=divmod(h,24)
    return '%sd %sh %sm %ss' % (d, h, m, s)


################################# Pythonization ###########################
#first change to foat so manage for example 25.0 to 25
def to_int(val):
    return int(float(val))

def to_float(val):
    return float(val)

def to_char(val):
    return val[0]

def to_split(val):
    val = val.split(',')
    if val == ['']:
        val = []
    return val

#bool('0') = true, so...
def to_bool(val):
    if val == '1':
        return True
    else:
        return False

def from_bool_to_string(b):
    if b :
        return '1'
    else:
        return '0'

def from_bool_to_int(b):
    if b :
        return 1
    else:
        return 0

def from_list_to_split(val):
    val = ','.join(['%s' % v for v in val])
    return val

def from_float_to_int(val):
    val = int(val)
    return val


### Functions for brok_transformations
### They take 2 parameters : ref, and a value
### ref is the item like a service, and value
### if the value to preprocess

# Just a string list of all names, with ,
def to_list_string_of_names(ref, tab):
    return ",".join([e.get_name() for e in tab])

# take a list of hosts and return a list
# of all host_names
def to_hostnames_list(ref, tab):
    r = []
    for h in tab:
        if hasattr(h, 'host_name'):
            r.append(h.host_name)
    return r

# Will create a dict with 2 lists:
# *services : all services of the tab
# *hosts : all hosts of the tab
def to_svc_hst_distinct_lists(ref, tab):
    r = {'hosts' : [], 'services' : []}
    for e in tab:
        cls = e.__class__
        if cls.my_type == 'service':
            name = e.get_dbg_name()
            r['services'].append(name)
        else:
            name = e.get_dbg_name()
            r['hosts'].append(name)
    return r


# Will expaand the value with macros from the
# host/service ref before brok it
def expand_with_macros(ref, value):
    return MacroResolver().resolve_simple_macros_in_string(value, ref.get_data_for_checks())


# Just get the string name of the object
# (like for realm)
def get_obj_name(obj):
    return obj.get_name()

# return the list of keys of the custom dict
# but without the _ before
def get_customs_keys(d):
    return [k[1:] for k in sorted(d.keys())]

# return the values of the dict
def get_customs_values(d):
    return [d[key] for key in sorted(d.keys())]


###################### Sorting ################
def scheduler_no_spare_first(x, y):
    if x.spare and not y.spare:
        return 1
    elif x.spare and y.spare:
        return 0
    else:
        return -1


#-1 is x first, 0 equal, 1 is y first
def alive_then_spare_then_deads(x, y):
    #First are alive
    if x.alive and not y.alive:
        return -1
    if y.alive and not x.alive:
        return 0
    #if not alive both, I really don't care...
    if not x.alive and not y.alive:
        return -1
    #Ok, both are alive... now spare after no spare
    if not x.spare:
        return -1
    #x is a spare, so y must be before, even if
    #y is a spare
    if not y.spare:
        return 1
    return 0

#-1 is x first, 0 equal, 1 is y first
def sort_by_ids(x, y):
    if x.id < y.id:
        return -1
    if x.id > y.id:
        return 1
    #So is equal
    return 0
    


##################### Cleaning ##############
def strip_and_uniq(tab):
    new_tab = set()
    for elt in tab:
        new_tab.add(elt.strip())
    return list(new_tab)



#################### Patern change application (mainly for host) #######

def expand_xy_patern(pattern):
    ns = NodeSet(pattern)
    if len(ns) > 1:
        for elem in ns:
            for a in expand_xy_patern(elem):
                yield a
    else:
        yield pattern




#This function is used to generate all patern change as
#recursive list.
#for example, for a [(1,3),(1,4),(1,5)] xy_couples,
#it will generate a 60 item list with:
#Rule: [1, '[1-5]', [1, '[1-4]', [1, '[1-3]', []]]]
#Rule: [1, '[1-5]', [1, '[1-4]', [2, '[1-3]', []]]]
#...
def got_generation_rule_patern_change(xy_couples):
    res = []
    xy_cpl = xy_couples
    if xy_couples == []:
        return []
    (x, y) = xy_cpl[0]
    for i in xrange(x, y+1):
        n = got_generation_rule_patern_change(xy_cpl[1:])
        if n != []:
            for e in n:
                res.append( [i, '[%d-%d]'%(x,y), e])
        else:
            res.append( [i, '[%d-%d]'%(x,y), []])
    return res
    

#this fuction apply a recursive patern change
#generate by the got_generation_rule_patern_change
#function.
#It take one entry of this list, and apply
#recursivly the change to s like :
#s = "Unit [1-3] Port [1-4] Admin [1-5]"
#rule = [1, '[1-5]', [2, '[1-4]', [3, '[1-3]', []]]]
#output = Unit 3 Port 2 Admin 1
def apply_change_recursive_patern_change(s, rule):
    #print "Try to change %s" % s, 'with', rule
    new_s = s
    (i, m, t) = rule
    #print "replace %s by %s" % (r'%s' % m, str(i)), 'in', s
    s = s.replace(r'%s' % m, str(i))
    #print "And got", s
    if t == []:
        return s
    return apply_change_recursive_patern_change(s, t)


#For service generator, get dict from a _custom properties
#as _disks   C$(80%!90%),D$(80%!90%)$,E$(80%!90%)$
#return {'C' : '80%!90%', 'D' : '80%!90%', 'E' : '80%!90%'}
#And if we have a key that look like [X-Y] we will expand it
#into Y-X+1 keys
GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR = 0
GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX = 1
GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT = 2
GET_KEY_VALUE_SEQUENCE_ERROR_NODE= 3
def get_key_value_sequence(entry, default_value=None):
    array1 = []
    array2 = []
    conf_entry = entry

    # match a key$(value1..n)$
    keyval_pattern_txt = r"""
\s*(?P<key>[^,]+?)(?P<values>(\$\(.*?\)\$)*)(?:[,]|$)
"""
    keyval_pattern = re.compile('(?x)' + keyval_pattern_txt)
    # match a whole sequence of key$(value1..n)$
    all_keyval_pattern = re.compile('(?x)^(' + keyval_pattern_txt + ')+$')
    # match a single value
    value_pattern = re.compile('(?:\$\((?P<val>.*?)\)\$)')
    # match a sequence of values
    all_value_pattern = re.compile('^(?:\$\(.*?\)\$)+$')

    if all_keyval_pattern.match(conf_entry):
        for mat in re.finditer(keyval_pattern, conf_entry):
            r = { 'KEY' : mat.group('key') }
            # The key is in mat.group('key')
            # If there are also value(s)...
            if mat.group('values'):
                if all_value_pattern.match(mat.group('values')):
                    # If there are multiple values, loop over them
                    valnum = 1
                    for val in re.finditer(value_pattern, mat.group('values')):
                        r['VALUE' + str(valnum)] = val.group('val')
                        valnum += 1
                else:
                    # Value syntax error
                    return (None, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX)
            else:
                r['VALUE1'] = None
            array1.append(r)
    else:
        # Something is wrong with the values. (Maybe unbalanced '$(')
        # TODO: count opening and closing brackets in the pattern
        return (None, GET_KEY_VALUE_SEQUENCE_ERROR_SYNTAX)

    # now fill the empty values with the default value
    for r in array1:
        if r['VALUE1'] == None:
            if default_value == None:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODEFAULT)
            else:
                r['VALUE1'] = default_value
        r['VALUE'] = r['VALUE1']

    #Now create new one but for [X-Y] matchs
    # array1 holds the original entries. Some of the keys may contain wildcards
    # array2 is filled with originals and inflated wildcards
    #import time
    #t0 = time.time()
    #NodeSet = None
    if NodeSet == None:
        #The patern that will say if we have a [X-Y] key.
        pat = re.compile('\[(\d*)-(\d*)\]')

    for r in array1:

        key = r['KEY']
        orig_key = r['KEY']

        #We have no choice, we cannot use NodeSet, so we use the
        #simple regexp
        if NodeSet == None:
            m = pat.search(key)
            got_xy = (m != None)
        else: # Try to look with a nodeset check directly
            try:
                ns = NodeSet(key)
                #If we have more than 1 element, we have a xy thing
                got_xy = (len(ns) != 1)
            except NodeSetParseRangeError:
                return (None, GET_KEY_VALUE_SEQUENCE_ERROR_NODE)
                pass # go in the next key

        #Now we've got our couples of X-Y. If no void,
        #we were with a "key generator"

        if got_xy:
            #Ok 2 cases : we have the NodeSet lib or not.
            #if not, we use the dumb algo (quick, but manage less
            #cases like /N or , in paterns)
            if NodeSet == None: #us the old algo
                still_loop = True
                xy_couples = [] # will get all X-Y couples
                while still_loop:
                    m = pat.search(key)
                    if m != None: # we've find one X-Y
                        (x,y) = m.groups()
                        (x,y) = (int(x), int(y))
                        xy_couples.append((x,y))
                        #We must search if we've gotother X-Y, so
                        #we delete this one, and loop
                        key = key.replace('[%d-%d]' % (x,y), 'Z'*10)
                    else:#no more X-Y in it
                        still_loop = False

                #Now we have our xy_couples, we can manage them

                #We search all patern change rules
                rules = got_generation_rule_patern_change(xy_couples)

                #Then we apply them all to get ours final keys
                for rule in rules:
                    res = apply_change_recursive_patern_change(orig_key, rule)
                    new_r = {}
                    for key in r:
                        new_r[key] = r[key]
                    new_r['KEY'] = res
                    array2.append(new_r)

            else:
                #The key was just a generator, we can remove it
                #keys_to_del.append(orig_key)

                #We search all patern change rules
                #rules = got_generation_rule_patern_change(xy_couples)
                nodes_set = expand_xy_patern(orig_key)
                new_keys = list(nodes_set)

                #Then we apply them all to get ours final keys
                for new_key in new_keys:
                #res = apply_change_recursive_patern_change(orig_key, rule)
                    new_r = {}
                    for key in r:
                        new_r[key] = r[key]
                    new_r['KEY'] = new_key
                    array2.append(new_r)
        else:
            # There were no wildcards
            array2.append(r)


    #t1 = time.time()
    #print "***********Diff", t1 -t0

    return (array2, GET_KEY_VALUE_SEQUENCE_ERROR_NOERROR)


