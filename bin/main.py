# PYTHON script

'''
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

DOCUMENTATON_GROUP = 'ANSA tools'
DOCUMENTATON_DESCRIPTION = 'tool to make the clip definition as easy as possible'

import os
import sys
from traceback import format_exc

import ansa
from ansa import base, guitk, constants

# ==============================================================================

# in case of running from remote simlink in windows
#if 'win' in sys.platform:
#	toolName = os.path.splitext(os.path.basename(__file__))[0].replace('tool_', '')
#	PATH_SELF = os.path.join(os.environ['ANSA_TOOLS'], toolName, 'default', 'bin')
#else:
PATH_SELF = os.path.dirname(os.path.realpath(__file__))

ansa.ImportCode(os.path.join(PATH_SELF, 'domain', 'util.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'domain', 'comp_items.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_selectCon.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_clipType.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_connectorStop.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_connectorNodes.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_mirrorClip.py'))

# ==============================================================================

DEBUG = 0

# ==============================================================================

def setWaitCursor(method, *args):
	def methodWithWaitCursor(*args):
		
		parent = args[0]
#		guitk.BCSetApplicationOverrideCursor(guitk.constants.BCCursorWait)
		try:
			method(*args)
		except Exception as e:
			print(format_exc())
			base.BlockRedraws(False)
			base.RedrawAll()
			SmartClipDialog.showMessage(str(e), critical=True)
			
			guitk.BCRestoreApplicationOverrideCursor()

	return methodWithWaitCursor
	
# ==============================================================================

class SmartClipDialog(object):
	
	TITLE = 'SmartClip'
	WIDTH = 600
	HEIGTH = 400
	
	DFT_TYPE_BEAM = 1
	DFT_TYPE_GEOM = 0
	DFT_MIRROR_CLIP = True
	
	def __init__(self):
		
		revision, modifiedBy, lastModified = util.getVersionInfo()
		
		self.mainWizard = guitk.BCWizardCreate("%s (%s)" % (self.TITLE, revision), guitk.constants.BCOnExitDestroy)
		
		self.smartClip = comp_items.SmartClip()
		
		self._setupPages()
		self._setupWidgets()
		
		guitk.BCShow(self.mainWizard)
	
	#-------------------------------------------------------------------------
	
	def _setupPages(self):
		
		''' Initialisation of pages '''
		
		self.pages = list()
		self.pages.append(page_clipType.SelectClipTypePage(self))
		self.pages.append(page_selectCon.SelectConPage(self))
		self.pages.append(page_connectorStop.ConnectorStopPage(self))
		self.pages.append(page_connectorNodes.SelectClipNodesPage(self))
		self.pages.append(page_connectorNodes.SelectClipOppositeNodesPage(self))
		self.pages.append(page_mirrorClip.MirrorClipPage(self))

	#-------------------------------------------------------------------------
	
	def _setupWidgets(self):
		
		guitk.BCWindowSetInitSize(self.mainWizard, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWizard, False)
		
		# page frame initialisation
		for page in self.pages:
			guitk.BCWizardAddPage(self.mainWizard, page.getFrame(), page.TITLE, page.DESCRIPTION,  page.INFO)
			
		guitk.BCWizardSetCurrentPageChangedFunction(self.mainWizard, self.currentPageChanged, None)
		guitk.BCWindowSetAcceptFunction(self.mainWizard, newClip, self)
			
		guitk.BCWindowSetRejectFunction(self.mainWizard, _reject, self)
		guitk.BCWindowSetSaveSettings(self.mainWizard, True)
				
	#-------------------------------------------------------------------------

	def getSmartClip(self):
		
		return self.smartClip
			
	#-------------------------------------------------------------------------
	@setWaitCursor
	def currentPageChanged(self, wizard, oldIndex, stepId, data):
				
		currentId =guitk.BCWizardCurrentIndex(self.mainWizard)
		currentPage = self.pages[currentId]
		
		self.pages[oldIndex].deactivated()
		if oldIndex > currentId:
			self.pages[oldIndex].deactivatedBack()
		else:
			self.pages[oldIndex].deactivatedNext()
			
		currentPage.activated()
		currentPage.updateInfo()
		self.checkNextState()
		
	#-------------------------------------------------------------------------

	def stepFinished(self):
	
		self.checkNextState()
	
	#-------------------------------------------------------------------------

	def checkNextState(self):
	
		currentId = guitk.BCWizardCurrentIndex(self.mainWizard)
		currentPage = self.pages[currentId]
				
		if currentPage.isFinished:
			guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
		else:	
			guitk.BCWizardSetNextButtonEnabled(self.mainWizard, False)
			
	#-------------------------------------------------------------------------
	
	def setTypeGeom(self, index, geomType):
			
		self.setDftTypeGeom(index)
		
		self.smartClip.setGeomType(geomType)
	
	#-------------------------------------------------------------------------
	
	def setTypeBeam(self, index, beamType):
			
		self.setDftTypeBeam(index)
		
		self.smartClip.setBeamType(beamType)
		
	#-------------------------------------------------------------------------
	@classmethod
	def setDftTypeBeam(cls, value):
		cls.DFT_TYPE_BEAM = value
		
	#-------------------------------------------------------------------------
	@classmethod
	def setDftTypeGeom(cls, value):
		cls.DFT_TYPE_GEOM = value
	
	#-------------------------------------------------------------------------
	@classmethod
	def setDftMirrorClipState(cls, state):
		cls.DFT_MIRROR_CLIP = state
	
	#-------------------------------------------------------------------------
    
	def showStatusBarMessage(self, message):
		
		guitk.BCStatusBarTimedMessage(self.statusBar, message, 2000)
	
	#-------------------------------------------------------------------------
	@staticmethod
	def showMessage(message, critical=False):
		
		if critical:
			messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxCritical, message, True)
		else:
			messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxInformation, message, True)
		
		guitk.BCMessageWindowSetRejectButtonVisible(messageWindow, False)
		guitk.BCWindowSetSaveSettings(messageWindow, True)
		guitk.BCMessageWindowExecute(messageWindow)
	
	#-------------------------------------------------------------------------
	@staticmethod
	def showQuestion(message):
	
		messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxQuestion, message, True)
		guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "Yes")
		guitk.BCMessageWindowSetRejectButtonText(messageWindow, "No")
	
		return guitk.BCMessageWindowExecute(messageWindow)
	

# ==============================================================================
 
def _reject(window, application):
	
#	answer = showQuestion('Do you really want to quit SmartClip?')
	#answer = guitk.UserQuestion('Do you really want to quit SmartClip?')
	
#	if answer == guitk.constants.BCRetKey or answer == 1:
		
	application.getSmartClip()._restoreF11drawingSettings()
#	guitk.BCDestroyLater(window)
	guitk.BCDestroy(window)

			
# ==============================================================================
@setWaitCursor
def newClip(window, parent):
		
		# create mirrored clip as the last step
		if parent.DFT_MIRROR_CLIP:
			comp_items.SymmetricalClip(parent.smartClip)
		
		parent.getSmartClip()._restoreF11drawingSettings()
		guitk.BCDestroyLater(window)
		
#		print('Initialising a new CLIP')
#		
#		status = base.And(initialEntities)
#		
#		main()
		
# ==============================================================================

@ansa.session.defbutton('Tools', 'SmartClip', __doc__)
def main():
	
	main.__doc__ = __doc__
	
	try:
		dialog = SmartClipDialog()
	except Exception as e:
		print(format_exc())


# ==============================================================================

if __name__ == '__main__' and DEBUG :
	
	main()

		