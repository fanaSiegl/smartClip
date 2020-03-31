#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

os.system('sphinx-build -b html -d build/doctrees source build/html')

print("Build finished.")