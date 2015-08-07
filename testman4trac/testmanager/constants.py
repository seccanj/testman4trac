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

class Constants(Component):

    default_status = None
    
    base_url = None

    DOUBLE_QUOTES = re.compile("\"")
    
    _config_properties = {}
    sortby = 'custom'
    open_new_window = False
    default_view_mode = 'tree'
    ticket_summary_option = 'full_path'
    ticket_summary_option_values = ['full_path', 'last_n_catalogs', 'empty', 'fixed_text']
    ticket_summary_text = ''
    ticket_summary_num_catalogs = '1'
    ticket_summary_separator = ' - '

    def __init__(self, *args, **kwargs):
        """
        Parses the configuration file for the section 'testmanager'.
        
        Available properties are:
        
          testplan.sortby = {modification_time|name|custom}    (default is custom)
          testcase.open_new_window = {True|False}              (default is False)
        """
        
        Component.__init__(self, *args, **kwargs)

        self._parse_config_options()

    
    def _parse_config_options(self):
        if 'testmanager' in self.config:
            self.sortby = self.config.get('testmanager', 'testplan.sortby', 'custom')
            self.open_new_window = self.config.get('testmanager', 'testcase.open_new_window', '') == 'True'
            self.ticket_summary_option = self.config.get('testmanager', 'ticket_summary_option', 'full_path')
            if not (self.ticket_summary_option in self.ticket_summary_option_values):
                raise TracError("Configuration property 'ticket_summary_option' in trac.ini file must be one of: " + ', '.join(self.ticket_summary_option_values))
            self.ticket_summary_text = self.config.get('testmanager', 'ticket_summary_text', '')
            self.ticket_summary_num_catalogs = self.config.get('testmanager', 'ticket_summary_num_catalogs', '')
            self.ticket_summary_separator = self.config.get('testmanager', 'ticket_summary_separator', ' - ')
            
            default_view_mode = self.config.get('testmanager', 'testcatalog.default_view', 'tree')

