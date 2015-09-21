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
    Removing page_name column
    """
    cursor = db.cursor()
    
    realm = 'testcaseinplan'

    env.log.info("Creating temporary table for test cases in plan")
    cursor.execute("CREATE TEMPORARY TABLE %(realm)s_old AS SELECT * FROM %(realm)s" % {'realm': realm})

    env.log.info("Dropping old test cases in plan table")
    cursor.execute("DROP TABLE %(realm)s" % {'realm': realm})

    table_metadata = TestManagerModelProvider(env).get_data_models()[realm]['table']

    env.log.info("Creating new table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    new_table_contents = []

    cursor = db.cursor()

    cursor.execute("SELECT id, planid, page_version, status FROM %(realm)s_old" % {'realm': realm})

    env.log.info("Reading test cases in plan")
    for id, planid, page_version, status in cursor:
        row = {'id': id, 'planid': planid, 'page_version': page_version, 'status': status}
        env.log.info(row)

        new_table_contents.append(row)

    env.log.info("Migrating test cases in plan")
    for new_row in new_table_contents:
        env.log.info(new_row)
        cursor.execute("INSERT INTO " + realm + " (id, planid, page_version, status) VALUES (%s, %s, %s, %s)", 
            (new_row['id'], new_row['planid'], new_row['page_version'], new_row['status']))

    env.log.info("Dropping test cases in plan temporary table")
    cursor.execute("DROP TABLE %(realm)s_old" % {'realm': realm})

