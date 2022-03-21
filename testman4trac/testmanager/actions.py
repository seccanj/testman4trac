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

from StringIO import StringIO
import json

from genshi.filters.transform import Transformer
from genshi.core import Markup

from testmanager.admin import get_all_table_columns_for_object
from testmanager.api import TestManagerSystem
from testmanager.beans import *
from testmanager.model import TestCatalog, TestCase, TestCaseInPlan, TestPlan, TestManagerModelProvider
from testmanager.util import *

from trac.attachment import AttachmentModule
from trac.util import get_reporter_id
from trac.web.chrome import web_context
from trac.web.session import *
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser

from testmanager.util import *

from tracgenericclass.cache import GenericClassCacheSystem
from tracgenericclass.model import GenericClassModelProvider
from tracgenericclass.util import *

from tracstruts.api import Invocable


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
            'parameters': {
                'url_artifact_type': 'in_out',
                'url_artifact_id': 'in_out',
                'url_artifact_planid': 'in_out'
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def initview(self):
        self.env.log.debug(">> initview")
        
        if self.url_artifact_type is not None and self.url_artifact_type != '':
            session_attributes = {
                    'artifact_type': self.url_artifact_type,
                    'artifact_id': self.url_artifact_id,
                    'artifact_planid': self.url_artifact_planid
                }
            
            _save_session(self.env, self.req, session_attributes)
            
        
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
    def get_session(self):
        self.env.log.debug(">> get_session")
        
        session_attributes = _retrieve_session(self.env, self.req)
        
        jsdstr = json.dumps(session_attributes)
            
        self.ajax_result = jsdstr
        
        self.env.log.debug("<< get_session")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_VIEW', 'TEST_ADMIN')
        }
    )
    def resetview(self):
        self.env.log.debug(">> resetview")
        
        _save_session(self.env, self.req, {})
        
        jsdstr = '{}'
            
        self.ajax_result = jsdstr
        
        self.env.log.debug("<< resetview")
        
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
                'test_catalog': {'kind': 'template', 'template_name': 'test_catalog.html'},
                'test_plan': {'kind': 'template', 'template_name': 'test_plan.html'}
            },
            'parameters': {
                'mode': 'in',
                'fulldetails': 'in',
                'test_catalog_bean': 'out',
                'wiki_contents': 'out',
                'attachments': 'out',
                'can_modify': 'out',
                'tzinfo': 'out',
                'Markup': 'out',
                'custom_fields': 'out',
                'custom_field_values': 'out',
                'custom_field_values_markup': 'out',
                'obj': 'out',
                'obj_key': 'out'
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
        
        self.Markup = Markup

        test_plan = _get_test_plan(test_plan_id, self.env)
        test_catalog = _get_test_catalog(test_catalog_id, self.env)

        self.test_catalog_bean = TestManagerSystem(self.env).get_test_catalog_details_data_model(test_catalog = test_catalog, include_status = include_status, test_plan = test_plan)
        self.test_catalog_bean.load_test_plans()
        self.wiki_contents = _get_wiki_page_contents(self.req, self.env, test_catalog['page_name'], test_catalog.description)
        
        page = WikiPage(self.env, test_catalog['page_name'], version=None)
        context = web_context(self.req, page.resource)
        self.attachments = AttachmentModule(self.env).attachment_data(context)
        self.can_modify = _can_modify(self.req)
        self.tzinfo = get_default_timezone(self.env)

        if include_status:
            self.obj = test_plan
            self.obj_key = test_plan.gey_key_string()
            self.prepare_custom_fields('testplan')
        else:
            self.obj = test_catalog
            self.obj_key = test_catalog.gey_key_string()
            self.prepare_custom_fields('testcatalog')

        session_attributes = {
                'artifact_type': 'testcatalog',
                'artifact_id': test_catalog_id,
                'artifact_planid': test_plan_id
            }
        
        _save_session(self.env, self.req, session_attributes)

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_catalog_details")
        
        if test_plan_id is not None and test_plan_id != '':
            return 'test_plan'

        return 'test_catalog'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'test_case.html'}
            },
            'parameters': {
                'mode': 'in',
                'fulldetails': 'in',
                'test_case_bean': 'out',
                'wiki_contents': 'out',
                'attachments': 'out',
                'can_modify': 'out',
                'tzinfo': 'out',
                'default_outcome': 'out',
                'statuses_by_name': 'out',
                'Markup': 'out',
                'custom_fields': 'out',
                'custom_field_values': 'out',
                'custom_field_values_markup': 'out',
                'obj': 'out',
                'obj_key': 'out'
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
        
        self.default_outcome = TestManagerSystem(self.env).get_default_tc_status()
        self.statuses_by_name = TestManagerSystem(self.env).get_tc_statuses_by_name()
        self.Markup = Markup

        test_plan = _get_test_plan(test_plan_id, self.env)
        test_case = _get_test_case(test_case_id, self.env)
        test_case_in_plan = _get_test_case_in_plan(test_case_id, test_plan_id, self.env)

        self.test_case_bean = TestManagerSystem(self.env).get_test_case_data_model(test_case = test_case, include_status = include_status, test_plan = test_plan)

        self.wiki_contents = _get_wiki_page_contents(self.req, self.env, test_case['page_name'], self.test_case_bean.description)
        
        page = WikiPage(self.env, name = test_case['page_name'])
        context = web_context(self.req, page.resource)
        self.attachments = AttachmentModule(self.env).attachment_data(context)
        self.can_modify = _can_modify(self.req)
        self.tzinfo = get_default_timezone(self.env)

        if include_status:
            self.obj = test_case_in_plan
            self.obj_key = test_case_in_plan.gey_key_string()
            self.prepare_custom_fields('testcaseinplan')
        else:
            self.obj = test_case
            self.obj_key = test_case.gey_key_string()
            self.prepare_custom_fields('testcase')

        session_attributes = {
                'artifact_type': 'testcase',
                'artifact_id': test_case_id,
                'artifact_planid': test_plan_id
            }
        
        _save_session(self.env, self.req, session_attributes)

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_case_details")
        
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
            'required_roles': ('TEST_VIEW', 'TEST_EXECUTE', 'TEST_ADMIN')
        }
    )
    def get_test_plan(self, test_plan_id):
        self.env.log.debug(">> get_test_plan")

        GenericClassCacheSystem.clear_cache()

        test_plan = TestPlan(self.env, test_plan_id)
        test_catalog = TestCatalog(self.env, test_plan['catid'])
        test_catalog_bean = TestManagerSystem(self.env).get_test_catalog_data_model(test_catalog, sortby = self.sortby, include_status = True, test_plan = test_plan)

        jsdstr = '['
        jsdstr += json.dumps(test_catalog_bean.as_dictionary())
        jsdstr += ']'
        
        self.ajax_result = jsdstr

        session_attributes = {
                'artifact_type': 'testcatalog',
                'artifact_id': test_plan['catid'],
                'artifact_planid': test_plan_id
            }
        
        _save_session(self.env, self.req, session_attributes)

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< get_test_plan")
        
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

        self.env.log.debug("parent_id: '%s'" % (self.parent_id))

        if self.parent_id != '-1':
            self.parent_test_catalog = _get_test_catalog(self.parent_id, self.env)

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

        self.env.log.debug("parent_id: '%s'" % (self.parent_id))

        self.parent_test_catalog = _get_test_catalog(self.parent_id, self.env)

        self.env.log.debug("<< get_new_test_case_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'new_test_plan_dialog.html'}
            },
            'parameters': {
                'parent_id': 'in_out',
                'parent_test_catalog': 'out'
            },
            'required_roles': ('TEST_PLAN_ADMIN', 'TEST_ADMIN')
        }
    )
    def get_new_test_plan_dialog(self):
        self.env.log.debug(">> get_new_test_plan_dialog")

        self.env.log.debug("parent_id: '%s'" % (self.parent_id))

        self.parent_test_catalog = _get_test_catalog(self.parent_id, self.env)

        self.env.log.debug("<< get_new_test_plan_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'edit_title_dialog.html'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'title': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_edit_title_dialog(self):
        self.env.log.debug(">> get_edit_title_dialog")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env)
        self.title = test_artifact.title
        
        self.env.log.debug("<< get_edit_title_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'edit_description_dialog.html'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'description': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_edit_description_dialog(self):
        self.env.log.debug(">> get_edit_description_dialog")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env)
        self.description = test_artifact.description
        
        self.env.log.debug("<< get_edit_description_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'attachments_dialog.html'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'wikipage': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_attachments_dialog(self):
        self.env.log.debug(">> get_attachments_dialog")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env)
        page_name = test_artifact['page_name']

        self.wikipage = WikiPage(self.env, page_name)
    
        self.env.log.debug("<< get_attachments_dialog")
        
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

        GenericClassCacheSystem.clear_cache()

        test_manager_system = TestManagerSystem(self.env)

        id = test_manager_system.get_next_id('catalog')

        jsdstr = None
        
        try:
            # Add template if exists...
            new_content = test_manager_system.get_default_tcat_template()
            
            pagename = 'TC_TT'+str(id)
            new_tc = TestCatalog(self.env, id, pagename, parent_id, title, new_content)

            new_tc.author = get_reporter_id(self.req, 'author')
            new_tc.remote_addr = self.req.remote_addr
            # This also creates the Wiki page
            new_tc.insert()
            
            jsdstr = '{"result": "OK", "id": ' + str(id) + '}'

        except:
            self.env.log.error("Error adding test catalog!")
            self.env.log.error(formatExceptionInfo())

            jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test catalog."}'

        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

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

        GenericClassCacheSystem.clear_cache()

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
            new_tc.author = get_reporter_id(self.req, 'author')
            new_tc.remote_addr = self.req.remote_addr

            new_tc.insert()
            
            jsdstr = '{"result": "OK", "id": ' + str(id) + '}'

        except:
            self.env.log.error("Error adding test catalog!")
            self.env.log.error(formatExceptionInfo())

            jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test case."}'

        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< create_test_case")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_PLAN_ADMIN', 'TEST_ADMIN')
        }
    )
    def create_test_plan(self, parent_id, title, contains_all, snapshot, selected_test_cases=""):
        self.env.log.debug(">> create_test_plan")

        self.env.log.debug("parent_id: '%s'" % (parent_id))

        GenericClassCacheSystem.clear_cache()

        test_manager_system = TestManagerSystem(self.env)
        id = test_manager_system.get_next_id('testplan')

        jsdstr = None
        
        try:
            contains_all_int = (0, 1)[contains_all == 'true']
            snapshot_int = (0, 1)[snapshot == 'true']
            selected_tcs = []
            if not contains_all_int and not selected_test_cases == "":
                selected_tcs = selected_test_cases.split(',')

            test_catalog = TestCatalog(self.env, parent_id)
            new_tp = TestPlan(self.env, id, parent_id, title, get_reporter_id(self.req, 'author'), contains_all_int, snapshot_int, selected_tcs)
            new_tp.remote_addr = self.req.remote_addr

            new_tp.insert()
            
            jsdstr = '{"result": "OK", "id": ' + str(id) + '}'

        except:
            self.env.log.error("Error adding test catalog!")
            self.env.log.error(formatExceptionInfo())

            jsdstr = '{"result": "ERROR", "message": "An error occurred while creating the test plan."}'

        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< create_test_plan")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'title': 'in'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def change_title(self):
        self.env.log.debug(">> change_title")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env)
        test_artifact.title = self.title
        
        self.ajax_result = _save_modified_artifact(self.req, self.env, test_artifact, message="Title changed")

        self.env.log.debug("<< change_title")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'description': 'in'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def change_description(self):
        self.env.log.debug(">> change_description")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env)
        test_artifact.description = self.description
        
        self.ajax_result = _save_modified_artifact(self.req, self.env, test_artifact, message="Description changed")

        self.env.log.debug("<< change_description")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'artifact': 'in_out',
                'id': 'in_out',
                'planid': 'in_out',
                'field_name': 'in',
                'field_type': 'in',
                'value': 'in'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def change_custom_field(self):
        self.env.log.debug(">> change_custom_field")

        self.env.log.debug("artifact: '%s', id: '%s'" % (self.artifact, self.id))

        test_artifact = _get_test_artifact(self.artifact, self.id, self.env, self.planid)
        
        if not test_artifact.exists:
            if self.artifact == 'testcaseinplan':
                default_status = TestManagerSystem(self.env).get_default_tc_status()
                test_artifact.set_status(default_status, get_reporter_id(self.req, 'author'))
                test_artifact.insert()
                
                test_artifact = _get_test_artifact(self.artifact, self.id, self.env, self.planid)
            else:
                self.ajax_result = '{"result": "ERROR", "message": "Cannot change a custom field of an inexistent object."}'
                return 'success'
        
        test_artifact[self.field_name] = self.value
        
        result_value = None
        if self.field_type == 'textarea':
            result_value = _get_wiki_page_contents(self.req, self.env, 'TC', self.value)
        elif self.field_type == 'checkbox':
            if self.value == '0':
                result_value = '<i class="fa fa-square-o"></i>'
            else:
                result_value = '<i class="fa fa-check-square-o"></i>'
        
        self.ajax_result = _save_modified_artifact(self.req, self.env, test_artifact, message="Field "+self.field_name+" changed", result_value=result_value)

        self.env.log.debug("<< change_custom_field")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'required_roles': ('TEST_EXECUTE', 'TEST_ADMIN')
        }
    )
    def change_test_case_status(self, test_case_id, test_plan_id, new_status):
        self.env.log.debug(">> change_test_case_status")

        if test_case_id is None or test_plan_id is None:
            raise TracException("Should provide a test case ID and a test plan ID.") 

        GenericClassCacheSystem.clear_cache()

        jsdstr = None
        
        try:
            author = get_reporter_id(self.req, 'author')
            
            test_case_in_plan = TestCaseInPlan(self.env, test_case_id, test_plan_id)
            test_case_in_plan.author = author
            test_case_in_plan.remote_addr = self.req.remote_addr

            test_case_in_plan.set_status(new_status, author)
            
            if not test_case_in_plan.exists:
                test_case_in_plan.insert()
            else:
                test_case_in_plan.save_changes(author, "Status changed")
    
            jsdstr = '{"result": "OK", "id": ' + str(test_case_id) + '}'
    
        except:
            self.env.log.error("Error changing the status of the test case!")
            self.env.log.error(formatExceptionInfo())
    
            jsdstr = '{"result": "ERROR", "message": "An error occurred while changing the status of the test case."}'
            
        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< change_test_case_status")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'template', 'template_name': 'confirm_artifact_move_dialog.html'},
                'no_need': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'artifact_type': 'in_out',
                'artifact_id': 'in_out',
                'new_parent_id': 'in_out',
                'default_outcome': 'out',
                'statuses_by_name': 'out',
                'confirm_data': 'out'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def get_move_artifact_confirmation_dialog(self):
        self.env.log.debug(">> get_move_artifact_confirmation_dialog")

        if self.artifact_type is None or self.artifact_id is None or self.new_parent_id is None:
            raise TracException("Should provide artifact type, id and the new parent id.") 

        GenericClassCacheSystem.clear_cache()

        self.default_outcome = TestManagerSystem(self.env).get_default_tc_status()
        self.statuses_by_name = TestManagerSystem(self.env).get_tc_statuses_by_name()

        self.confirm_data = get_artifact_move_consequences(self.env, self.artifact_type, self.artifact_id, self.new_parent_id)
        self.env.log.debug("Consequences of the move are\n'%s'" % (self.confirm_data,))
        
        GenericClassCacheSystem.clear_cache()

        #if len(self.confirm_data) == 0:
        #    self.ajax_result = ''
        #    
        #    return 'no_need'
        
        self.env.log.debug("<< get_move_artifact_confirmation_dialog")
        
        return 'success'


    @Invocable(
        {
            'results': {
                'success': {'kind': 'json', 'field_name': 'ajax_result'}
            },
            'parameters': {
                'artifact_type': 'in',
                'artifact_id': 'in',
                'new_parent_id': 'in'
            },
            'required_roles': ('TEST_MODIFY', 'TEST_ADMIN')
        }
    )
    def move_artifact(self):
        self.env.log.debug(">> move_artifact")

        if self.artifact_type is None or self.artifact_id is None or self.new_parent_id is None:
            raise TracException("Should provide artifact type, id and the new parent id.") 

        GenericClassCacheSystem.clear_cache()

        jsdstr = None
        
        try:
            destination_catalog = TestCatalog(self.env, self.new_parent_id)
            
            consequences = get_artifact_move_consequences(self.env, self.artifact_type, self.artifact_id, self.new_parent_id)
            self.env.log.debug("Consequences of the move are\n'%s'" % (consequences,))
    
            for tc_title, status, tp_id, tp_name, tp_author, tp_date in consequences:
                self.env.log.debug("Deleting test case in plan with id %s and planid %s" % (self.artifact_id, tp_id))
                tcip = TestCaseInPlan(self.env, self.artifact_id, tp_id)
                tcip.delete_history()
                tcip.delete()

            test_artifact = None
            
            if (self.artifact_type == 'testcase'):
                test_artifact = TestCase(self.env, self.artifact_id)
                
            elif (self.artifact_type == 'testcatalog'):
                test_artifact = TestCatalog(self.env, self.artifact_id)
            
            test_artifact.author = get_reporter_id(self.req, 'author')
            test_artifact.remote_addr = self.req.remote_addr

            test_artifact.move_to(destination_catalog)

            jsdstr = '{"result": "OK"}'
    
        except:
            self.env.log.error("Error moving the test artifact!")
            self.env.log.error(formatExceptionInfo())
    
            jsdstr = '{"result": "ERROR", "message": "An error occurred while moving the test artifact."}'
            
        self.ajax_result = jsdstr

        GenericClassCacheSystem.clear_cache()

        self.env.log.debug("<< move_artifact")
        
        return 'success'

    def prepare_custom_fields(self, artifact_type):
        self.env.log.debug(">> prepare_custom_fields")
        
        tmmodelprovider = GenericClassModelProvider(self.env)
        self.custom_fields = tmmodelprovider.get_custom_fields_for_realm(artifact_type)
        
        self.custom_field_values = {}
        self.custom_field_values_markup = {}
    
        for f in self.custom_fields:
            field_name = f['name']
            field_value = self.obj[field_name]
            field_type = f['type']
            
            if field_type == 'textarea':
                if field_value is not None:
                    if ('format' in f) and f['format'] == 'wiki':
                        self.custom_field_values_markup[field_name] = _get_wiki_page_contents(self.req, self.env, 'TC', field_value)
                    else:
                        field_value = html_escape(field_value)
                else:
                    self.custom_field_values_markup[field_name] = ''
                    field_value = ''

            else:
                if field_value is not None:
                    field_value = html_escape(field_value)
                    
            self.custom_field_values[field_name] = field_value

        self.env.log.debug("<< prepare_custom_fields")

##########################################################################################################

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
            self.wiki_contents = _get_wiki_page_contents(req, test_case['page_name'], test_case.description)
                
            template = 'test_case.html'

        elif artifact == 'test_catalog_details':
            self.test_catalog = TestManagerSystem(self.env).get_test_catalog_details_data_model(test_catalog = test_catalog, include_status = include_status, test_plan = test_plan)
            self.wiki_contents = _get_wiki_page_contents(req, test_catalog['page_name'], test_catalog.description)
            
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

##########################################################################################################


def get_artifact_move_consequences(env, artifact_type, artifact_id, new_parent_id):
    
    result = []
    
    if (artifact_type == 'testcase'):
        test_artifact = TestCase(env, artifact_id)
    
        # Calculate path from the destination catalog to the root
        destination_path_to_root = []
        parent_catalog = TestCatalog(env, new_parent_id).get_enclosing_catalog();
        while parent_catalog is not None:
            destination_path_to_root.append(parent_catalog['id'])
            
            parent_catalog = parent_catalog.get_enclosing_catalog()
        
        # Calculate path from the moved test case to the root
        parent_catalog = test_artifact.get_enclosing_catalog();
        while parent_catalog is not None:
            if parent_catalog['id'] not in destination_path_to_root:
                # The test case is being moved to a catalog that does not 
                # have this particular catalog in the path to its root.
                # This means that any test plan defined for this particular
                # catalog will not have the test case in them anymore.
                for test_plan in parent_catalog.list_testplans():
                    tcip = TestCaseInPlan(env, artifact_id, test_plan['id'])
                    if tcip.exists:
                        for ts, author, status in tcip.list_history():
                            result.append(
                                    [test_artifact.title, status, test_plan['id'], test_plan['name'], author, ts]
                                )
            
            parent_catalog = parent_catalog.get_enclosing_catalog()
            
    elif (artifact_type == 'testcatalog'):
        test_artifact = TestCatalog(env, artifact_id)
        
        for test_case in test_artifact.list_testcases(deep = True):
            result.extend(get_artifact_move_consequences(env, 'testcase', test_case['id'], new_parent_id))
    
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


def _can_view(req):
    return req.perm.has_permission('TEST_VIEW') or req.perm.has_permission('TEST_ADMIN')

def _can_modify(req):
    return req.perm.has_permission('TEST_MODIFY') or req.perm.has_permission('TEST_ADMIN')

def _can_execute(req):
    return req.perm.has_permission('TEST_EXECUTE') or req.perm.has_permission('TEST_ADMIN')

def _can_delete(req):
    return req.perm.has_permission('TEST_DELETE') or req.perm.has_permission('TEST_ADMIN')

def _can_admin_plans(req):
    return req.perm.has_permission('TEST_PLAN_ADMIN') or req.perm.has_permission('TEST_ADMIN')

def _can_admin(req):
    return req.perm.has_permission('TEST_ADMIN')


def _get_wiki_page_contents(req, env, page_name, markup):
    context = web_context(req)
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
    
def _get_test_case_in_plan(test_case_id, planid, env):
    test_case_in_plan = None
    if test_case_id is not None and planid is not None:
        test_case_in_plan = TestCaseInPlan(env, test_case_id, planid)

    return test_case_in_plan
    
def _get_test_artifact(artifact_type, id, env, planid = '-1'):
    if artifact_type is None:
        raise TracError("Artifact parameter must not be None")

    result = None
    if artifact_type == 'testcase':
        result = _get_test_case(id, env)
        
    elif artifact_type == 'catalog':
        result = _get_test_catalog(id, env)
    
    elif artifact_type == 'testplan':
        result = _get_test_plan(id, env)
    
    elif artifact_type == 'testcaseinplan':
        result = _get_test_case_in_plan(id, planid, env)
    
    else:
        raise TracError("Unrecognized artifact type '%s'" % (artifact_type,))

    return result

def _save_modified_artifact(req, env, test_artifact, message="Property changed", result_value=None):

    jsdstr = {}
    
    try:
        author = get_reporter_id(req, 'author')
        test_artifact.author = author
        test_artifact.remote_addr = req.remote_addr

        test_artifact.save_changes(author, message)

        jsdstr['result'] = "OK"
        jsdstr['id'] = str(test_artifact['id'])
        
        if result_value is not None:
            jsdstr['value'] = result_value

    except:
        env.log.error("Error saving changed object!")
        env.log.error(formatExceptionInfo())

        jsdstr['result'] = "ERROR"
        jsdstr['message'] = "An error occurred while saving the changes."

    io = StringIO()
    json.dump(jsdstr, io)
        
    return io.getvalue()

def _retrieve_session(env, req):
    attributes = {}
    
    attributes['artifact_type'] = None
    attributes['artifact_id'] = None
    attributes['artifact_planid'] = None
    
    curr_session = Session(env, req)
    
    if 'tm_curr_artifact_type' in curr_session and curr_session['tm_curr_artifact_type'] != 'None':
        attributes['artifact_type'] = curr_session['tm_curr_artifact_type']
        
    if 'tm_curr_artifact_id' in curr_session and curr_session['tm_curr_artifact_id'] != 'None':
        attributes['artifact_id'] = curr_session['tm_curr_artifact_id']

    if 'tm_curr_artifact_planid' in curr_session and curr_session['tm_curr_artifact_planid'] != 'None':
        attributes['artifact_planid'] = curr_session['tm_curr_artifact_planid']

    env.log.debug('retrieved session artifact_type: %s' % (attributes['artifact_type'],))
    env.log.debug('retrieved session artifact_id: %s' % (attributes['artifact_id'],))
    env.log.debug('retrieved session artifact_planid: %s' % (attributes['artifact_planid'],))
    
    return attributes
    
def _save_session(env, req, attributes):
    curr_session = Session(env, req)
    
    if 'artifact_type' in attributes:
        curr_session.set('tm_curr_artifact_type', attributes['artifact_type'])
        env.log.debug('saved session artifact_type: %s' % (attributes['artifact_type'],))
    else:
        curr_session.pop('tm_curr_artifact_type', None)
        env.log.debug('removed session artifact_type')

    if 'artifact_id' in attributes:
        curr_session.set('tm_curr_artifact_id', attributes['artifact_id'])
        env.log.debug('saved session artifact_id: %s' % (attributes['artifact_id'],))
    else:
        curr_session.pop('tm_curr_artifact_id', None)
        env.log.debug('removed session artifact_id')

    if 'artifact_planid' in attributes:
        curr_session.set('tm_curr_artifact_planid', attributes['artifact_planid'])
        env.log.debug('saved session artifact_planid: %s' % (attributes['artifact_planid'],))
    else:
        curr_session.pop('tm_curr_artifact_planid', None)
        env.log.debug('removed session artifact_planid')

    curr_session.save()

