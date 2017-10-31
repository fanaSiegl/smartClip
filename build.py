#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Python script for '''

import os
import sys
import shutil
import string
import subprocess
import argparse
from _imaging import path

PATH_SELF = os.path.dirname(os.path.abspath(__file__))

#===============================================================================

def runSubprocess(command):
    
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    return process.communicate()

#=============================================================================

def createRevisionContents():
    
    print 'Creating a revision content'
    
    if os.path.isdir(targetDir):
        print 'Current revision exists already.'
        sys.exit()
    else:
        os.makedirs(targetDir)
    
    runSubprocess('git clone . %s' % (targetDir))
    runSubprocess('git checkout %s' % (args.revision))

#=============================================================================

def cleanUp():
    
    print 'Cleaning up files'
    
    repositoryPath = os.path.join(targetDir, '.git')
    shutil.rmtree(repositoryPath)
        
    buildScript = os.path.join(targetDir, 'build.py')
    os.remove(buildScript)

#=============================================================================

def install():
    
    print 'Releasing to the productive version'
    
    defaultDir = os.path.join(args.target, 'default')
    
    if os.path.exists(defaultDir):
        os.unlink(defaultDir)
    os.symlink(args.revision, defaultDir)

#=============================================================================
    
parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('target', help='Build destination path.')
parser.add_argument('revision', help='Revision number to be build.')
parser.add_argument('-i', action='store_true',  dest='install',
    help='Makes a build revision default.')

args = parser.parse_args()

targetDir = os.path.join(args.target, args.revision)

createRevisionContents()
cleanUp()

if args.install:
    install()
    
print 'Done'