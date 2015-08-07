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

import inspect

import json
import sys
import traceback

from StringIO import StringIO

from genshi import HTML, Markup
from genshi.builder import tag, Element
from genshi.core import Attrs, START
from genshi.filters import Translator
from genshi.filters.transform import Transformer
from genshi.output import DocType
from genshi.template import TemplateLoader, MarkupTemplate, NewTextTemplate

from trac.core import *
from trac.util import get_reporter_id
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider
from trac.web.href import Href
from trac.wiki.formatter import Formatter

from api import Invocable


class TracStruts(Component):
    """
    """
    
    implements(IRequestHandler, ITemplateStreamFilter, ITemplateProvider)


    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/action/')

    def process_request(self, req):

        self.log.info("Handling request path '%s'" % (req.path_info,))
        full_action_name = req.path_info.rpartition('/action/')[2]

        if not full_action_name:
            raise TracError("Must specify the action to be performed")

        action_class, _, action_name = full_action_name.partition('!')

        self.env.log.debug("Action class: '%s', method: '%s'" % (action_class, action_name))

        if not action_class or not action_name:
            raise TracError("Action class and method names are required")

        if action_name not in Invocable.invocables:
            raise TracError("Unrecognized action '%s'. Known actions are: %s" % (action_name,Invocable.invocables.keys()))

        # Get reference to action handler wrapper (i.e. _Invocable)
        invocable = Invocable.invocables[action_name]

        # Perform security check if requested
        if 'required_roles' in invocable.specs:
            self.env.log.debug("'required_roles' in Invocable specs is '%s'" % (invocable.specs['required_roles'],))

            has_permission = False
            for required_role in invocable.specs['required_roles']:
                if req.perm.has_permission(required_role):
                    has_permission = True
                    break
                    
            if not has_permission:
                raise PermissionError(str(invocable.specs['required_roles']), None, env)

        # Create instance of the user's action class
        # Note: this assumes the class is in this code's scope. 
        #       Otherwise, we should use the _get_class() function found
        #       at the bottom of this file, which also imports the 
        #       module. In this case, the action name should be 
        #       fully qualified, e.g. "module.submodule.ClassName"
        #action_instance = globals()[action_class]()
        action_instance = _get_class(action_class)

        # Deserialize tracstruts context from the JSON hidden field
        # 'tracstruts_context', or create it
        tracstruts_context_string = req.args.get('__STRACS_CONTEXT', None)
        tracstruts_context = None
        if tracstruts_context_string is not None:
            io = StringIO(tracstruts_context_string)
            tracstruts_context = json.load(io)
        else:
            tracstruts_context_string = '{}'
            tracstruts_context = {}        
        
        self.env.log.debug("Tracstruts context JSON deserialized is '%s'." % (tracstruts_context_string,))

        # Inject basic fields into the instance
        setattr(action_instance, 'env', self.env)
        setattr(action_instance, 'req', req)

        
        # Inject required fields into the instance
        if 'parameters' in invocable.specs:
            self.env.log.debug("'parameters' in Invocable specs is '%s'" % (invocable.specs['parameters'],))

            for arg_name in invocable.specs['parameters'].keys():
                arg_kind = invocable.specs['parameters'][arg_name]
                
                if arg_kind == 'in' or arg_kind == 'in_out':
                    arg_value = req.args.get(arg_name, None)

                    # If arg_value == None, take the value from the 
                    # tracstruts_context, if present
                    if arg_value is None and arg_name in tracstruts_context:
                        arg_value = tracstruts_context[arg_name]

                    self.env.log.debug("Injecting field '%s'='%s' in action instance." % (arg_name, arg_value))
                    setattr(action_instance, arg_name, arg_value)

                    # Add any request parameter to the tracstruts_context,
                    # as if it were a user session
                    if _is_type_json_supported(arg_value):
                        tracstruts_context[arg_name] = arg_value

        else:
            self.env.log.debug("No 'parameters' specified in Invocable specs.")

        self.env.log.debug("Tracstruts context object after parameters injection is: '%s'" % (tracstruts_context,))
            
        # Build required handler parameters
        action_args = []

        for arg_name in invocable.method_args:
            if arg_name != "self":
                arg_value = req.args.get(arg_name, None)
                
                # If arg_value == None, take the value from the 
                # tracstruts_context, if present
                if arg_value is None and arg_name in tracstruts_context:
                    arg_value = tracstruts_context[arg_name]

                self.env.log.debug("Action method arg '%s'='%s'" % (arg_name, arg_value))
                
                action_args.append(arg_value)

                # Add any method argument to the tracstruts_context,
                # as if it were a user session
                if _is_type_json_supported(arg_value):
                    tracstruts_context[arg_name] = arg_value

        self.env.log.debug("Complete action method args are: '%s'" % (action_args,))
        
        self.env.log.debug("Tracstruts context object after action method parameter preparation is: '%s'" % (tracstruts_context,))

        # Invoke action handler on created instance
        try:
            if action_args:
                result = invocable.handle_request(action_instance, *action_args)
            else:
                result = invocable.handle_request(action_instance)

            if result:
                self.env.log.debug("Action result is: '%s'" % (result,))
            else:
                self.env.log.debug("Action did not return a result")
                
            if result and ('results' in invocable.specs):
                if not result in invocable.specs['results']:
                    raise TracError("Unrecognized result '%s' for action '%s'" % (result, full_action_name))
                    
                result_kind = invocable.specs['results'][result]['kind']

                self.env.log.debug("Result kind is '%s'." % (result_kind,))
                
                if result_kind == 'template':
                    if not 'template_name' in invocable.specs['results'][result]:
                        raise TracError("Missing 'template_name' specification in the @Invocable for action '%s'" % (full_action_name,))
                    
                    # Prepare data dictionary for template rendering
                    data = {}

                    # Set built-in data elements
                    data['base_url'] = Href(req.base_path)()

                    # Add every (old) value in the tracstruts_context to the
                    # data for the template.
                    # Any new values from the action will override these 
                    # old values just next.
                    for k in tracstruts_context.keys():
                        data[k] = tracstruts_context[k]

                    # Get output field values from the action instance and set
                    # them into the data
                    if 'parameters' in invocable.specs:
                        for arg_name in invocable.specs['parameters'].keys():
                            arg_kind = invocable.specs['parameters'][arg_name]
                            
                            if arg_kind == 'out' or arg_kind == 'in_out':
                                arg_value = None
                                
                                if hasattr(action_instance, arg_name):
                                    arg_value = getattr(action_instance, arg_name)
                                elif arg_name in tracstruts_context:
                                    # If the instance has not provided a
                                    # field for this output argument,
                                    # take the value from the
                                    # tracstruts_context, if present
                                    arg_value = tracstruts_context[arg_name]                                    

                                self.env.log.debug("Setting data for template: '%s'='%s'" % (arg_name, arg_value))
                                data[arg_name] = arg_value

                                # Add or update any output parameter to 
                                # the tracstruts_context as if it were a 
                                # user session
                                if _is_type_json_supported(arg_value):
                                    tracstruts_context[arg_name] = arg_value

                    # Serialize tracstruts_context into JSON and add it to
                    # the data for the template.
                    # This makes it also available to the 
                    # ITemplateStreamFilter, which will add it to every
                    # form, inside a hidden field.
                    io = StringIO()
                    
                    self.env.log.debug("Tracstruts context object after action invocation is: '%s'" % (tracstruts_context,))
                    #str.replace("\r\n", "\\\n")
                    
                    json.dump(tracstruts_context, io)
                    tracstruts_context_string = io.getvalue()
                    data['tracstruts_context'] = tracstruts_context_string

                    self.env.log.debug("Tracstruts context JSON after action invocation is '%s'." % (tracstruts_context_string,))

                    template = invocable.specs['results'][result]['template_name']

                    self.env.log.debug("Template name is '%s'." % (template,))

                    return template, data, None

                elif result_kind == 'json':
                    class_field_name = invocable.specs['results'][result]['field_name']

                    if not hasattr(action_instance, class_field_name):
                        raise TracError("Action '%s' must provide the the JSON result in a field named '%s'." % (full_action_name, class_field_name))
                        
                    jsdstr = getattr(action_instance, class_field_name)
                    
                    if isinstance(jsdstr, unicode): 
                        jsdstr = jsdstr.encode('utf-8') 

                    req.send_header("Content-Length", len(jsdstr))
                    req.write(jsdstr)
                    return

            else:
                self.env.log.debug("Nothing to render.")
                return None

        except:
            self.env.log.error("Error invoking action handler")
            self.env.log.error(formatExceptionInfo())

            return None


    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        self.env.log.debug("Filtering stream to add tracstruts_context.")

        if 'tracstruts_context' in data:
            stream = stream | Transformer('//head').append(self._add_tracstruts_context_javascript(data['tracstruts_context'])) \
                            | self._add_tracstruts_context_to_forms(data['tracstruts_context'])
                     
        return stream

    def _add_tracstruts_context_to_forms(self, tracstruts_context_string):
        """
        Add tracstruts context as a hidden field to every form.
        """
        self.env.log.debug("Adding tracstruts_context to every form.")

        elem = tag.div(
            tag.input(type='hidden', name='__STRACS_CONTEXT', value=tracstruts_context_string)
        )
        def _generate(stream, ctxt=None):
            for kind, data, pos in stream:
                if kind is START and data[0].localname == 'form':
                               # and data[1].get('method', '').lower() == 'post':
                    yield kind, data, pos
                    for event in elem.generate():
                        yield event
                else:
                    yield kind, data, pos
        return _generate

    def _add_tracstruts_context_javascript(self, tracstruts_context_string):
        """
        Add tracstruts context as a Javascript global variable, named
        'tracstrutsContext', available to client's Javascript code.
        This is useful for Ajax requests.
        """
        self.env.log.debug("Adding tracstruts_context as a Javascript global variable.")

        js_variable = u"var tracstrutsContext=JSON.parse('"+tracstruts_context_string+"');"
    
        elem = tag.script(js_variable, type='text/javascript')

        self.env.log.debug(elem)

        return elem


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        self.env.log.debug("get_templates_dirs()")
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        self.env.log.debug("get_templates_dirs()")
        from pkg_resources import resource_filename
        return [('tracstruts', resource_filename(__name__, 'htdocs'))]


def _get_class(kls):
    parts = kls.split('.')
    module = ",".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

_JSON_SUPPORTED_TYPES = (dict, list, tuple, str, unicode, int, long, float)

def _is_type_json_supported(value):
    return isinstance(value, _JSON_SUPPORTED_TYPES)
    
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
