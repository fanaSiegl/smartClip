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

PRODUCTIVE_VERSION_BIN = '/data/fem/+software/SKRIPTY/tools/bin'
CONFIG_FILE = 'ini/config.ini'
CONFIG_FILE_TEMPLATE = 'ini/config_template.ini'

APPLICATION_NAME = 'smartClip'

DOCUMENTATON_PATH = '/data/fem/+software/SKRIPTY/tools/python/tool_documentation/default'
DOCUMENTATON_GROUP = 'ANSA tools'
DOCUMENTATON_DESCRIPTION = 'is a tool to make the clip definition as easy as possible.'

#===============================================================================

def runSubprocess(command):
    
    process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    return process.communicate()

#===============================================================================

def createConfigFile():
    
    print 'Updating a configuration file'
    
    cfgFileName = os.path.join(PATH_SELF, CONFIG_FILE_TEMPLATE)
    cfgFile = open(cfgFileName, 'rt')
    template = string.Template(cfgFile.read())
    cfgFile.close()
    
    outputString = template.substitute(
        {'revision' : args.revision,
         'modifiedBy' : modifiedBy,
         'lastModified': lastModified})
    
    cfgFile = open(os.path.join(targetDir, CONFIG_FILE), 'wt')
    cfgFile.write(outputString)
    cfgFile.close()
    
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

    configFileTemplate = os.path.join(targetDir, CONFIG_FILE_TEMPLATE)
    os.remove(configFileTemplate)
    
    buildScript = os.path.join(targetDir, 'build.py')
    os.remove(buildScript)

#=============================================================================

def getRevisionInfo():
    
    print 'Gathering revision information'
    
    output, _ = runSubprocess('git log %s -n 1' % args.revision)
    
    lines = output.split('\n')
    
    modifiedBy = lines[1].split(':')[1].strip()
    lastModified = ':'.join(lines[2].split(':')[1:]).strip()
    
    return modifiedBy, lastModified

#=============================================================================

def install():
    
    print 'Releasing to the productive version'
    
    defaultDir = os.path.join(args.target, 'default')
    
    if os.path.exists(defaultDir):
        os.unlink(defaultDir)
    os.symlink(args.revision, defaultDir)


#=============================================================================

def createDocumentation():
    
    SPHINX_DOC = os.path.join(targetDir, 'doc', 'sphinx')
    SPHINX_SOURCE = os.path.join(SPHINX_DOC, 'source')
    SPHINX_DOCTREES = os.path.join(SPHINX_DOC, 'build', 'doctrees')
    SPHINX_HTML = os.path.join(SPHINX_DOC, 'build', 'html')
        
    # create local documentation
    os.system('sphinx-build -b html -d %s %s %s' % (SPHINX_DOCTREES, SPHINX_SOURCE, SPHINX_HTML))


#=============================================================================

def publishDocumentation():

    SPHINX_DOC = os.path.join(targetDir, 'doc', 'sphinx')
    SPHINX_HTML = os.path.join(SPHINX_DOC, 'build', 'html')
    
    SPHINX_INDEX = os.path.join(SPHINX_HTML, 'index.thml')
    
    # copy to tool documentation
    docFileName = os.path.join(DOCUMENTATON_PATH, 'source',
        DOCUMENTATON_GROUP.replace(' ', '_'), '%s.rst' % APPLICATION_NAME)
    
    if not os.path.exists(os.path.dirname(docFileName)):
        os.mkdir(os.path.dirname(docFileName))
    
    if os.path.exists(docFileName):
        os.remove(docFileName)
    
    fo = open(docFileName, 'wt')
    fo.write('.. _%s: %s\n\n' % (APPLICATION_NAME, SPHINX_INDEX))
    fo.write('`%s`_ - %s\n\n' % (APPLICATION_NAME, DOCUMENTATON_DESCRIPTION))
    fo.close()
    
    # update tool documentation
    updateScriptPath = os.path.join(DOCUMENTATON_PATH, 'buildHtmlDoc.py')
    os.system(updateScriptPath)
    
    
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
modifiedBy, lastModified = getRevisionInfo()
createConfigFile()
createDocumentation()
cleanUp()

if args.install:
    install()
    publishDocumentation()
    
print 'Done'