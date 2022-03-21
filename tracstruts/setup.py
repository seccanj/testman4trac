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

from setuptools import setup

setup(
    name='TracStruts',
    version='3.0.0',
    packages=['tracstruts'],
    package_data={'tracstruts' : ['COPYING', '*.txt', 'templates/*.html', 'htdocs/*.*', 'htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.*']},
    author = 'Roberto Longobardi',
    author_email='otrebor.dev@gmail.com',
    license='Modified BSD, same as Trac. See the file COPYING contained in the package.',
    url='http://trac-hacks.org/wiki/TestManagerForTracPlugin',
    download_url='https://sourceforge.net/projects/testman4trac/files/',
    description='Test management plugin for Trac - TracStruts component',
    long_description='A Trac plugin to create Test Cases, organize them in catalogs and track their execution status and outcome. This module provides an MVC framework, similar to Apache Struts for Java, to help develop Trac plugins.',
    keywords='trac plugin struts mvc generic class framework persistence sql execution run test case management project quality assurance statistics stats charts charting graph',
    entry_points = {'trac.plugins': [
            'tracstruts.api = tracstruts.api', 
            'tracstruts.samples = tracstruts.samples', 
            'tracstruts.tracstruts = tracstruts.tracstruts'
        ]},
    dependency_links = ['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev', 'https://trac.edgewall.org'],
    install_requires = ['Genshi >= 0.6', 'Trac >= 1.4']
)
