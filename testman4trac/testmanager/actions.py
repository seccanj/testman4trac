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

import json

from StringIO import StringIO

from trac.mimeview.api import Context
from trac.util import get_reporter_id
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser

from tracstruts.api import Invocable

from tracgenericclass.cache import GenericClassCacheSystem
from tracgenericclass.model import GenericClassModelProvider
from tracgenericclass.util import *

from testmanager.beans import *
from testmanager.util import *
from testmanager.admin import get_all_table_columns_for_object
from testmanager.api import TestManagerSystem
from testmanager.model import TestCatalog, TestCase, TestCaseInPlan, TestPlan, TestManagerModelProvider

from genshi.filters.transform import Transformer

try:
    from testmanager.api import _, tag_, N_
except ImportError:
    from trac.util.translation import _, N_
    tag_ = _


# Contains the TracStruts actions
class Actions(object):

    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'testmanager.html'}
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def initview(self):
        self.env.log.debug(">> initview")
        
        self.env.log.debug("<< initview")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def loadtree(self):
        self.env.log.debug(">> loadtree")

        GenericClassCacheSystem.clear_cache()

        test_catalog_beans = TestManagerSystem(self.env).get_all_test_catalogs_data_model()

        jsdstr = '['
        for idx, test_catalog_bean in enumerate(test_catalog_beans):
            jsdstr += json.dumps(test_catalog_bean.as_dictionary())
            
            if idx < len(test_catalog_beans)-1:
                jsdstr += ','
        
        jsdstr += ']'
            
        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< loadtree")
        
        return 'success'

    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'mode': 'in',
                'fulldetails': 'in',
                'sortby': 'in'
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def get_test_catalog(self, test_catalog_id, test_plan_id):
        self.env.log.debug(">> get_test_catalog")

        GenericClassCacheSystem.clear_cache()

        if not self.mode:
            self.mode = Constants(self.env).default_view_mode

        self.fulldetails = self.fulldetails or 'False'

        self.env.log.debug("test_catalog_id: '%s', test_plan_id: '%s'" % (test_catalog_id, test_plan_id))

        if test_catalog_id is None:
            raise TracException("Should provide a test catalog ID.") 

        include_status = test_plan_id is not None

        test_plan = _get_test_plan(test_plan_id, self.env)
        test_catalog = _get_test_catalog(test_catalog_id, self.env)

        test_catalog_bean = TestManagerSystem(self.env).get_test_catalog_data_model(test_catalog, sortby = self.sortby, include_status = include_status, test_plan = test_plan)
        jsdstr = json.dumps(test_catalog_bean.as_dictionary())
                
        self.ajax_result = jsdstr
            
        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_catalog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'test_catalog.html'}
            },
            'parameters': {
                'mode': 'in',
                'fulldetails': 'in',
                'test_catalog_bean': 'out',
                'wiki_contents': 'out'
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def get_test_catalog_details(self, test_catalog_id, test_plan_id):
        self.env.log.debug(">> get_test_catalog_details")

        GenericClassCacheSystem.clear_cache()

        if not self.mode:
            self.mode = Constants(self.env).default_view_mode

        self.fulldetails = self.fulldetails or 'False'

        self.env.log.debug("test_catalog_id: '%s', test_plan_id: '%s'" % (test_catalog_id, test_plan_id))

        if test_catalog_id is None:
            raise TracException("Should provide a test catalog ID.") 

        include_status = test_plan_id is not None

        test_plan = _get_test_plan(test_plan_id, self.env)
        test_catalog = _get_test_catalog(test_catalog_id, self.env)

        self.test_catalog_bean = TestManagerSystem(self.env).get_test_catalog_details_data_model(test_catalog = test_catalog, include_status = include_status, test_plan = test_plan)
        self.wiki_contents = self._get_wiki_page_contents(self.req, self.env, test_catalog['page_name'], test_catalog.description)
            
        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_catalog_details")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'test_case.html'}
            },
            'parameters': {
                'mode': 'in',
                'fulldetails': 'in',
                'test_case_bean': 'out',
                'wiki_contents': 'out'
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def get_test_case_details(self, test_case_id, test_plan_id):
        self.env.log.debug(">> get_test_case_details")

        GenericClassCacheSystem.clear_cache()

        if not self.mode:
            self.mode = Constants(self.env).default_view_mode

        self.fulldetails = self.fulldetails or 'False'

        self.env.log.debug("test_case_id: '%s', test_plan_id: '%s'" % (test_case_id, test_plan_id))

        if test_case_id is None:
            raise TracException("Should provide a test case ID.") 

        include_status = test_plan_id is not None

        test_plan = _get_test_plan(test_plan_id, self.env)
        test_case = _get_test_case(test_case_id, self.env)

        self.test_case_bean = TestManagerSystem(self.env).get_test_case_data_model(test_case = test_case, include_status = include_status, test_plan = test_plan)
        self.wiki_contents = self._get_wiki_page_contents(self.req, self.env, test_case['page_name'], test_case.description)
            
        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_case_details")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'breadcrumbs.html'}
            },
            'parameters': {
                'breadcrumbs': 'out'
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def get_breadcrumbs(self, test_catalog_id, test_case_id, test_plan_id):
        self.env.log.debug(">> get_breadcrumbs")

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("test_catalog_id: '%s', test_case_id: '%s', test_plan_id: '%s'" % (test_catalog_id, test_case_id, test_plan_id))

        test_catalog = _get_test_catalog(test_catalog_id, self.env)
        test_case = _get_test_case(test_case_id, self.env)
        test_plan = _get_test_plan(test_plan_id, self.env)

        self.breadcrumbs = self._get_breadcrumbs(test_catalog = test_catalog, test_case = test_case, test_plan = test_plan)
            
        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_breadcrumbs")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'new_test_catalog_dialog.html'}
            },
            'parameters': {
                'parent_id': 'in_out',
                'parent_test_catalog': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_new_test_catalog_dialog(self):
        self.env.log.debug(">> get_new_test_catalog_dialog")

        self.env.log.debug("parent_id: '%s'" % (parent_id))

        if parent_id != '-1':
            self.parent_test_catalog = _get_test_catalog(parent_id, self.env)

        self.env.log.debug("<< get_new_test_catalog_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'new_test_case_dialog.html'}
            },
            'parameters': {
                'parent_id': 'in_out',
                'parent_test_catalog': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_new_test_case_dialog(self):
        self.env.log.debug(">> get_new_test_case_dialog")

        self.env.log.debug("parent_id: '%s'" % (parent_id))

        self.parent_test_catalog = _get_test_catalog(parent_id, self.env)

        self.env.log.debug("<< get_new_test_case_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def create_test_catalog(self, parent_id, title):
        self.env.log.debug(">> create_test_catalog")

        self.env.log.debug("parent_id: '%s'" % (parent_id))

        test_manager_system = TestManagerSystem(self.env)

        id = test_manager_system.get_next_id('catalog')

        jsdstr = None
        
        try:
            # Add template if exists...
            new_content = test_manager_system.get_default_tcat_template()
            
            pagename = 'TC_TT'+str(id)
            new_tc = TestCatalog(self.env, id, pagename, parent_id, title, new_content)

            new_tc.author = get_reporter_id(req, 'author')
            new_tc.remote_addr = self.req.remote_addr
            # This also creates the Wiki page
            new_tc.insert()
            
            self.test_catalog = TestCatalogBean(new_tc)

            jsdstr = '{"result": "OK", "id": ' + str(id) + '}'

        except:
            self.env.log.error("Error adding test catalog!")
            self.env.log.error(formatExceptionInfo())

            jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test catalog."}'

        self.ajax_result = jsdstr

        self.env.log.debug("<< create_test_catalog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def create_test_case(self, parent_id, title):
        self.env.log.debug(">> create_test_case")

        self.env.log.debug("parent_id: '%s'" % (parent_id))

        test_manager_system = TestManagerSystem(self.env)

        id = test_manager_system.get_next_id('testcase')
        pagename = 'TC_TC'+str(id)

        jsdstr = None
        
        try:
            # Get containing catalog
            parent_tcat = TestCatalog(self.env, parent_id)

            # Add template if exists...
            new_content = test_manager_system.get_tc_template(parent_tcat['page_name'])

            new_tc = TestCase(self.env, id, pagename, parent_id, title, new_content)
            new_tc.author = get_reporter_id(req, 'author')
            new_tc.remote_addr = self.req.remote_addr

            new_tc.insert()
            
            self.test_case = TestCaseBean(new_tc)

            jsdstr = '{"result": "OK", "id": ' + str(id) + '}'

        except:
            self.env.log.error("Error adding test catalog!")
            self.env.log.error(formatExceptionInfo())

            jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test catalog."}'

        self.ajax_result = jsdstr

        self.env.log.debug("<< create_test_case")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'tm_action_output_template.html'},
                'success_ajax': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'mode': 'in_out',
                'fulldetails': 'in_out',
                'parent_id': 'in_out',
                'artifact': 'in_out',
                'test_catalog_id': 'in_out',
                'test_case_id': 'in_out',
                'test_plan_id': 'in_out',
                'breadcrumbs': 'out',
                'wiki_contents': 'out',
                'test_catalog': 'out',
                'test_case': 'out'            
            }
        }
    )
    def getcatalog_OLD(self, test_catalog_id, test_plan_id):
        self.env.log.debug(">> getcatalog")

        if not self.req.perm.has_permission('TEST_VIEW') and not self.req.perm.has_permission('TEST_ADMIN'):
            raise PermissionError('TEST_VIEW', None, self.env)

        result = 'success'
        
        GenericClassCacheSystem.clear_cache()

        if not self.mode:
            self.mode = Constants(self.env).default_view_mode

        if not self.fulldetails:
            self.fulldetails = 'False'

        self.env.log.debug("test_catalog_id: '%s', test_case_id: '%s', test_plan_id: '%s'" % (self.test_catalog_id, self.test_case_id, self.test_plan_id))

        show_all = test_catalog_id is None and test_case_id is None and test_plan_id is None
        include_status = test_plan_id is not None

        test_plan = None
        if self.test_plan_id is not None:
            test_plan = TestPlan(self.env, self.test_plan_id, self.test_catalog_id)
        
            if not test_plan.exists:
                raise TracException("The specified test plan with id '%s' does not exist." % (self.test_plan_id,)) 

        test_catalog = None
        if self.test_catalog_id is not None:
            test_catalog = TestCatalog(self.env, self.test_catalog_id)
            
            if not test_catalog.exists:
                raise TracException("The specified test catalog with id '%s' does not exist." % (self.test_catalog_id,)) 

        test_case = None
        if self.test_case_id is not None:
            test_case = TestCase(self.env, self.test_case_id)
            
            if not test_case.exists:
                raise TracException("The specified test case with id '%s' does not exist." % (self.test_case_id,)) 

        if artifact == 'breadcrumbs':
            self.breadcrumbs = self._get_breadcrumbs(test_catalog = test_catalog, test_case = test_case, test_plan = test_plan)
            
            template = 'breadcrumbs.html'
            
        elif artifact == 'test_case_details':
            self.test_case = TestManagerSystem(self.env).get_test_case_data_model(test_case = test_case, include_status = include_status, test_plan = test_plan)
            self.wiki_contents = self._get_wiki_page_contents(req, test_case['page_name'], test_case.description)
                
            template = 'test_case.html'

        elif artifact == 'test_catalog_details':
            self.test_catalog = TestManagerSystem(self.env).get_test_catalog_details_data_model(test_catalog = test_catalog, include_status = include_status, test_plan = test_plan)
            self.wiki_contents = self._get_wiki_page_contents(req, test_catalog['page_name'], test_catalog.description)
            
            template = 'test_catalog.html'

        else:
            use_template = False
            jsdstr = None
            
            if show_all:
                test_catalog_beans = TestManagerSystem(self.env).get_all_test_catalogs_data_model()
                jsdstr = '['
                
                for idx, test_catalog_bean in enumerate(test_catalog_beans):
                    jsdstr += json.dumps(test_catalog_bean.as_dictionary())
                    
                    if idx < len(test_catalog_beans)-1:
                        jsdstr += ','
                
                jsdstr += ']'

            else:
                test_catalog_bean = TestManagerSystem(self.env).get_test_catalog_data_model(test_catalog, sortby = self.sortby, include_status = include_status, test_plan = test_plan)
                jsdstr = json.dumps(test_catalog_bean.as_dictionary())
                
            self.ajax_result = jsdstr
            
            result = 'success_ajax'

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< loadtree")
        
        return result


def _check_view_permission(req, env):
    if not req.perm.has_permission('TEST_VIEW') and not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_VIEW', None, env)

def _check_modify_permission(req, env):
    if not req.perm.has_permission('TEST_MODIFY') and not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_MODIFY', None, env)

def _check_execute_permission(req, env):
    if not req.perm.has_permission('TEST_EXECUTE') and not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_EXECUTE', None, env)

def _check_delete_permission(req, env):
    if not req.perm.has_permission('TEST_DELETE') and not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_DELETE', None, env)

def _check_plan_admin_permission(req, env):
    if not req.perm.has_permission('TEST_PLAN_ADMIN') and not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_PLAN_ADMIN', None, env)

def _check_admin_permission(req, env):
    if not req.perm.has_permission('TEST_ADMIN'):
        raise PermissionError('TEST_ADMIN', None, env)


def _get_wiki_page_contents(req, env, page_name, markup):
    context = Context.from_request(req, 'wiki', page_name)
    wikidom = WikiParser(env).parse(markup)
    out = StringIO()
    f = Formatter(env, context)
    f.reset(wikidom)
    f.format(wikidom, out, False)

    return out.getvalue()

def _get_test_plan(test_plan_id, env):
    test_plan = None
    if test_plan_id is not None:
        test_plan = TestPlan(env, test_plan_id)
    
        if not test_plan.exists:
            raise TracException("The specified test plan with id '%s' does not exist." % (test_plan_id,)) 

    return test_plan

def _get_test_catalog(test_catalog_id, env):
    test_catalog = None
    if test_catalog_id is not None:
        test_catalog = TestCatalog(env, test_catalog_id)
        
        if not test_catalog.exists:
            raise TracException("The specified test catalog with id '%s' does not exist." % (test_catalog_id,)) 

    return test_catalog

def _get_test_case(test_case_id, env):
    test_case = None
    if test_case_id is not None:
        test_case = TestCase(env, test_case_id)
        
        if not test_case.exists:
            raise TracException("The specified test case with id '%s' does not exist." % (test_case_id,)) 

    return test_case
    
