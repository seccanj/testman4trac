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

from setuptools import setup

setup(
    name = 'SQLExecutor',
    version = '2.0.0',
    packages = ['sqlexecutor'],
    package_data = {'sqlexecutor' : ['*.txt', 'templates/*.html', 'htdocs/*.*', 'htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.*']},
    author = 'Roberto Longobardi',
    author_email = 'otrebor.dev@gmail.com',
    license = 'Modified BSD, same as Trac. See the file COPYING contained in the package.',
    url = 'http://trac-hacks.org/wiki/TestManagerForTracPlugin',
    download_url = 'https://sourceforge.net/projects/testman4trac/files/',
    description = 'Test management plugin for Trac - SQL Executor component',
    long_description = 'A Trac plugin to create Test Cases, organize them in catalogs and track their execution status and outcome. This module provides a generic SQL executor to help debugging your application.',
    keywords = 'trac plugin generic class framework persistence sql execution run test case management project quality assurance statistics stats charts charting graph',
    entry_points = {'trac.plugins': ['sqlexecutor.sql = sqlexecutor.sql']},
    dependency_links = ['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev', 'https://trac.edgewall.org/wiki', 'http://trac-hacks.org/wiki/TestManagerForTracPluginGenericClass'],
    install_requires = ['Genshi >= 0.6', 'Trac >= 1.4, < 1.5', 'TracGenericClass >= 2.0.0']
)
