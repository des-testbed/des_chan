#!/usr/bin/python
"""
DES-CHAN: A Framework for Channel Assignment Algorithms for Testbeds

des_db - A simple interface to access the database of the DES-Testbed, which
stores information about the network nodes. This is a stripped version of the 
testbed management system (TBMS) that only supports to run raw queries via the
_raw_query(..) function.

The module uses PgSQL - A PyDB-SIG 2.0 compliant module to access the PostgreSQL
database. The latter is included in the Debian package python-pgsql.

Authors:    Matthias Philipp <mphilipp@inf.fu-berlin.de>,
            Felix Juraschek <fjuraschek@gmail.com>

Copyright 2008-2013, Freie Universitaet Berlin (FUB). All rights reserved.

These sources were developed at the Freie Universitaet Berlin, 
Computer Systems and Telematics / Distributed, embedded Systems (DES) group 
(http://cst.mi.fu-berlin.de, http://www.des-testbed.net)
-------------------------------------------------------------------------------
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see http://www.gnu.org/licenses/ .
--------------------------------------------------------------------------------
For further information and questions please use the web site
       http://www.des-testbed.net
       
"""

from os import path


try:
    from pyPgSQL import PgSQL
except ImportError:
    raise ImportError("You need to install PgSQL - A PyDB-SIG 2.0 compliant "\
                      "module for PostgreSQL.\nIt is included in the Debian "\
                      "package python-pgsql.")


class Error(Exception):
    """Base class for exceptions in this module."""
    pass

# Define the default connection parameters for the DES database
_HOST = "host"
_DATABASE = "db_name"
_USER = "db_user"
_PASSWORD = "db_pwd"
# Global variable to store the PgSQL.connection object
_connection = None


def _connect(host="", database="", user="", password=""):
    """Opens a connection to the database.

    Normally, this function does not have to be called, because the other
    functions of this module connect to the database automatically.  If invoked
    without parameters, it uses the default connection parameters for the DES
    database.  If, for some reason, you need to connect to a different database
    or use different credentials, you can invoke this function with the desired
    parameters. Further calls of functions from this module will then use that
    connection.

    """
    global _connection
    # Use the default values for the connection, if the parameters are not given
    if host == "":
        host = _HOST
    if database == "":
        database = _DATABASE
    if user == "":
        user = _USER
    if password == "":
        password = _PASSWORD
    # Make a connection to the database and check to see if it succeeded.
    try:
        _connection = PgSQL.connect(host=host, database=database, user=user,\
                                    password=password)
    except PgSQL.Error, msg:
        errstr = "Connection to database '%s' failed\n%s" % (_DATABASE, msg)
        raise Error(errstr.strip())


def _disconnect():
    """Closes the connection to the database.

    Note, that there is normally no need to call this function, since the
    connection is terminated automatically in the destructor of the
    PgSQL.connection object.

    """
    global _connection
    _connection.close()
    _connection = None


def _raw_query(stmt):
    """Executes the given SQL statement.

    It returns a list of dictionaries. The list contains a dictionary for each
    result row. The dictionaries contain the column names as keys and the
    selected values as values.

    """
    # Connect to the database if necessary
    if _connection is None:
        _connect()
    # Create a Cursor object.  This handles the transaction block and the
    # declaration of the database cursor.  
    cursor = _connection.cursor() 
    # Try to execute the INSERT statement
    try:
        cursor.execute(stmt)
    except PgSQL.Error, msg:
        errstr = "Following statement failed:\n%s\n%s" % (stmt, msg)
        raise Error(errstr.strip())
    # List that contains a dictionary with column name and data for each result row
    data = list()
    # Get the first result row
    result = cursor.fetchone()
    # as long as there are result rows available
    while result is not None:
        # dictionary for this row
        row = dict()
        # add the column name and data for each column of this result row
        for column in result.description():
            row.update({column[0]: eval("result.%s" % column[0])})
        # append the dictionary from this row to the list of rows
        data.append(row)
        # Get the next result row
        result = cursor.fetchone()
    # Close the cursor
    cursor.close()
    # Commit the transaction
    _connection.commit()
    return data

