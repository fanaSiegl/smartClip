
import os
import sys

try:
    import configparser
except ImportError as e:
    import ConfigParser as configparser

# ==============================================================================

PATH_BIN = os.path.dirname(os.path.realpath(__file__))
PATH_INI = os.path.normpath(os.path.join(PATH_BIN,'..', 'ini'))
PATH_RES = os.path.normpath(os.path.join(PATH_BIN, '..', 'res'))

VERSION_FILE = 'version.ini'

#=============================================================================

def getVersionInfo():

	SECTION_VERSION = 'VERSION'

	config = configparser.ConfigParser()

	cfgFileName = os.path.join(PATH_INI, VERSION_FILE)
	config.read(cfgFileName)

	revision = config.get(SECTION_VERSION, 'REVISION')
	modifiedBy = config.get(SECTION_VERSION, 'AUTHOR')
	lastModified = config.get(SECTION_VERSION, 'MODIFIED')

	return revision, modifiedBy, lastModified

#=============================================================================
