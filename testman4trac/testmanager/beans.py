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

import copy
from datetime import date, datetime
import re
import time

from testmanager.constants import Constants
from testmanager.util import *
from trac.core import *
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionError
from trac.resource import Resource, ResourceNotFound
from trac.util.datefmt import utc, utcmax
from trac.util.text import CRLF
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from tracgenericclass.model import IConcreteClassProvider, AbstractVariableFieldsObject, AbstractWikiPageWrapper, need_db_create_for_realm, create_db_for_realm, need_db_upgrade_for_realm, upgrade_db_for_realm
from tracgenericclass.util import *


class TestCatalogBean(object):
    """
    A test catalog bean, used for presentation purposes.
    """
    
    def __init__(self, test_catalog = None, test_plan = None, has_status = False, color = None, unique_idx = 0):
        self.test_catalog = test_catalog
        
        self.test_plan = test_plan

        self.has_status = has_status
        
        self.color = color

        self.unique_idx = unique_idx
        
        self.sub_catalogs = {}
    
        self.test_cases = {}
        
        self.test_plans = None
        
        self.tot = 0
        
        self.key = None
        
    def add_sub_catalog(self, sub_catalog_bean):
        self.sub_catalogs[sub_catalog_bean.get_key()] = sub_catalog_bean
        
        self.tot += sub_catalog_bean.tot
        
        if self.has_status:
            self.color = self._calc_worse_color(sub_catalog_bean.color)
        
    def add_test_case(self, test_case_bean):
        self.test_cases[test_case_bean.get_key()] = test_case_bean
        
        self.tot += 1
        
        if self.has_status:
            self.color = self._calc_worse_color(test_case_bean.color)

    def load_test_plans(self):
        if self.test_plans is None:
            self.test_plans = {}
            i = 0
            for tp in self.test_catalog.list_testplans():
                test_plan_bean = TestPlanBean(self.test_catalog, tp, i)
                self.test_plans[test_plan_bean.get_key()] = test_plan_bean 
                i += 1
            
    def iterator(self):
        sorted_test_catalogs = sorted(self.sub_catalogs, key=_test_sorting(self.sub_catalogs))

        for sub_catalog_bean in sorted_test_catalogs:
            for item in sub_catalog_bean.iterator():
                yield item
                
        sorted_test_cases = sorted(self.test_cases, key=_test_sorting(self.test_cases))

        for test_case_bean in sorted_test_cases:
            yield test_case_bean
        
        yield TestListTerminatorBean()

    def sub_catalogs_iterator(self):
        sorted_test_catalogs = sorted(self.sub_catalogs, key=_test_sorting(self.sub_catalogs))

        for sub_catalog_bean in sorted_test_catalogs:
            yield sub_catalog_bean
    
    def test_cases_iterator(self):
        sorted_test_cases = sorted(self.test_cases, key=_test_sorting(self.test_cases))

        for test_case_bean in sorted_test_cases:
            yield test_case_bean

    def test_plans_iterator(self):
        sorted_test_plans = sorted(self.test_plans, key=_test_sorting(self.test_plans))

        for test_plan_bean in sorted_test_plans:
            yield self.test_plans[test_plan_bean]

    def get_key(self, sortby = 'custom'):

        if self.key is None:
            if sortby == 'custom' and self.test_catalog is not None and \
                    self.test_catalog['exec_order'] is not None and self.test_catalog['exec_order'] > 0:
                
                self.key = "%05d" % (self.test_catalog['exec_order'],)
            
            elif self.test_catalog is not None:
                self.key = self.test_catalog.title + str(self.unique_idx)
                
            else:
                self.key = 'NON_EXISTENT' + str(self.unique_idx)
        
        return self.key

    def get_test_catalog_id(self):
        if self.test_catalog is not None:
            return self.test_catalog['id']
        
        return ''

    def get_parent_id(self):
        if self.test_catalog is not None:
            return self.test_catalog['parent_id']
        
        return ''

    def get_test_plan_id(self):
        if self.test_plan is not None:
            return self.test_plan['id']
        
        return ''

    @property
    def title(self):
        if self.test_catalog is not None:
            return self.test_catalog.title
        
        return ''

    @property
    def description(self):
        if self.test_catalog is not None:
            return self.test_catalog.description
        
        return ''

    @property
    def page_name(self):
        if self.test_catalog is not None:
            return self.test_catalog['page_name']
        
        return ''

    def is_expandable(self):
        return tot > 0

    def has_test_plans(self):
        return self.test_plans is not None and len(self.test_plans) > 0

    def _calc_worse_color(self, other_color):
        if self.color == 'red' or other_color == 'red':
            return 'red'
            
        if self.color == 'yellow' or other_color == 'yellow':
            return 'yellow'
        
        return 'green'
        
    def as_dictionary(self):
        result = {'has_status': self.has_status, 'color': self.color, 'tot': self.tot, 'key': self.key}
        
        if self.test_catalog is not None:
            result['test_catalog'] = self.test_catalog.values
            result['test_catalog']['title'] = self.test_catalog.title
            result['test_catalog']['description'] = self.test_catalog.description

        if self.test_plan is not None:
            #result['test_plan'] = self.test_plan.values
            result['test_plan_id'] = self.test_plan['id']

        result['sub_catalogs'] = {}
        for sub_catalog in self.sub_catalogs:
            result['sub_catalogs'][sub_catalog] = self.sub_catalogs[sub_catalog].as_dictionary()
            
        result['test_cases'] = {}
        for test_case in self.test_cases:
            result['test_cases'][test_case] = self.test_cases[test_case].as_dictionary()
            
        return result

        
class TestCaseBean(object):
    """
    A test case bean, used for presentation purposes.
    """

    def __init__(self, test_case = None, has_status = False, test_plan = None, test_case_in_plan = None, color = None, unique_idx = 0):
        self.test_case = test_case

        self.has_status = has_status
        
        self.test_plan = test_plan
        
        self.test_case_in_plan = test_case_in_plan
        
        self.color = color
        
        self.unique_idx = unique_idx
        
        self.key = None

    def get_key(self, sortby = 'custom'):

        if self.key is None:
            if sortby == 'custom':
                if self.test_case.exists:
                    if self.test_case['exec_order'] is not None and self.test_case['exec_order'] > 0:
                        self.key = "%05d" % (self.test_case['exec_order'],)
                    
                    else:
                        self.key = self.test_case.title + str(self.unique_idx)

                else:
                    self.key = 'NON_EXISTENT' + str(self.unique_idx)
            
            elif sortby == 'name':
                self.key = self.test_case.title + str(self.unique_idx)
            
            else:
                ts = None
                if self.has_status and self.test_case_in_plan is not None and self.test_case_in_plan.exists:
                    for ts, author, status in self.test_case_in_plan.list_history():
                        break
                    
                    if not isinstance(ts, datetime):
                        ts = from_any_timestamp(ts)
                    
                else:
                    ts = self.test_plan['time']

                self.key = ts.isoformat()
        
        return self.key

    def get_test_case_id(self):
        if self.test_case is not None:
            return self.test_case['id']
        
        return ''

    def get_parent_id(self):
        if self.test_case is not None:
            return self.test_case['parent_id']
        
        return ''

    def get_test_plan_id(self):
        if self.test_plan is not None:
            return self.test_plan['id']
        
        return ''

    def get_test_plan_name(self):
        if self.test_plan is not None:
            return self.test_plan['name']
        
        return ''

    @property
    def title(self):
        if self.test_case is not None:
            return self.test_case.title
        
        return ''

    @property
    def description(self):
        if self.test_case is not None:
            return self.test_case.description
        
        return ''

    @property
    def page_name(self):
        if self.test_case is not None:
            return self.test_case['page_name']
        
        return ''

    def is_expandable(self):
        return False

    def as_dictionary(self):
        result = {'has_status': self.has_status, 'color': self.color, 'key': self.key}
        
        if self.test_case is not None:
            result['test_case'] = self.test_case.values
            result['test_case']['title'] = self.test_case.title
            result['test_case']['description'] = self.test_case.description

        if self.test_plan is not None:
            result['test_plan_id'] = self.test_plan['id']

        if self.test_case_in_plan is not None:
            result['test_case_in_plan'] = self.test_case_in_plan.values

        return result
        

class TestPlanBean(object):
    """
    A test plan bean, used for presentation purposes.
    """
    
    def __init__(self, test_catalog = None, test_plan = None, unique_idx = 0):
        self.test_catalog = test_catalog
        
        self.test_plan = test_plan

        self.unique_idx = unique_idx
        
        self.key = None

    @property
    def title(self):
        if self.test_plan is not None:
            return self.test_plan['name']
        
        return ''

    @property
    def contains_all(self):
        if self.test_plan is not None:
            return self.test_plan['contains_all']
        
        return 1

    @property
    def snapshot(self):
        if self.test_plan is not None:
            return self.test_plan['snapshot']
        
        return 0

    @property
    def author(self):
        if self.test_plan is not None:
            return self.test_plan['author']
        
        return ''

    @property
    def date(self):
        if self.test_plan is not None:
            return self.test_plan['time']
        
        return ''

    def get_test_plan_id(self):
        if self.test_plan is not None:
            return self.test_plan['id']
        
        return ''

    def get_test_catalog_id(self):
        if self.test_plan is not None:
            return self.test_plan['catid']
        
        return ''

    def get_key(self, sortby = 'custom'):

        if self.key is None:
            ts = self.test_plan['time']
            self.key = ts.isoformat()
        
        return self.key

        
class TestListTerminatorBean(object):
    """
    Used as an indicator of the end of a list of test artifacts
    """

    def is_expandable():
        return False


class BreadcrumbBean(object):
    """
    A breadcrumb bean, used for presentation purposes.
    """
    
    test_catalog = None
    
    test_case = None
    
    has_status = False
    
    test_plan = None
    
    def __init__(self, test_catalog = None, test_case = None, has_status = False, test_plan = None):
        self.test_catalog = test_catalog
        
        self.test_case = test_case

        self.has_status = has_status
        
        self.test_plan = test_plan

    def get_url(self, req):
        test_catalog_id = None
        if self.test_catalog is not None:
            test_catalog_id = self.test_catalog['id']
            
        test_case_id = None
        if self.test_case is not None:
            test_case_id = self.test_case['id']
            
        test_plan_id = None
        if self.test_plan is not None:
            test_plan_id = self.test_plan['id']
            
        mode = req.args.get('view_type', self.default_view_mode)
        fulldetails = req.args.get('fulldetails', 'False')
        
        href = Href(req.base_path, 'testview')

        return href(catid = test_catalog_id, tcid = test_case_id, planid = test_plan_id)

    def get_title(self, req):
        if self.test_case is not None:
            return self.test_case.title
            
        if self.test_catalog is not None:
            return self.test_catalog.title

        return _("All Catalogs")


def _test_sorting(items, sortby = 'custom'):
    def do_sort(k):
        return items[k].get_key(sortby = sortby)
        
    return do_sort
