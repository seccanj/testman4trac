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

from api import Invocable


# Example of class type of action
class MyActionsClass(object):

    @Invocable(
        {
            'results': {'success': {'kind': 'template', 'template_name': 'my_action_method_input_template.html'}}
        }
    )
    def my_action_init_view(self):
        """
        This method provides the first screen of the application.
        To summon it, point the browser to:
        http://<your environment>/action/tracstruts.samples.MyActionsClass!my_action_init_view
        
        It renders through the specified template "my_action_method_input_template.html"
        """
        
        print("inside my_action_init_view")
        
        return 'success'


    @Invocable(
        {
            'results': {'success': {'kind': 'template', 'template_name': 'my_action_method_output_template.html'}},
            'parameters': {
                'a1': 'in',
                'a2': 'in_out',
                'a3': 'in_out',
                'a4': 'out'
            }
        }
    )
    def my_action_method(self, a5, a6, a7):
        """
        This action is invoked from the initial screen's first form.
        
        It receives part of the parameters, the ones specified in the
        @Invocable "parameters" attribute with an 'in' or 'in_out' type,
        as instance fields, and part as method arguments.
        
        Which is which is determined automatically by the TracStruts
        engine.

        All 'in', 'in_out' and 'out' parameters are automatically added
        to a "tracstruts_context", which is then added to every FORM
        found in the template and thus received back with every form
        submission. 
        Parameters for the actions are thus first looked for in the 
        normal form sumbission parameters and, if not found, in the
        "tracstruts_context", which then acts like a user session.
        
        It renders through the specified template "my_action_method_output_template.html".
        """
        
        print("inside my_action_method. Parameters: %s %s %s %s %s %s" % (self.a1, self.a2, self.a3, a5, a6, a7))
        
        self.a1 = "AA1"
        self.a3 = a5
        self.a4 = 'output value'
        
        return 'success'


    @Invocable(
        {
            'results': {'success': {'kind': 'json', 'field_name': 'ajax_result'}},
            'parameters': {
                'a1': 'in',
                'a2': 'in_out',
                'a3': 'in_out'
            }
        }
    )
    def my_action_ajax_method(self, a5, a6, a7):
        """
        This action is invoked through an Ajax POST form submission.
        
        It receives part of the parameters, the ones specified in the
        @Invocable "parameters" attribute with an 'in' or 'in_out' type,
        as instance fields, and part as method arguments.
        
        Which is which is determined automatically by the TracStruts
        engine.
        
        All 'in', 'in_out' and 'out' parameters are automatically added
        to a "tracstruts_context", which is then added to every FORM
        found in the template and thus received back with every form
        submission. 
        Parameters for the actions are thus first looked for in the 
        normal form sumbission parameters and, if not found, in the
        "tracstruts_context", which then acts like a user session.
        
        Its result is not a template, but a JSON string which is
        returned in the instance field specified by the @Invocable
        parameter "field_name".
        """
        
        print("inside my_action_ajax_method. Parameters: %s %s %s %s %s %s" % (self.a1, self.a2, self.a3, a5, a6, a7))
        
        self.ajax_result = '{"a1": "'+self.a1+'", "a2": "'+self.a2+'", "a5": "'+a5+'", "a6": "'+a6+'"}'
        
        return 'success'



# Example of function type of action, still not supported for output
# parameters.
#@Invocable("template.html")
#def my_action(a1, a2, a3):
#    print "my_action", a1, a2, a3

