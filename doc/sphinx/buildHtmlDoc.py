#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

PATH_SELF = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(PATH_SELF, 'sphinx-build.py')

os.system('python %s -b html -d build/doctrees   source build/html' % path)

print "Build finished."