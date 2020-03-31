
import os
import sys
import collections

try:
    import configparser
except ImportError as e:
    import ConfigParser as configparser

# ==============================================================================

PATH_BIN = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
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

#===============================================================================

def registerClass(cls):
    
    def registerToContainer(container, listIdName='ID'):
        
        if type(container) is dict or type(container) is collections.OrderedDict:
            container[cls.NAME] = cls
        elif type(cls.container) is list:
            
            if hasattr(cls, listIdName):
                itemId = getattr(cls, listIdName)
                if itemId >= len(container):
                    container.extend((itemId - len(container) + 1)*[None])
                container[itemId] = cls
            else:
                container.append(cls)
    
    registerToContainer(cls.container)
    
    # register to subcontainer
    if hasattr(cls, 'subcontainer'):
        registerToContainer(cls.subcontainer, 'SUBID')
    
    return cls
    
#=============================================================================
