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

import csv
import json
import os
import pkg_resources
import re
import shutil
import sys
import time
import traceback

from datetime import datetime
from operator import itemgetter
from StringIO import StringIO

from trac.core import *
from trac.mimeview.api import Context
from trac.perm import IPermissionRequestor, PermissionError
from trac.resource import Resource, IResourceManager, render_resource_link, get_resource_url
from trac.util import get_reporter_id, format_datetime, format_date
from trac.util.datefmt import utc
from trac.web.api import IRequestHandler
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider, add_notice, add_warning, add_stylesheet
from trac.web.href import Href
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser

from genshi import HTML
from genshi.builder import tag
from genshi.filters.transform import Transformer

from tracgenericclass.cache import GenericClassCacheSystem
from tracgenericclass.model import GenericClassModelProvider
from tracgenericclass.util import *

from testmanager.beans import *
from testmanager.util import *
from testmanager.admin import get_all_table_columns_for_object
from testmanager.api import TestManagerSystem
from testmanager.model import TestCatalog, TestCase, TestCaseInPlan, TestPlan, TestManagerModelProvider

try:
    from testmanager.api import _, tag_, N_
except ImportError:
    from trac.util.translation import _, N_
    tag_ = _

class TestManagerView(Component):
    """Implement the test manager's view component, including the /testview and /testajax handlers."""
    
    implements(IRequestHandler)
    
    context = None
    
    formatter = None


    # IRequestHandler methods

    def match_request(self, req):
        return (req.path_info.startswith('/testview') or req.path_info.startswith('/testajax')) and (('TEST_VIEW' in req.perm or 'TEST_ADMIN' in req.perm))

    def process_request(self, req):

        type_ = req.args.get('type', '')

        self.context = Context.from_request(req, Resource('testmanager'))
        self.formatter = Formatter(self.env, self.context)

        author = get_reporter_id(req, 'author')
        remote_addr = req.remote_addr

        mode = req.args.get('view_type', Constants(self.env).default_view_mode)
        fulldetails = req.args.get('fulldetails', 'False')

        use_template = True
        template = 'testmanager.html'
        data = {}

        href = Href(req.base_path)
        data['base_url'] = href()

        self.env.log.info("process_request: %s" % (req.path_info,))
        
        GenericClassCacheSystem.clear_cache()

        if req.path_info.startswith('/testview'):
            if not req.perm.has_permission('TEST_VIEW') and not req.perm.has_permission('TEST_ADMIN'):
                raise PermissionError('TEST_VIEW', None, self.env)

            data['mode'] = mode
            data['fulldetails'] = fulldetails

        elif req.path_info.startswith('/testajax'):
            if not req.perm.has_permission('TEST_VIEW') and not req.perm.has_permission('TEST_ADMIN'):
                raise PermissionError('TEST_VIEW', None, self.env)

            parent_id = req.args.get('parent_id', None)
            artifact = req.args.get('artifact', None)
            
            data['parent_id'] = parent_id
            data['artifact'] = artifact

            if (type_ == 'load_dialog'):
                template = req.args.get('dialog', 'error_no_dialog.html')
                
                if (artifact == 'catalog'):
                    id = req.args.get('id', None)
                    data['id'] = id

                    test_catalog = TestCatalog(self.env, id)
                    data['title'] = test_catalog['id']

                elif (artifact == 'testcase'):
                    id = req.args.get('id', None)
                    data['id'] = id

                    test_case = TestCatalog(self.env, id)
                    data['title'] = test_case['id']

            elif (type_ == 'create'):
                test_manager_system = TestManagerSystem(self.env)
                
                req.perm.require('TEST_MODIFY')

                self.env.log.debug("Parent id = %s" % parent_id)
                
                title = req.args.get('title')

                id = test_manager_system.get_next_id(artifact)

                use_template = False
                
                jsdstr = ''
                
                if (artifact == 'catalog'):
                    pagename = 'TC_TT'+str(id)

                    try:
                        # Add template if exists...
                        new_content = test_manager_system.get_default_tcat_template()
                        
                        new_tc = TestCatalog(self.env, id, pagename, parent_id, title, new_content)
                        new_tc.author = author
                        new_tc.remote_addr = remote_addr
                        # This also creates the Wiki page
                        new_tc.insert()

                        jsdstr = '{"result": "OK", "id": ' + str(id) + '}'
                        
                    except:
                        self.env.log.error("Error adding test catalog!")
                        self.env.log.error(formatExceptionInfo())

                        jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test catalog."}'

                elif (artifact == 'testcase'):
                    pagename = 'TC_TC'+str(id)

                    try:
                        parent_tcat = TestCatalog(self.env, parent_id)

                        # Add template if exists...
                        new_content = test_manager_system.get_tc_template(parent_tcat['page_name'])

                        new_tc = TestCase(self.env, id, pagename, parent_id, title, new_content)
                        new_tc.author = author
                        new_tc.remote_addr = remote_addr
                        # This also creates the Wiki page
                        new_tc.insert()

                        jsdstr = '{"result": "OK", "id": ' + str(id) + '}'
                        
                    except:
                        self.env.log.error("Error adding test case!")
                        self.env.log.error(formatExceptionInfo())

                        jsdstr = '{"result": "ERROR", "message": "An error occurred while adding the test case."}'

            elif (type_ == 'edit_title'):
                req.perm.require('TEST_MODIFY')

                id = req.args.get('id', None)
                self.env.log.debug("id = %s" % id)
                
                title = req.args.get('title')

                try:
                    if (artifact == 'catalog'):
                        test_object = TestCatalog(self.env, id)

                    elif (artifact == 'testcase'):
                        test_object = TestCase(self.env, id)

                    test_object['title'] = title
                    test_object.author = author
                    test_object.remote_addr = remote_addr
                    test_object.save_changes(author, "Changed title")

                    jsdstr = '{"result": "OK", "id": ' + str(id) + '}'
                    
                except:
                    self.env.log.error("Error changing test object title!")
                    self.env.log.error(formatExceptionInfo())

                    jsdstr = '{"result": "ERROR", "message": "An error occurred while changing the title."}'

            else:
                artifact = req.args.get('artifact', None)

                test_catalog_id = req.args.get('catid', None)
                test_case_id = req.args.get('tcid', None)
                test_plan_id = req.args.get('planid', None)

                fulldetails = req.args.get('fulldetails', 'False')

                show_all = test_catalog_id is None and test_case_id is None and test_plan_id is None
                include_status = test_plan_id is not None

                data['test_catalog_id'] = test_catalog_id
                data['test_case_id'] = test_case_id
                data['test_plan_id'] = test_plan_id

                self.env.log.debug("test_catalog_id: '%s', test_case_id: '%s', test_plan_id: '%s'" % (test_catalog_id, test_case_id, test_plan_id))

                test_plan = None
                if test_plan_id is not None:
                    test_plan = TestPlan(self.env, test_plan_id, test_catalog_id)
                
                    if not test_plan.exists:
                        raise TracException("The specified test plan with id '%s' does not exist." % (test_plan_id,)) 

                test_catalog = None
                if test_catalog_id is not None:
                    test_catalog = TestCatalog(self.env, test_catalog_id)
                    
                    if not test_catalog.exists:
                        raise TracException("The specified test catalog with id '%s' does not exist." % (test_catalog_id,)) 

                test_case = None
                if test_case_id is not None:
                    test_case = TestCase(self.env, test_case_id)
                    
                    if not test_case.exists:
                        raise TracException("The specified test case with id '%s' does not exist." % (test_case_id,)) 

                if artifact == 'breadcrumbs':
                    data['breadcrumbs'] = self._get_breadcrumbs(test_catalog = test_catalog, test_case = test_case, test_plan = test_plan)
                    
                    template = 'breadcrumbs.html'
                    
                elif artifact == 'test_case_details':
                    data['test_case'] = TestManagerSystem(self.env).get_test_case_data_model(test_case = test_case, include_status = include_status, test_plan = test_plan)
                    data['wiki_contents'] = self._get_wiki_page_contents(req, test_case['page_name'], test_case.description)
                        
                    template = 'test_case.html'

                elif artifact == 'test_catalog_details':
                    data['test_catalog'] = TestManagerSystem(self.env).get_test_catalog_details_data_model(test_catalog = test_catalog, include_status = include_status, test_plan = test_plan)
                    data['wiki_contents'] = self._get_wiki_page_contents(req, test_catalog['page_name'], test_catalog.description)
                    
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

        GenericClassCacheSystem.clear_cache()

        if use_template:
            return template, data, None
        else:
            if isinstance(jsdstr, unicode): 
                jsdstr = jsdstr.encode('utf-8') 

            req.send_header("Content-Length", len(jsdstr))
            req.write(jsdstr)
            return

    def _get_breadcrumbs(self, test_catalog = None, test_case = None, test_plan = None):
        breadcrumb = []
        
        self.env.log.debug("Building breadcrumbs starting with catalog ID %s" % (test_catalog['id'],))
        
        test_plan_catalog_id = -1
        if test_plan is not None:
            test_plan_catalog_id = test_plan['catid']
        
        # Manage leaf test case, if present
        if test_case is not None:
            curr_step = BreadcrumbBean(test_catalog = test_catalog, test_case = test_case, test_plan = test_plan)
            breadcrumb.insert(0, curr_step)
        
        # Manage test catalogs, starting with the last one and navigating parent-wide
        while True:
            if test_catalog is None or not test_catalog.exist or test_catalog['id'] == '-1':
                curr_step = BreadcrumbBean()
                breadcrumb.insert(0, curr_step)
                
                break
            else:
                curr_step = BreadcrumbBean(test_catalog = test_catalog, test_plan = test_plan)
                breadcrumb.insert(0, curr_step)
            
                # If the catalog to which the test plan is tied has been reached,
                # must not go further, because higher catalogs are not in the scope
                # of the test plan
                if test_catalog['id'] == test_plan_catalog_id:
                    break
                
                test_catalog = TestCatalog(self.env, test_catalog['parent_id'])
        
        return breadcrumb


    def _get_wiki_markup(wiki_text):
        result = '<div class="tm_wiki">'
        
        wikidom = WikiParser(self.env).parse(wiki_text)
        out = StringIO()
        f = self.formatter
        f.reset(wikidom)
        f.format(wikidom, out, False)
        description = out.getvalue()

        result += description
        
        result += '</div>'

        return result

    def _get_test_catalog_node_markup(test_catalog_bean):
        result = ''
        
        result += '<ul class="tm_test_catalog_node %s" data-test_catalog_id="%s" data-test_plan_id="%s">' % (('', 'tm_expandable')[test_catalog_bean.is_expandable()], test_catalog_bean.get_test_catalog_id(), test_catalog_bean.get_test_plan_id())
        
        for sub_catalog_bean in test_catalog_bean.sub_catalogs_iterator():
            result += self._get_test_catalog_node_markup(sub_catalog_bean)
            
        for test_case_bean in test_catalog_bean.test_cases_iterator():
            result += self._get_test_case_node_markup(test_case_bean)
        
        result += '</ul>'

    def _get_test_case_node_markup(test_case_bean):
        result = '<li class="tm_test_case" data-test_case_id="%s" data-test_plan_id="%s">' % (test_case_bean.get_test_case_id(), test_case_bean.get_test_plan_id())
        
        result += '</li>'

    def _get_wiki_page_contents(self, req, page_name, markup):
        context = Context.from_request(req, 'wiki', page_name)
        formatter = Formatter(self.env, context)
        wikidom = WikiParser(self.env).parse(markup)
        out = StringIO()
        f = Formatter(self.env, context)
        f.reset(wikidom)
        f.format(wikidom, out, False)
        #result = re.sub(self.DOUBLE_QUOTES, "\"\"", out.getvalue())

        result = out.getvalue()
        
        return result

#<ul style="list-style: none;"><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_1"><span onclick="toggle('b_1')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_1" onmouseover="underlineLink('l_1')" onmouseout="removeUnderlineLink('l_1')" onclick="window.location='TC_TT1'" title="Open" style="color: black; text-decoration: none; background-color: white;">Ciao core de mamma</span></span><span style="color: gray;">&nbsp;(9)</span><ul id="b_1_list" style="display:none;list-style: none; margin-bottom: 0px;"><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_3"><span onclick="toggle('b_3')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_3" onmouseover="underlineLink('l_3')" onmouseout="removeUnderlineLink('l_3')" onclick="window.location='TC_TT13'" title="Open">Ciao_core</span></span><span style="color: gray;">&nbsp;(1)</span><ul id="b_3_list" style="display:none;list-style: none; margin-bottom: 0px;"><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC11" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC11', true)" onmouseout="hidePencil('pencilIconTC_TC11', false)"><a href="TC_TC11?a=a">Ciao_core&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC11?action=edit" id="pencilIconTC_TC11"></a></span></span></li></ul></li><li style="font-weight: normal"><span name="nope" style="cursor: pointer" id="b_5"><span onclick="toggle('b_5')"><img class="iconElement" src="../chrome/testmanager/images/empty.png"></span><span id="l_5" onmouseover="underlineLink('l_5')" onmouseout="removeUnderlineLink('l_5')" onclick="window.location='TC_TT7'" title="Open">Test catalog 01.01.01</span></span><span style="color: gray;">&nbsp;(0)</span><ul id="b_5_list" style="display:none;list-style: none; margin-bottom: 0px;"></ul></li><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_7"><span onclick="toggle('b_7')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_7" onmouseover="underlineLink('l_7')" onmouseout="removeUnderlineLink('l_7')" onclick="window.location='TC_TT6'" title="Open">Test catalog 01.01.02</span></span><span style="color: gray;">&nbsp;(1)</span><ul id="b_7_list" style="display:none;list-style: none; margin-bottom: 0px;"><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC10" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC10', true)" onmouseout="hidePencil('pencilIconTC_TC10', false)"><a href="TC_TC10?a=a">Test case 01.01.02.01&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC10?action=edit" id="pencilIconTC_TC10"></a></span></span></li></ul></li><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_9"><span onclick="toggle('b_9')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_9" onmouseover="underlineLink('l_9')" onmouseout="removeUnderlineLink('l_9')" onclick="window.location='TC_TT8'" title="Open">Test catalog 01.01.03</span></span><span style="color: gray;">&nbsp;(4)</span><ul id="b_9_list" style="display:none;list-style: none; margin-bottom: 0px;"><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_11"><span onclick="toggle('b_11')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_11" onmouseover="underlineLink('l_11')" onmouseout="removeUnderlineLink('l_11')" onclick="window.location='TC_TT14'" title="Open">fewfewewefw</span></span><span style="color: gray;">&nbsp;(2)</span><ul id="b_11_list" style="display:none;list-style: none; margin-bottom: 0px;"><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC12" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC12', true)" onmouseout="hidePencil('pencilIconTC_TC12', false)"><a href="TC_TC12?a=a">fweewfewf&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC12?action=edit" id="pencilIconTC_TC12"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC13" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC13', true)" onmouseout="hidePencil('pencilIconTC_TC13', false)"><a href="TC_TC13?a=a">fweewfewfqweqe&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC13?action=edit" id="pencilIconTC_TC13"></a></span></span></li></ul></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC8" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC8', true)" onmouseout="hidePencil('pencilIconTC_TC8', false)"><a href="TC_TC8?a=a">Test case 01.01.03.01&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC8?action=edit" id="pencilIconTC_TC8"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC9" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC9', true)" onmouseout="hidePencil('pencilIconTC_TC9', false)"><a href="TC_TC9?a=a">Test case 01.01.03.02&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC9?action=edit" id="pencilIconTC_TC9"></a></span></span></li></ul></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC5" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC5', true)" onmouseout="hidePencil('pencilIconTC_TC5', false)"><a href="TC_TC5?a=a">Test&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC5?action=edit" id="pencilIconTC_TC5"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC6" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC6', true)" onmouseout="hidePencil('pencilIconTC_TC6', false)"><a href="TC_TC6?a=a">Test case 01.02&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC6?action=edit" id="pencilIconTC_TC6"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC7" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC7', true)" onmouseout="hidePencil('pencilIconTC_TC7', false)"><a href="TC_TC7?a=a">Test case 01.03&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC7?action=edit" id="pencilIconTC_TC7"></a></span></span></li></ul></li><li style="font-weight: normal"><span name="toggable" style="cursor: pointer" id="b_13"><span onclick="toggle('b_13')"><img class="iconElement" src="../chrome/testmanager/images/plus.png"></span><span id="l_13" onmouseover="underlineLink('l_13')" onmouseout="removeUnderlineLink('l_13')" onclick="window.location='TC_TT2'" title="Open" style="color: black; text-decoration: none; background-color: white;">Test catalog 01.02</span></span><span style="color: gray;">&nbsp;(3)</span><ul id="b_13_list" style="display:none;list-style: none; margin-bottom: 0px;"><li style="font-weight: normal"><span name="nope" style="cursor: pointer" id="b_15"><span onclick="toggle('b_15')"><img class="iconElement" src="../chrome/testmanager/images/empty.png"></span><span id="l_15" onmouseover="underlineLink('l_15')" onmouseout="removeUnderlineLink('l_15')" onclick="window.location='TC_TT3'" title="Open">Test catalog 01.01.02</span></span><span style="color: gray;">&nbsp;(0)</span><ul id="b_15_list" style="display:none;list-style: none; margin-bottom: 0px;"></ul></li><li style="font-weight: normal"><span name="nope" style="cursor: pointer" id="b_17"><span onclick="toggle('b_17')"><img class="iconElement" src="../chrome/testmanager/images/empty.png"></span><span id="l_17" onmouseover="underlineLink('l_17')" onmouseout="removeUnderlineLink('l_17')" onclick="window.location='TC_TT4'" title="Open">Test catalog 01.01.03</span></span><span style="color: gray;">&nbsp;(0)</span><ul id="b_17_list" style="display:none;list-style: none; margin-bottom: 0px;"></ul></li><li style="font-weight: normal"><span name="nope" style="cursor: pointer" id="b_19"><span onclick="toggle('b_19')"><img class="iconElement" src="../chrome/testmanager/images/empty.png"></span><span id="l_19" onmouseover="underlineLink('l_19')" onmouseout="removeUnderlineLink('l_19')" onclick="window.location='TC_TT5'" title="Open">Test catalog 01.01.04</span></span><span style="color: gray;">&nbsp;(0)</span><ul id="b_19_list" style="display:none;list-style: none; margin-bottom: 0px;"></ul></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC2" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC2', true)" onmouseout="hidePencil('pencilIconTC_TC2', false)"><a href="TC_TC2?a=a">Test case 01.01.01&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC2?action=edit" id="pencilIconTC_TC2"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC3" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC3', true)" onmouseout="hidePencil('pencilIconTC_TC3', false)"><a href="TC_TC3?a=a">Test case 01.01.02&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC3?action=edit" id="pencilIconTC_TC3"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC4" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC4', true)" onmouseout="hidePencil('pencilIconTC_TC4', false)"><a href="TC_TC4?a=a">Test case 01.01.03&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC4?action=edit" id="pencilIconTC_TC4"></a></span></span></li></ul></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC0" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC0', true)" onmouseout="hidePencil('pencilIconTC_TC0', false)"><a href="TC_TC0?a=a">Test case 01.01&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC0?action=edit" id="pencilIconTC_TC0"></a></span></span></li><li name="tc_node" style="font-weight: normal; margin-left: 10px;"><input name="select_tc_checkbox" value="TC_TC1" type="checkbox" style="display: none;float: left; position: relative; top: 3px;"><span onmouseover="showPencil('pencilIconTC_TC1', true)" onmouseout="hidePencil('pencilIconTC_TC1', false)"><a href="TC_TC1?a=a">Test case 01.02&nbsp;</a><span><a class="rightIcon" style="display: none;" title="Edit the Test Case" href="TC_TC1?action=edit" id="pencilIconTC_TC1"></a></span></span></li></ul>

