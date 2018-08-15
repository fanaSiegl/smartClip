#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

os.system('sphinx-build -b html -d build/doctrees   source build/html')

print "Build finished."