
import os
import sys

import ansa
from ansa import base, guitk, constants

# ==============================================================================

PATH_SELF = os.path.dirname(os.path.realpath(__file__))

ansa.ImportCode(os.path.join(PATH_SELF, 'util.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'comp_items.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'comp_widgets.py'))

from comp_items import SmartClipException

# ==============================================================================

class SmartClipDialog(object):
	
	WIDTH = 600
	HEIGTH = 400
	
	DFT_TYPE_BEAM = 0
	DFT_TYPE_GEOM = 0
	DFT_MIRROR_CLIP = True
	
	def __init__(self):
		
		self.initialEntities = base.CollectEntities(constants.ABAQUS, None, ['SHELL', 'FACE', 'BEAM', 'CONNECTOR', 'ORIENTATION_R'], filter_visible=True )
		self.smartClip = comp_items.SmartClip()
		self.pageContainer = comp_widgets.PageContainer()
		
		revision, modifiedBy, lastModified = util.getVersionInfo()
		
		self.mainWindow = guitk.BCWizardCreate("SmartClip (%s)" % revision, guitk.constants.BCOnExitDestroy)
		guitk.BCWindowSetInitSize(self.mainWindow, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWindow, False)
		
		self.page0 = comp_widgets.SelectClipTypePage(self, 'Select CLIP Type', 'Select a type of the CLIP')
		self.page1 = comp_widgets.SelectConPage(self, 'Select CON', 'Select the guiding clip edge - CON')
		self.page2 = comp_widgets.SelectClipNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip')
		self.page3 = comp_widgets.SelectClipContraNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip contra side')
		self.page3 = comp_widgets.MirrorClipPage(self, 'Mirror clip', 'Do you want to mirror created clip?')
				
		guitk.BCWizardSetCurrentPageChangedFunction(self.mainWindow, self.controller, None)
		
		guitk.BCWindowSetAcceptFunction(self.mainWindow, newClip, self)
			
		guitk.BCWindowSetRejectFunction(self.mainWindow, _reject, self)
		guitk.BCWindowSetSaveSettings(self.mainWindow, True)
		guitk.BCShow(self.mainWindow)
	
	#-------------------------------------------------------------------------

	def getSmartClip(self):
		
		return self.smartClip
		
	#-------------------------------------------------------------------------

	def controller(self, wizard, oldIndex, stepId, data):
		
		if stepId == 1:
			if self.smartClip.geomType().selectedCon is None:
				try:
					self.smartClip.geomType().setBaseFaces()
					
					guitk.BCSetApplicationOverrideCursor(guitk.constants.BCCursorWait)
					#self.smartClip.createNodesForConnector()
					self.smartClip.geomType().setStopDistances(hideMeasurements=False)
					self.smartClip.geomType().createCoorSystem()
					#self.smartClip.createConnector()
					
					#self.pageContainer.updateCurrentWidgetInfo()
										
					#self.next()
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except SmartClipException as e:
					self._showStatusBarMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					if guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)

				self.pageContainer.updateCurrentWidgetInfo()
				
			else:
				
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			guitk.BCRestoreApplicationOverrideCursor()
		
		elif stepId == 2:
			
			if not self.smartClip.beamType().beamsCsDefined:
				try:
					self.smartClip.beamType().createNodesForConnector()
					self.smartClip.beamType().createConnector()
					
					self.smartClip.geomType().hideMeasurements()
					self.smartClip.geomType().hidePoints()
					comp_items.hideAllFaces()
					self.smartClip.beamType().createBeamsConnectorClipSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#self.next()
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except SmartClipException as e:
					self._showStatusBarMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					if guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
		elif stepId == 3:
			
			if not self.smartClip.beamType().beamsCcsDefined:
				try:
					comp_items.hideAllFaces()
					self.smartClip.beamType().createBeamsConnectorClipContraSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except SmartClipException as e:
					self._showStatusBarMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					if guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
					
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
	
	answer = showQuestion('Do you really want to quit SmartClip?')
	#answer = guitk.UserQuestion('Do you really want to quit SmartClip?')
	
	if answer == guitk.constants.BCRetKey or answer == 1:
		
		application.getSmartClip()._restoreF11drawingSettings()
		guitk.BCDestroyLater(window)
	#elif answer == guitk.constants.BCEscKey:
	#	print("Reject")
	#elif answer == guitk.constants.BCQuitAll:
	#	guitk.BCDestroyLater(window)
	
# ==============================================================================
    
def showCriticalMessage(message):
	
	print(message)
	#guitk.UserWarning(message)
	#guitk.UserError(message)
		
# ==============================================================================

def showQuestion(message):
		
	
	messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxQuestion, message, True)
	guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "Yes")
	guitk.BCMessageWindowSetRejectButtonText(messageWindow, "No")

	return guitk.BCMessageWindowExecute(messageWindow)
		
# ==============================================================================

def newClip(window, parent):
		
		initialEntities = parent.initialEntities
		# create mirrored clip as the last step
		if parent.DFT_MIRROR_CLIP:
			comp_items.SymmetricalClip(parent.smartClip)
		
		guitk.BCDestroyLater(window)
		#guitk.BCDestroy(window)
		
		print('Initialising a new CLIP')
		
		status = base.And(initialEntities)
		
		main()
		
# ==============================================================================

@ansa.session.defbutton('Tools', 'SmartClip', util.DESCRIPTION)
def main():
	
	main.__doc__ = util.DESCRIPTION
	
	try:
		dialog = SmartClipDialog()
	except Exception as e:
		print(str(e))


# ==============================================================================

if __name__ == '__main__':
	
	main()

		