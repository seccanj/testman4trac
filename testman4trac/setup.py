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

extra = {} 

try:
    import babel

    from trac.dist import get_l10n_js_cmdclass
    cmdclass = get_l10n_js_cmdclass()
    if cmdclass: # OK, Babel is there
        extra['cmdclass'] = cmdclass 
        extractors = [ 
            ('**.py',                'python', None), 
            ('**/templates/**.html', 'genshi', None), 
            ('**/templates/**.txt',  'genshi', { 
                'template_class': 'genshi.template:TextTemplate' 
            }), 
        ] 
        extra['message_extractors'] = { 
            'testmanager': extractors, 
        }

except ImportError as error:
    print(error)
    print("Babel not found!")
    pass

setup(
    name = 'TestManager',
    version = '2.0.0',
    packages = ['testmanager','testmanager.upgrades'],
    package_data = {
        'testmanager' : [
            'COPYING', 
            '*.txt', 
            'templates/*.html', 
            'htdocs/js/*.js', 
            'htdocs/js/*.swf', 
            'htdocs/css/*.css', 
            'htdocs/css/jquery-ui/*.css', 
            'htdocs/css/jquery-ui/images/*.*', 
            'htdocs/css/blitzer/*.css', 
            'htdocs/css/blitzer/images/*.*', 
            'htdocs/css/images/*.*', 
            'htdocs/images/*.*', 
            'locale/*.*', 
            'locale/*/LC_MESSAGES/*.mo',
            'htdocs/testmanager/*.js'
        ]
    },
    author = 'Roberto Longobardi',
    author_email = 'otrebor.dev@gmail.com',
    license = 'Modified BSD, same as Trac. See the file COPYING contained in the package.',
    url = 'http://trac-hacks.org/wiki/TestManagerForTracPlugin',
    download_url = 'https://sourceforge.net/projects/testman4trac/files/',
    description = 'Test management plugin for Trac',
    long_description = 'A Trac plugin to create Test Cases, organize them in catalogs and track their execution status and outcome.',
    keywords = 'trac plugin test case management project quality assurance statistics stats charts charting graph',
    entry_points = {'trac.plugins': [
            'testmanager.admin = testmanager.admin', 
            'testmanager.api = testmanager.api', 
            'testmanager.model = testmanager.model', 
            'testmanager.rpcsupport = testmanager.rpcsupport', 
            'testmanager.stats = testmanager.stats', 
            'testmanager.web_ui = testmanager.web_ui', 
            'testmanager.wiki = testmanager.wiki', 
            'testmanager.workflow = testmanager.workflow'
        ]},
    dependency_links = ['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev', 'https://trac.edgewall.org/wiki', 'http://trac-hacks.org/wiki/TestManagerForTracPluginGenericClass', 'http://trac-hacks.org/wiki/TracGenericWorkflowPlugin'],
    install_requires = ['Genshi >= 0.6', 'Trac >= 1.4, < 1.5', 'TracGenericClass >= 2.0.0', 'TracGenericWorkflow >= 2.0.0'],
    **extra
)
