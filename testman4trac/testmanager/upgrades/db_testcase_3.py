# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2022 Roberto Longobardi
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
from trac.attachment import Attachment

from tracgenericclass.util import *

from testmanager.model import TestManagerModelProvider

def do_upgrade(env, ver, db_backend, db):
    """
    Add 'parent_id' column and corresponding index to testcase table
    """
    cursor = db.cursor()
    
    realm = 'testcase'

    env.log.info("Creating temporary table for test cases")
    cursor.execute("CREATE TEMPORARY TABLE %(realm)s_old AS SELECT * FROM %(realm)s" % {'realm': realm})

    env.log.info("Dropping old test cases table")
    cursor.execute("DROP TABLE %(realm)s" % {'realm': realm})

    table_metadata = TestManagerModelProvider(env).get_data_models()[realm]['table']

    env.log.info("Creating new table for class %s" % realm)
    for stmt in db_backend.to_sql(table_metadata):
        env.log.debug(stmt)
        cursor.execute(stmt)

    new_table_contents = []

    cursor = db.cursor()

    cursor.execute("SELECT id,page_name,exec_order FROM %(realm)s_old" % {'realm': realm})

    env.log.info("Determining parent_id and page_name values for every test case")
    for id, page_name, exec_order in cursor:
        parent_path = page_name.rpartition('_')[0]
        parent_id = int(parent_path.rpartition('_TT')[2])
            
        row = {'id': id, 'old_page_name': page_name, 'page_name': 'TC_TC'+str(id), 'exec_order': exec_order, 'parent_id': parent_id}
        env.log.info(row)

        new_table_contents.append(row)

    env.log.info("Migrating test cases")
    for new_row in new_table_contents:
        env.log.info(new_row)
        cursor.execute("INSERT INTO " + realm + " (id, page_name, exec_order, parent_id) VALUES (%s, %s, %s, %s)", 
            (new_row['id'], new_row['page_name'], new_row['exec_order'], new_row['parent_id']))

        # Rename the wiki page
        cursor.execute("UPDATE wiki SET name = %s WHERE name = %s", 
            (new_row['page_name'], new_row['old_page_name']))

        # Reparent wiki attachments
        Attachment.reparent_all(env, 'wiki', new_row['old_page_name'], 'wiki', new_row['page_name'])

    env.log.info("Dropping test cases temporary table")
    cursor.execute("DROP TABLE %(realm)s_old" % {'realm': realm})

    # Invalidate Trac 0.12 page name cache
    try:
        del WikiSystem(self.env).pages
    except:
        pass

