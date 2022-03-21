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

import logging
import json
import sys
import traceback

import cli.app
import cli.log

import xmlrpclib 

class SyntaxErrorException(Exception):
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        if self.value is not None:
            return repr(self.value)
        else:
            return ''

class RpcConnection():

    app = None

    def __init__(self, app):
        self.app = app
        
        authentication_separator = ''
        username_separator = ''

        username = ''
        if app.params.user is not None and app.params.user != '':
            username = app.params.user
            authentication_separator = '@'
            self.app.log.info("Input username='%s'" % username)

        password = ''
        if app.params.password is not None and app.params.password != '':
            password = app.params.password
            username_separator = ':'
            self.app.log.info("Input password='%s'" % password)

        hostname = ''
        if app.params.hostname is not None and app.params.hostname != '':
            hostname = app.params.hostname
            self.app.log.info("Input hostname='%s'" % hostname)

        port = ''
        if app.params.port is not None and app.params.port != '':
            port = app.params.port
            self.app.log.info("Input port='%s'" % port)

        project = ''
        if app.params.project is not None and app.params.project != '':
            project = app.params.project
            self.app.log.info("Input project='%s'" % project)

        context_root = '/rpc'
        if password != '':
            context_root = '/login/rpc'

        self.app.log.info("Context root='%s'" % context_root)
            
        self.trac_project_url = "http://%(username)s%(username_separator)s%(password)s%(authentication_separator)s%(hostname)s:%(port)s/%(project)s%(context_root)s" % \
            {'username': username, 'password': password, 
             'username_separator': username_separator, 'authentication_separator': authentication_separator, 
             'hostname': hostname, 'port': port, 'project': project,
             'context_root': context_root}
        
        self.app.log.info("Connection URL: %s" % self.trac_project_url)
        
        self.server = xmlrpclib.ServerProxy(self.trac_project_url)

    def createTestCatalog(self, parent_catalog_id, title, description):
        """ Creates a new test catalog, in the parent catalog specified, 
        with the specified title and description.
        To create a root catalog, specify '' as the parent catalog.
        Returns the generated object ID, or '-1' if an error occurs. """
        
        try:
            print self.server.testmanager.createTestCatalog(parent_catalog_id, title, description)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error adding test catalog with title '%s' in catalog with ID %s!" % (title, parent_catalog_id))
        
    def createTestCase(self, catalog_id, title, description):
        """ Creates a new test case, in the catalog specified, with the 
        specified title and description.
        Returns the generated object ID, or '-1' if an error occurs. """
        
        try:
            print self.server.testmanager.createTestCase(catalog_id, title, description)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error adding test case with title '%s' in catalog with ID %s!" % (title, catalog_id))
        
    def createTestPlan(self, catalog_id, name):
        """ Creates a new test plan, on the catalog specified, with the 
        specified name.
        Returns the generated object ID, or '-1' if an error occurs. """
        
        try:
            print self.server.testmanager.createTestPlan(catalog_id, name)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error adding test plan with name '%s' for catalog with ID %s!" % (name, catalog_id))

    def deleteTestObject(self, objtype, id):
        """ Deletes the test object of the specified type identified
        by the given id. 
        Returns True if successful, False otherwise. """
        
        try:
            print self.server.testmanager.deleteTestObject(objtype, id)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error deleting test object of type %s with ID %s." % (objtype, id))

    def modifyTestObject(self, objtype, id, attributes={}):
        """ Modifies the test object of the specified type identified
        by the given id.
        Returns True if successful, False otherwise. """

        try:
            print self.server.testmanager.modifyTestObject(objtype, id, attributes)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error modifying test object of type %s with ID %s." % (objtype, id))

    def setTestCaseStatus(self, testcase_id, plan_id, status):
        """ Sets the test case status.
        Returns True if successful, False otherwise. """
        
        try:
            print self.server.testmanager.setTestCaseStatus(testcase_id, plan_id, status)
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error setting the test case status with ID %s on plan %s to %s!" % (testcase_id, plan_id, status))
            
    def getTestCatalog(self, catalog_id):
        """ Returns the catalog properties.
        The result is in the form, all strings:
        (wiki_page_name, title, description) """
        
        try:
            tc = self.server.testmanager.getTestCatalog(catalog_id)
            print '{"page_name": "%(page_name)s", "parent_id": %(parent_id)s, "title": %(title)s, "description": %(description)s}\n' % \
                {'page_name': tc[0], 'parent_id': tc[1], 'title': json.dumps(tc[2]), 'description': json.dumps(tc[3])}
            
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error getting the test catalog with ID %s!" % catalog_id)
            
    def getTestCase(self, testcase_id, plan_id=''):
        """ Returns the test case properties.
        If plan_id is provided, also the status of the test case in the
        plan will be returned.
        Each result is in the form, all strings:
            If plan_id is NOT provided:
                (wiki_page_name, title, description)
            If plan_id is provided:
                (wiki_page_name, title, description, status) """
        
        try:
            if plan_id is None or plan_id == '':
                tc = self.server.testmanager.getTestCase(testcase_id)
                print '{"page_name": "%(page_name)s", "parent_id": %(parent_id)s, "title": %(title)s, "description": %(description)s}\n' % \
                    {'page_name': tc[0], 'parent_id': tc[1], 'title': json.dumps(tc[2]), 'description': json.dumps(tc[3])}
            else:
                tc = self.server.testmanager.getTestCase(testcase_id, plan_id)
                print '{"page_name": "%(page_name)s", "parent_id": %(parent_id)s, "title": %(title)s, "description": %(description)s, "status": "%(status)s"}\n' % \
                    {'page_name': tc[0], 'parent_id': tc[1], 'title': json.dumps(tc[2]), 'description': json.dumps(tc[3]), 'status': tc[4]}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error getting the test case with ID %s!" % testcase_id)
            
    def getTestPlan(self, plan_id):
        """ Returns the test plan properties.
        The result is in the form, all strings:
        (wiki_page_name, name) """
        
        try:
            tp = self.server.testmanager.getTestPlan(plan_id)
            print '{"page_name": "%(page_name)s", "name": %(name)s}\n' % \
                {'page_name': tp[0], 'name': json.dumps(tp[1])}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error getting the test plan with ID %s." % plan_id)
            
    def listRootCatalogs(self):
        """ Returns a iterator over the root-level test catalogs.
        Each result is in the form, all strings:
        (test_catalog_id, wiki_page_name, title, description) """
        
        try:
            for tc in self.server.testmanager.listRootCatalogs():
                print '{"id": %(id)s, "page_name": "%(page_name)s", "title": %(title)s, "description": %(description)s}\n' % \
                    {'id': tc[0], 'page_name': tc[1], 'title': json.dumps(tc[2]), 'description': json.dumps(tc[3])}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error listing the root-level test catalogs!")

    def listSubCatalogs(self, catalog_id):
        """ Returns a iterator over the direct sub-catalogs of the specified 
        catalog.
        Each result is in the form, all strings:
        (test_catalog_id, wiki_page_name, title, description) """
        
        try:
            for tc in self.server.testmanager.listSubCatalogs(catalog_id):
                print '{"id": %(id)s, "page_name": "%(page_name)s", "parent_id": %(parent_id)s, "title": %(title)s, "description": %(description)s}\n' % \
                    {'id': tc[0], 'page_name': tc[1], 'parent_id': tc[2], 'title': json.dumps(tc[3]), 'description': json.dumps(tc[4])}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error listing the test catalogs!")

    def listTestPlans(self, catalog_id):
        """ Returns a iterator over the test plans associated 
        to the specified catalog.
        Each result is in the form, all strings:
        (testplan_id, name) """
        
        try:
            for tp in self.server.testmanager.listTestPlans(catalog_id):
                print '{"id": %(id)s, "name": %(name)s}\n' % \
                    {'id': tp[0], 'name': json.dumps(tp[1])}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error listing the test plans!")

    def listTestCases(self, catalog_id, plan_id=''):
        """ Returns a iterator over the test cases directly in the 
        specified catalog (no sub-catalogs).
        If plan_id is provided, also the status of the test case in the
        plan will be returned.
        Each result is in the form, all strings:
            If plan_id is NOT provided:
                (testcase_id, wiki_page_name, title, description)
            If plan_id is provided:
                (testcase_id, wiki_page_name, status) """
        
        try:
            if plan_id is None or plan_id == '':
                for tc in self.server.testmanager.listTestCases(catalog_id):
                    print '{"id": %(id)s, "page_name": "%(page_name)s", "parent_id": %(parent_id)s, "title": %(title)s, "description": %(description)s}\n' % \
                        {'id': tc[0], 'page_name': tc[1], 'parent_id': tc[2], 'title': json.dumps(tc[3]), 'description': json.dumps(tc[4])}
            else:
                for tc in self.server.testmanager.listTestCases(catalog_id, plan_id):
                    print '{"id": %(id)s, "page_name": "%(page_name)s", "parent_id": %(parent_id)s, "status": "%(status)s"}\n' % \
                        {'id': tc[0], 'page_name': tc[1], 'parent_id': tc[2], 'status': tc[3]}
        except:
            self.app.log.error(formatExceptionInfo())
            self.app.log.error("Error listing the test cases in the catalog with ID %s!" % catalog_id)


@cli.log.LoggingApp
def testmanager(app):
    app.log.info("TestManager for Trac CLI")

    retcode = 0
        
    try:
        rpc = RpcConnection(app)
        
        command = None
        if app.params.command is not None and app.params.command != '':
            command = app.params.command
        
        catalog = None
        if app.params.catalog is not None and app.params.catalog != '':
            catalog = app.params.catalog

        testcase = None
        if app.params.testcase is not None and app.params.testcase != '':
            testcase = app.params.testcase

        plan = None
        if app.params.plan is not None and app.params.plan != '':
            plan = app.params.plan

        parent = None
        if app.params.parent is not None and app.params.parent != '':
            parent = app.params.parent

        objecttype = None
        if app.params.objecttype is not None and app.params.objecttype != '':
            objecttype = app.params.objecttype
        
        name = None
        if app.params.name is not None and app.params.name != '':
            name = app.params.name
        
        description = None
        if app.params.description is not None and app.params.description != '':
            description = app.params.description
        
        status = None
        if app.params.status is not None and app.params.status != '':
            status = app.params.status
        
        attribute = None
        if app.params.attribute is not None and app.params.attribute != '':
            attribute = app.params.attribute
        
        value = None
        if app.params.value is not None and app.params.value != '':
            value = app.params.value
        
        if command != None:
            _check_command_parameter(command)
            
        if command == 'list':
            _check_objecttype_parameter(objecttype)

            _check_catalog_parameter(catalog)

            if objecttype == 'testcatalog':
                if catalog == '-1':
                    rpc.listRootCatalogs()
                else:
                    rpc.listSubCatalogs(catalog)
            
            elif objecttype == 'testcase':
                rpc.listTestCases(catalog, plan)

            elif objecttype == 'testplan':
                rpc.listTestPlans(catalog)
                
        elif command == 'create':
            _check_objecttype_parameter(objecttype)

            if objecttype == 'testcatalog':
                _check_parent_parameter(parent)
                _check_name_parameter(name)
                _check_description_parameter(description)

                rpc.createTestCatalog(parent, name, description)
            
            elif objecttype == 'testcase':
                _check_catalog_parameter(catalog)
                _check_name_parameter(name)
                _check_description_parameter(description)

                rpc.createTestCase(catalog, name, description)

            elif objecttype == 'testplan':
                _check_catalog_parameter(catalog)
                _check_name_parameter(name)

                rpc.createTestPlan(catalog, name)
        
        elif command == 'delete':
            if catalog != None:
                rpc.deleteTestObject('testcatalog', catalog)
            
            elif testcase != None:
                rpc.deleteTestObject('testcase', testcase)
                
            elif plan != None:
                rpc.deleteTestObject('testplan', plan)
        
        elif command == 'modify':
            _check_attribute_parameter(attribute)
            _check_value_parameter(value)

            new_value = {}
            new_value[attribute] = value
            
            if catalog != None:
                rpc.modifyTestObject('testcatalog', catalog, new_value)
            
            elif testcase != None:
                rpc.modifyTestObject('testcase', testcase, new_value)
                
            elif plan != None:
                rpc.modifyTestObject('testplan', plan, new_value)

        elif command == 'setstatus':
            _check_testcase_parameter(testcase)
            _check_plan_parameter(plan)
            _check_status_parameter(status)
        
            rpc.setTestCaseStatus(testcase, plan, status)
        
        elif command == 'getproperties':
            if catalog != None:
                _check_catalog_parameter(catalog)
                rpc.getTestCatalog(catalog)
            
            elif testcase != None:
                _check_testcase_parameter(testcase)
                rpc.getTestCase(testcase, plan)
                
            elif plan != None:
                _check_plan_parameter(plan)
                rpc.getTestPlan(plan)
        
    except SyntaxErrorException as e:
        print "Syntax error: " + str(e)
        retcode = -2
    
    except Exception as e1:
        print "Command failed: " + str(e1)
        retcode = -1

    return retcode

def _check_command_parameter(command):
    if command == None:
        raise SyntaxErrorException("Missing 'command' parameter: should be one of 'list', 'create', 'delete', 'modify', 'setstatus' or 'getproperties'")

    if command not in ['list', 'create', 'delete', 'modify', 'setstatus', 'getproperties']:
        raise SyntaxErrorException("Illegal 'command' parameter: should be one of 'list', 'create', 'delete', 'modify', 'setstatus' or 'getproperties'")

def _check_objecttype_parameter(objecttype):
    if objecttype == None:
        raise SyntaxErrorException("Missing 'objecttype' parameter: should be one of 'testcatalog', 'testcase' or 'testplan'")

    if objecttype not in ['testcatalog', 'testcase', 'testplan']:
        raise SyntaxErrorException("Illegal 'objecttype' parameter: should be one of 'testcatalog', 'testcase' or 'testplan'")

def _check_parent_parameter(parent):
    if parent == None or parent == '':
        raise SyntaxErrorException("Missing 'parent' parameter")

def _check_catalog_parameter(catalog):
    if catalog == None or catalog == '':
        raise SyntaxErrorException("Missing 'catalog' parameter")

def _check_testcase_parameter(testcase):
    if testcase == None or testcase == '':
        raise SyntaxErrorException("Missing 'testcase' parameter")

def _check_plan_parameter(plan):
    if plan == None or plan == '':
        raise SyntaxErrorException("Missing 'plan' parameter")

def _check_name_parameter(name):
    if name == None:
        raise SyntaxErrorException("Missing 'name' parameter")

def _check_description_parameter(description):
    if description == None:
        raise SyntaxErrorException("Missing 'description' parameter")

def _check_status_parameter(status):
    if status == None or status == '':
        raise SyntaxErrorException("Missing 'status' parameter")

def _check_attribute_parameter(attribute):
    if attribute == None or attribute == '':
        raise SyntaxErrorException("Missing 'attribute' parameter")

def _check_value_parameter(value):
    if value == None or value == '':
        raise SyntaxErrorException("Missing 'value' parameter")

def formatExceptionInfo(maxTBlevel=5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    
    try:
        excArgs = exc.__dict__["args"]
    except KeyError:
        excArgs = "<no args>"
    
    excTb = traceback.format_tb(trbk, maxTBlevel)
    
    tracestring = ""
    for step in excTb:
        tracestring += step + "\n"
    
    return "Error name: %s\nArgs: %s\nTraceback:\n%s" % (excName, excArgs, tracestring)


testmanager.add_param("-u", "--user", help="username used to authenticate to Trac", default=None)
testmanager.add_param("-p", "--password", help="password used to authenticate to Trac", default=None)
testmanager.add_param("-n", "--hostname", help="hostname of the Trac server", default='localhost')
testmanager.add_param("-o", "--port", help="port of the Trac server", default=8001, type=int)
testmanager.add_param("-r", "--project", help="Trac project name", default='')

testmanager.add_param("-m", "--command", 
    help= \
        """
        The command to execute:
            list
            create
            delete
            modify
            setstatus
            getproperties
        """ \
    , default=None)

testmanager.add_param("-c", "--catalog", help="Test catalog ID", default=None)
testmanager.add_param("-t", "--testcase", help="Test case ID", default=None)
testmanager.add_param("-a", "--plan", help="Test plan ID", default=None)
testmanager.add_param("-e", "--parent", help="Parent test catalog ID", default=None)
testmanager.add_param("-y", "--objecttype", help="Test object type. Can be testcatalog, testcase or testplan", default=None)
testmanager.add_param("-k", "--name", help="Test object name", default=None)
testmanager.add_param("-d", "--description", help="Test object description", default=None)
testmanager.add_param("-x", "--status", help="Test case status to be set", default=None)
testmanager.add_param("-b", "--attribute", help="Test artifact attribute name to be modified", default=None)
testmanager.add_param("-w", "--value", help="Test artifact attribute value to be set", default=None)


if __name__ == "__main__":
    testmanager.run()

