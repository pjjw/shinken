#!/usr/bin/python
#Copyright (C) 2011 Durieux David, d.durieux@siprossii.com
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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information into the glpi database. for the moment
#only Mysql is supported. This code is __imported__ from Broker.
#The managed_brok function is called by Broker for manage the broks. It calls
#the manage_*_brok functions that create queries, and then run queries.


import copy
import time
import sys

properties = {
    'daemons' : ['broker'],
    'type' : 'glpidb',
    'phases' : ['running'],
    }

from shinken.basemodule import BaseModule
from shinken.log import logger

def de_unixify(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))



#Class for the Glpidb Broker
#Get broks and puts them in merlin database
class Glpidb_broker(BaseModule):
    def __init__(self, modconf, host=None, user=None, password=None, database=None, character_set=None, database_path=None):
#Mapping for name of data, rename attributes and transform function
        self.mapping = {
           #Host
           'host_check_result' : {
               'plugin_monitoring_hosts_id' : {'transform' : None},
               'event' : {'transform' : None},
               'perf_data' : {'transform' : None},
               }
           }
        # Last state of check
        self.checkstatus = {
           '0' : None,
           }
        BaseModule.__init__(self, modconf)
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.character_set = character_set
        self.database_path = database_path
        
        from shinken.db_mysql import DBMysql
        print "Creating a mysql backend"
        self.db_backend = DBMysql(host, user, password, database, character_set)



    #Called by Broker so we can do init stuff
    #TODO : add conf param to get pass with init
    #Conf from arbiter!
    def init(self):
        print "I connect to Glpi database"
        self.db_backend.connect_database()




    def preprocess(self, type, brok):
        new_brok = copy.deepcopy(brok)
        #Only preprocess if we can apply a mapping
        if type in self.mapping:
            if brok.data['host_name']:
               s = brok.data['host_name'].split('-')
               new_brok.data['plugin_monitoring_hosts_id'] = s[1]
               # If last check have same message, not add entry in DB
               lhc = brok.data['output'].split('-')
               if new_brok.data['plugin_monitoring_hosts_id'] in self.checkstatus:
                  if self.checkstatus[new_brok.data['plugin_monitoring_hosts_id']] == lhc[0]:
                     return brok
                  else:
                     self.checkstatus[new_brok.data['plugin_monitoring_hosts_id']] = lhc[0]
               else :
                  self.checkstatus[new_brok.data['plugin_monitoring_hosts_id']] = lhc[0]
               brok.data['plugin_monitoring_hosts_id'] = s[1]
               new_brok.data['event'] = brok.data['output']
               brok.data['event'] = brok.data['output']
            to_del = []
            to_add = []
            mapping = self.mapping[brok.type]
            for prop in new_brok.data:
            #ex : 'name' : 'program_start_time', 'transform'
                if prop in mapping:
                    #print "Got a prop to change", prop
                    val = brok.data[prop]
                    if mapping[prop]['transform'] is not None:
                        print "Call function for", type, prop
                        f = mapping[prop]['transform']
                        val = f(val)
                    name = prop
                    if 'name' in mapping[prop]:
                        name = mapping[prop]['name']
                    to_add.append((name, val))
                    to_del.append(prop)
                else:
                    to_del.append(prop)
            for prop in to_del:
                del new_brok.data[prop]
            for (name, val) in to_add:
                new_brok.data[name] = val
        else:
            print "No preprocess type", brok.type
            print brok.data
        return new_brok



    #Get a brok, parse it, and put in in database
    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        type = b.type
        manager = 'manage_'+type+'_brok'
        if hasattr(self, manager):
            new_b = self.preprocess(type, b)
            if 'host_name' in new_b.data:
               if 'plugin_monitoring_hosts_id' not in new_b.data:
                  return
            f = getattr(self, manager)
            queries = f(new_b)
            #Ok, we've got queries, now : run them!
            for q in queries :
                self.db_backend.execute_query(q)
            return


    #Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        logger.log("GLPI : data in DB %s " % b)
        b.data['date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        query = self.db_backend.create_insert_query('glpi_plugin_monitoring_hostevents', b.data)
        return [query]