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


class Invocable(object):
    """
    """
    invocables = {}
    default = None
    
    class _Invocable(object):
        """
        """
        
        def handle_request(self, *args):
            print "Inside handle_request()", self.name
            print args
            
            return self.action(*args)
            
            #self.action(*{'a1': 'ciao', 'a2': 'core', 'a3': 'de papa'})
            #self.action(*['ciao', 'core', 'de papa'])
            #self.action(a1='ciao', a2='core', a3='de papa')
            
    def __init__(self, *decoratorArgs):
        """
        """
        self._invocable = Invocable._Invocable()
        decoratorArgs = list(decoratorArgs)

        if decoratorArgs:
            self._invocable.specs = decoratorArgs[0]
            print "Invocable args: %s" % (decoratorArgs[0],)
        
    def __call__(self, action):
        """
        """
        print "Action: %s" % (action,)

        if action.__name__ in Invocable.invocables:
            raise TracException("@Invocable function or method name must be unique")
        
        # Retrieve the names of the action method arguments
        argspec = inspect.getargspec(action)

        self._invocable.name = action.__name__
        self._invocable.description = action.__doc__ or ""
        self._invocable.action = action
        self._invocable.method_args = argspec.args
        Invocable.invocables[action.__name__] = self._invocable

        return self._invocable

