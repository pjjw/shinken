#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
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


from shinken.bin import VERSION
from shinken.satellite import Satellite
from shinken.util import to_int, to_bool


def usage(name):
    print "Shinken Poller Daemon, version %s, from : " % VERSION
    print "        Gabes Jean, naparuba@gmail.com"
    print "        Gerhard Lausser, Gerhard.Lausser@consol.de"
    print "        Gregory Starck, g.starck@gmail.com"
    print "Usage: %s [options] [-c configfile]" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file."
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"



#Our main APP class
class Poller(Satellite):
    do_checks = True #I do checks
    do_actions = False #but no actions
    #default_port = 7771

    properties = {
            'workdir' : {'default' : '/usr/local/shinken/var', 'pythonize' : None, 'path' : True},
            'pidfile' : {'default' : '/usr/local/shinken/var/pollerd.pid', 'pythonize' : None, 'path' : True},
            'port' : {'default' : '7771', 'pythonize' : to_int},
            'host' : {'default' : '0.0.0.0', 'pythonize' : None},
            'user' : {'default' : 'shinken', 'pythonize' : None},
            'group' : {'default' : 'shinken', 'pythonize' : None},
            'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool},
            'use_ssl' : {'default' : '0', 'pythonize' : to_bool},
            'certs_dir' : {'default' : 'etc/certs', 'pythonize' : None},
            'ca_cert' : {'default' : 'etc/certs/ca.pem', 'pythonize' : None},
            'server_cert' : {'default': 'etc/certs/server.pem', 'pythonize' : None},
            'hard_ssl_name_check' : {'default' : '0', 'pythonize' : to_bool},
            }


    ################### Process launch part

