#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


from itemgroup import Itemgroup, Itemgroups
from brok import Brok


class Hostgroup(Itemgroup):
    id = 1 #0 is always a little bit special... like in database
    my_type = 'hostgroup'

    properties={'id': {'required': False, 'default': 0, 'status_broker_name' : None},
                'hostgroup_name': {'required': True, 'status_broker_name' : None},
                'alias': {'required':  True, 'status_broker_name' : None},
                'notes': {'required': False, 'default':'', 'status_broker_name' : None},
                'notes_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'action_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'members' : {'required': True}#No status_broker_name because it put hosts, not host_name
                }

    macros = {
        'HOSTGROUPALIAS' : 'alias',
        'HOSTGROUPMEMBERS' : 'members',
        'HOSTGROUPNOTES' : 'notes',
        'HOSTGROUPNOTESURL' : 'notes_url',
        'HOSTGROUPACTIONURL' : 'action_url'
        }


    def get_name(self):
        return self.hostgroup_name


    def get_hosts(self):
        return self.members


    def get_hostgroup_members(self):
        if self.has('hostgroup_members'):
            return self.hostgroup_members.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    #Because hostgroup we call may not have it's members
    #we call get_hosts_by_explosion on it
    def get_hosts_by_explosion(self, hostgroups):
        #First we tag the hg so it will not be explode
        #if a son of it already call it
        self.already_explode = True
        
        #Now the recursiv part
        #rec_tag is set to False avery HG we explode
        #so if True here, it must be a loop in HG
        #calls... not GOOD!
        if self.rec_tag:
            print "Error : we've got a loop in hostgroup definition", self.get_name()
            if self.has('members'):
                return self.members
            else:
                return ''
        #Ok, not a loop, we tag it and continue
        self.rec_tag = True

        hg_mbrs = self.get_hostgroup_members()
        for hg_mbr in hg_mbrs:
            hg = hostgroups.find_by_name(hg_mbr.strip())
            if hg is not None:
                value = hg.get_hosts_by_explosion(hostgroups)
                if value is not None:
                    self.add_string_member(value)

        if self.has('members'):
            return self.members
        else:
            return ''



class Hostgroups(Itemgroups):
    name_property = "hostgroup_name" # is used for finding hostgroups
    inner_class = Hostgroup

    def get_members_by_name(self, hgname):
        id = self.find_id_by_name(hgname)
        if id == None:
            return []
        return self.itemgroups[id].get_hosts()


    def linkify(self, hosts=None):
        self.linkify_hg_by_hst(hosts)

    
    #We just search for each hostgroup the id of the hosts 
    #and replace the name by the id
    def linkify_hg_by_hst(self, hosts):
        for hg in self.itemgroups.values():
            mbrs = hg.get_hosts()
            #The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                new_mbrs.append(hosts.find_by_name(mbr))
            #We find the id, we remplace the names
            hg.replace_members(new_mbrs)


    #Add a host string to a hostgroup member
    #if the host group do not exist, create it
    def add_member(self, hname, hgname):
        id = self.find_id_by_name(hgname)
        #if the id do not exist, create the hg
        if id == None:
            hg = Hostgroup({'hostgroup_name' : hgname, 'alias' : hgname, 'members' :  hname})
            self.add(hg)
        else:
            self.itemgroups[id].add_string_member(hname)


    #Use to fill members with hostgroup_members
    def explode(self):
        #We do not want a same hg to be explode again and again
        #so we tag it
        for tmp_hg in self.itemgroups.values():
            tmp_hg.already_explode = False
        for hg in self.itemgroups.values():
            if hg.has('hostgroup_members') and not hg.already_explode:
                #get_hosts_by_explosion is a recursive
                #function, so we must tag hg so we do not loop
                for tmp_hg in self.itemgroups.values():
                    tmp_hg.rec_tag = False
                hg.get_hosts_by_explosion(self)

        #We clean the tags
        for tmp_hg in self.itemgroups.values():
            del tmp_hg.rec_tag
            del tmp_hg.already_explode
