Check the tutorial on YouTube: http://www.youtube.com/watch?v=BIi3QMT0rT4 

Test Manager plugin for Trac

Copyright (C) 2010-2022 Roberto Longobardi
 
This file is part of the Test Manager plugin for Trac.
 
This software is licensed as described in the file COPYING, which
you should have received as part of this distribution. The terms
are also available at: 

https://trac-hacks.org/wiki/TestManagerForTracPluginLicense

Author: Roberto Longobardi <otrebor.dev@gmail.com>


Project web page on TracHacks: http://trac-hacks.org/wiki/TestManagerForTracPlugin

Project web page on SourceForge.net (don't use it for the git repo): http://sourceforge.net/projects/testman4trac/
  
Project web page on Pypi: http://pypi.python.org/pypi/TestManager

Project source repository on GitHub: https://github.com/seccanj/testman4trac

  
A Trac plugin to create Test Cases, organize them in catalogs, generate test plans and track their execution status and outcome.

This module provides a framework to help creating workflows around any Trac Resource.

Features:
    * Declarative definition of the workflow, specified in trac.ini.
    * Same syntax as the basic Ticket workflow (I may have derived
      some line of code from Trac itself... ;-))
    * Easy GUI integration support. You can expose the workflow 
      operation widgets anywhere in your application pages.
    * Fine-grained authorization control. You can specify which role
      is required to perform each state transition, and to execute
      each corresponding action.
    * Custom actions. An open API allows you to program your own 
      custom actions to be executed at any workflow state transition.
    * Out-of-the-box built-in actions are provided.

=================================================================================================  
Change History:

(Refer to the tickets on trac-hacks for complete descriptions.)

Release 2.0.0 (2022-03-19): 

  o Fixed compatibility with Trac 1.4. This version only works with Trac 1.4.x.
    With Trac 0.12.x use plugins v. 1.9.x.
    With Trac 1.2 use plugins v. 1.20.x.
    There is currently no version that works with Trac 1.5.x.

  o With this version a big effort has been done to update and complete all the translations.
    Also thanks to @longradix for adding Dutch and updating German and to Google Translate for the rest :-)

Release 1.1.0 (2022-02-07): 
  o Removed use of deprecated APIs and replaced with updated ones. Plugin now compatible with Trac 1.4.

Release 1.0.4 (2012-10-14):
  This release makes the plugins compatible with Trac 1.0.
  o Fixed Ticket #10293 (Track-Hacks): New install impossible on Trac 1.0beta1

Release 1.0.2 (2010-11-30):
  o Added out of the box operation to workflow engine: set_owner and set_owner_to_self

Release 1.0.0 (2010-10-01):
  o First release publicly available apart from the core Test Manager plugin
  
