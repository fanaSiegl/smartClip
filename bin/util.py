
import os
import sys
import configparser

# ==============================================================================

PATH_BIN = os.path.dirname(os.path.realpath(__file__))
PATH_INI = os.path.normpath(os.path.join(PATH_BIN,'..', 'ini'))
PATH_RES = os.path.normpath(os.path.join(PATH_BIN, '..', 'res'))

CONFIG_FILE = 'config.ini'

DESCRIPTION = '''"SmartClip" tool is an utility to make the clip definition as easy as possible.
	
According to the guiding CON that must be selected by a user, searches for normals of neighbour faces and defines a base
coordinate system orientation. Projects points to its boundaries in the correspondent vectors and searches for their projection to
the clip contra part. Measures projection distance and defines CONNECTOR STOP property.
In the second step, the user is requested to select nodes for the beam definition connecting the connector element with the clip
itself and the contra part.

Usage:
	1. select guiding CON
	2. select nodes connecting the connector element and the clip contra part
	3. select nodes connecting the connector element and the clip itself

NOTE:
	SmartClip requires geometry and FEM model loaded into the one session.
	Keep FEM model visible (visib switch on) in the time of guiding CON selection for the best result.
'''

#=============================================================================

def getVersionInfo():

	SECTION_VERSION = 'VERSION'

	config = configparser.ConfigParser()

	cfgFileName = os.path.join(PATH_INI, CONFIG_FILE)
	config.read(cfgFileName)

	revision = config.get(SECTION_VERSION, 'REVISION')
	modifiedBy = config.get(SECTION_VERSION, 'AUTHOR')
	lastModified = config.get(SECTION_VERSION, 'MODIFIED')

	return revision, modifiedBy, lastModified

#=============================================================================
