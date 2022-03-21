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

import threading
from threading import current_thread


class GenericClassCacheSystem:
    """
    Generic Class cache system for Trac.
    
    Stores objects in a thread-related storage.
    """

    cache = {}
    
    @classmethod
    def clear_cache(cls):
        """
        Clears the cache for a particular thread.
        """
        
        cls.cache[current_thread().name] = {}

    @classmethod
    def cache_put(cls, obj):
        """
        Puts the specified object into the thread-related cache
        """
        
        key = obj.gey_key_string()
        
        thread_name = current_thread().name
        
        if thread_name not in cls.cache:
            cls.cache[thread_name] = {}
            
        cls.cache[thread_name][obj.realm + ":" + key] = obj
        
    @classmethod
    def cache_get(cls, realm, key):
        """
        Gets the object specified by key form the thread-related cache
        """
        
        result = None
        thread_name = current_thread().name
        full_key = realm + ":" + key
        
        if thread_name in cls.cache and full_key in cls.cache[thread_name]:
            result = cls.cache[thread_name][full_key]
        
        return result

