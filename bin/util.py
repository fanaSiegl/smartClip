
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

DESCRIPTION = '''
SmartClip
=========

is a tool to make the clip definition as easy as possible.

About
-----

According to the guiding CON that must be selected by a user, searches for normals of neighbour faces and defines a base
coordinate system orientation. Projects points to its boundaries in the correspondent vectors and searches for their projection to
the clip contra part. Measures projection distance and defines CONNECTOR STOP property.
In the second step, the user is requested to select nodes for the beam definition connecting the connector element with the clip
itself and the contra part.

Requirements
------------

.. warning::
    
    When run as a plugin, ANSA 18.0.1 and newer must be used! This is due to a bug in version 17.x.x


* SmartClip requires geometry and FEM model loaded into the one session.
* At least the clip part geometry has to be meshed (the finer the mesh is the more accurate is the stop distances mechanism).
    

Usage
-----

1. select guiding CON
2. select nodes connecting the connector element and the clip contra part
3. select nodes connecting the connector element and the clip itself
4. an option to create a symmetrical clip automatically


Best practice
-------------
    
* Keep FEM model visible (visib switch on) in the time of guiding CON selection.
* Try to reduce model geometry and avoid large faces (cut them if necessary). That will significantly reduce the time for clip creation.
	
'''

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

__doc__ = DESCRIPTION