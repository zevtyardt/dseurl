#!/usr/bin/env python

DESCRIPTION = """
website list grabber
"""

from distutils.core import setup

setup (name = "dseurl",
       version = "0.3",
       license = "GPL",
       description = "dork, search engine, parse",
       long_description = DESCRIPTION,
       author = "zvtyrdt.id",
       author_email = "xnver404@gmail.com",
       url = "https://github.com/zevtyardt",
       install_requires = ['requests'],
       py_modules = ['dse'],
       zip_safe = False,
       entry_points = {'console_scripts': ['dseurl=dse:main']}
       )
