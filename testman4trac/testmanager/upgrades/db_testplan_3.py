# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2015 Roberto Longobardi
# 
# This file is part of the Test Manager plugin for Trac.
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at: 
#   https://trac-hacks.org/wiki/TestManagerForTracPluginLicense
#
# Author: Roberto Longobardi <otrebor.dev@gmail.com>
#

from trac.db import Table, Column, Index, DatabaseManager

from tracgenericclass.model import create_db_for_realm
from tracgenericclass.util import *

from testmanager.model import TestManagerModelProvider

def do_upgrade(env, ver, db_backend, db):
    """
    Remove page_name column
    """
    cursor = db.cursor()
    
    realm = 'testplan'

    env.log.info("Creating temporary table for test plans")
    cursor.execute("CREATE TEMPORARY TABLE %(realm)s_old AS SELECT * FROM %(realm)s" % {'realm': realm})

    env.log.info("Dropping old test plan table")
    cursor.execute("DROP TABLE %(realm)s" % {'realm': realm})

    table_metadata = TestManagerModelProvider(env).get_data_models()[realm]['table']

    env.log.info("Creating new table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    new_table_contents = []

    cursor = db.cursor()

    cursor.execute("SELECT id, catid, name, author, time, contains_all, freeze_tc_versions FROM %(realm)s_old" % {'realm': realm})

    env.log.info("Reading test plans")
    for id, catid, name, author, time, contains_all, freeze_tc_versions in cursor:
        row = {'id': id, 'catid': catid, 'name': name, 'author': author, 'time': time, 'contains_all': contains_all, 'freeze_tc_versions': freeze_tc_versions}
        env.log.info(row)

        new_table_contents.append(row)

    env.log.info("Migrating test plans")
    for new_row in new_table_contents:
        env.log.info(new_row)
        cursor.execute("INSERT INTO " + realm + " (id, catid, name, author, time, contains_all, freeze_tc_versions) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
            (new_row['id'], new_row['catid'], new_row['name'], new_row['author'], new_row['time'], new_row['contains_all'], new_row['freeze_tc_versions']))

    env.log.info("Dropping test plans temporary table")
    cursor.execute("DROP TABLE %(realm)s_old" % {'realm': realm})
