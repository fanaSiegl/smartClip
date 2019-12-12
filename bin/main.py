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
if 'win' in sys.platform:
	toolName = os.path.splitext(os.path.basename(__file__))[0].replace('tool_', '')
	PATH_SELF = os.path.join(os.environ['ANSA_TOOLS'], toolName, 'default', 'bin')
else:
	PATH_SELF = os.path.dirname(os.path.realpath(__file__))

ansa.ImportCode(os.path.join(PATH_SELF, 'domain', 'util.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'domain', 'comp_items.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'comp_widgets.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'presentation', 'page_coorSys.py'))

from comp_items import SmartClipException

# ==============================================================================

DEBUG = 1

# ==============================================================================

def setWaitCursor(method, *args):
	def methodWithWaitCursor(*args):
		
#		parent = args[0]
#		guitk.BCSetApplicationOverrideCursor(guitk.constants.BCCursorWait)
		try:
			method(*args)
		except Exception as e:
			print(format_exc())
			base.BlockRedraws(False)
			base.RedrawAll()
			showCriticalMessage(str(e))
			
			guitk.BCRestoreApplicationOverrideCursor()

	return methodWithWaitCursor
	
# ==============================================================================

class SmartClipDialog(object):
	
	WIDTH = 600
	HEIGTH = 400
	
	DFT_TYPE_BEAM = 0
	DFT_TYPE_GEOM = 0
	DFT_MIRROR_CLIP = True
	
	def __init__(self):
		
#		self.initialEntities = base.CollectEntities(constants.ABAQUS, None, ['SHELL', 'FACE', 'BEAM', 'CONNECTOR', 'ORIENTATION_R'], filter_visible=True )
		self.smartClip = comp_items.SmartClip()
		self.pageContainer = comp_widgets.PageContainer()
		
		revision, modifiedBy, lastModified = util.getVersionInfo()
		
		self.mainWizard = guitk.BCWizardCreate("SmartClip (%s)" % revision, guitk.constants.BCOnExitDestroy)
		guitk.BCWindowSetInitSize(self.mainWizard, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWizard, False)
		
		self.pages = list()
		self.pages.append(comp_widgets.SelectClipTypePage(self, 'Select CLIP Type', 'Select a type of the CLIP'))
		self.pages.append(page_coorSys.CoorSysModificationPage(self))
		guitk.BCWizardAddPage(self.mainWizard, self.pages[1].getFrame(), self.pages[1].TITLE, self.pages[1].DESCRIPTION,  self.pages[1].INFO)
		self.pageContainer.content.append(self.pages[1])
		
		self.pages.append(comp_widgets.SelectConPage(self, 'STOP distances', 'Select faces for connector STOP criteria if necessary'))
		self.pages.append(comp_widgets.SelectClipNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip'))
		self.pages.append(comp_widgets.SelectClipContraNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip contra side'))
		self.pages.append(comp_widgets.MirrorClipPage(self, 'Mirror clip', 'Do you want to mirror created clip?'))
				
		guitk.BCWizardSetCurrentPageChangedFunction(self.mainWizard, self.controller, None)
		
		guitk.BCWindowSetAcceptFunction(self.mainWizard, newClip, self)
			
		guitk.BCWindowSetRejectFunction(self.mainWizard, _reject, self)
		guitk.BCWindowSetSaveSettings(self.mainWizard, True)
		guitk.BCShow(self.mainWizard)
	
	#-------------------------------------------------------------------------

	def getSmartClip(self):
		
		return self.smartClip
		
	#-------------------------------------------------------------------------
	@setWaitCursor
	def controller(self, wizard, oldIndex, stepId, data):
		
		if stepId == 1:
			try:
				self.pages[1].activated()
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
			except SmartClipException as e:
				self._showStatusBarMessage(str(e))
				showCriticalMessage(str(e))					
				if guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, False)

			self.pageContainer.updateCurrentWidgetInfo()
			
		elif stepId == 2:
			guitk.BCSetApplicationOverrideCursor(guitk.constants.BCCursorWait)
			try:				
				
				self.smartClip.geomType().setStopDistances(hideMeasurements=False)
									
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
			except SmartClipException as e:
				self._showStatusBarMessage(str(e))
				showCriticalMessage(str(e))
				#guitk.BCSetEnabled(self.pushButtonNext, False)
				if guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, False)
		
				else:
					
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
						guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
					#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
			self.pageContainer.updateCurrentWidgetInfo()
			guitk.BCRestoreApplicationOverrideCursor()
			
			
		
		elif stepId == 3:
			
			if not self.smartClip.beamType().beamsCsDefined:
				try:
					self.smartClip.beamType().checkClipSideNodeRedefinition()
					
					self.smartClip.beamType().createNodesForConnector()
					self.smartClip.beamType().createConnector()
					
					self.smartClip.geomType().hideMeasurements()
					self.smartClip.geomType().hidePoints()
					comp_items.hideAllFaces()
					self.smartClip.beamType().createBeamsConnectorClipSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#self.next()
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
						guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
				except SmartClipException as e:
					self._showStatusBarMessage(str(e))
					showCriticalMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					if guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
						guitk.BCWizardSetNextButtonEnabled(self.mainWizard, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
		elif stepId == 4:
			
			if not self.smartClip.beamType().beamsCcsDefined:
				try:
					comp_items.hideAllFaces()
					
					self.smartClip.beamType().checkClipContraSideNodeRedefinition()
					
					self.smartClip.beamType().createBeamsConnectorClipContraSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
						guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
				except SmartClipException as e:
					self._showStatusBarMessage(str(e))
					showCriticalMessage(str(e))					
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					if guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
						guitk.BCWizardSetNextButtonEnabled(self.mainWizard, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWizard):
					guitk.BCWizardSetNextButtonEnabled(self.mainWizard, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
	
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
    
	def _showStatusBarMessage(self, message):
		
		print(message)
		#guitk.BCStatusBarTimedMessage(self.statusBar, message, 2000)

# ==============================================================================
 
def _reject(window, application):
	
#	answer = showQuestion('Do you really want to quit SmartClip?')
	#answer = guitk.UserQuestion('Do you really want to quit SmartClip?')
	
#	if answer == guitk.constants.BCRetKey or answer == 1:
		
	application.getSmartClip()._restoreF11drawingSettings()
#	guitk.BCDestroyLater(window)
	guitk.BCDestroy(window)

	
# ==============================================================================
    
def showCriticalMessage(message):
	
#	print(message)
	#guitk.UserWarning(message)
#	guitk.UserError(message)
	messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxCritical, message, True)
	guitk.BCMessageWindowSetRejectButtonVisible(messageWindow, False)
	guitk.BCMessageWindowExecute(messageWindow)
	
		
# ==============================================================================

def showQuestion(message):
		
	
	messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxQuestion, message, True)
	guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "Yes")
	guitk.BCMessageWindowSetRejectButtonText(messageWindow, "No")

	return guitk.BCMessageWindowExecute(messageWindow)
		
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
		print(str(e))


# ==============================================================================

if __name__ == '__main__' and DEBUG :
	
	main()

		