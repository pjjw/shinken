#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


#DBMysql is a MySQL access database class
from shinken.db import DB

connect_function = None
IntegrityError_exp = None
ProgrammingError_exp = None
DatabaseError_exp = None
InternalError_exp = None
DataError_exp = None
OperationalError_exp = None


#Failed to import will be catch by __init__.py
from cx_Oracle import connect as connect_function
from cx_Oracle import IntegrityError as IntegrityError_exp
from cx_Oracle import ProgrammingError as ProgrammingError_exp
from cx_Oracle import DatabaseError as DatabaseError_exp
from cx_Oracle import InternalError as InternalError_exp
from cx_Oracle import DataError as DataError_exp
from cx_Oracle import OperationalError as OperationalError_exp


class DBOracle(DB):
    def __init__(self, user, password, database, table_prefix = ''):
        self.user = user
        self.password = password
        self.database = database
        self.table_prefix = table_prefix


    #Create the database connection
    #TODO : finish (begin :) ) error catch and conf parameters...
    def connect_database(self):
        connstr='%s/%s@%s' % (self.user, self.password, self.database)

        self.db = connect_function(connstr)
        self.db_cursor = self.db.cursor()
        self.db_cursor.arraysize=50


    #Just run the query
    #TODO: finish catch
    def execute_query(self, query):
        print "[DBOracle] I run Oracle query", query, "\n"
        try:
            self.db_cursor.execute(query)
            self.db.commit ()
        except IntegrityError_exp , exp:
            print "[DBOracle] Warning : a query raise an integrity error : %s, %s" % (query, exp)
        except ProgrammingError_exp , exp:
            print "[DBOracle] Warning : a query raise a programming error : %s, %s" % (query, exp)
        except DatabaseError_exp , exp:
            print "[DBOracle] Warning : a query raise a database error : %s, %s" % (query, exp)
        except InternalError_exp , exp:
            print "[DBOracle] Warning : a query raise an internal error : %s, %s" % (query, exp)
        except DataError_exp , exp:
            print "[DBOracle] Warning : a query raise a data error : %s, %s" % (query, exp)
        except OperationalError_exp , exp:
            print "[DBOracle] Warning : a query raise an operational error : %s, %s" % (query, exp)
        except Exception , exp:
            print "[DBOracle] Warning : a query raise an unknow error : %s, %s" % (query, exp)
            print exp.__dict__
