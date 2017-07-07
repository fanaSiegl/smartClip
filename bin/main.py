
import os
import sys

import ansa
from ansa import base, guitk, constants


# ==============================================================================

try:
	# development version
	PATH_BIN = os.path.dirname(__file__)
	sys.path.append(PATH_BIN)
	import comp_items
	import comp_widgets
	import util
	
	print('Runnig devel version ', __file__)
	
except ImportError as e:
	# installed default version
	PATH_BIN = '/data/fem/users/siegl/tools/python/ansaTools/smartClip/default/bin'
	
	ansa.ImportCode(os.path.join(PATH_BIN, 'util.py'))
	ansa.ImportCode(os.path.join(PATH_BIN, 'comp_items.py'))
	ansa.ImportCode(os.path.join(PATH_BIN, 'comp_widgets.py'))

#import imp
#imp.reload(comp_items)
#imp.reload(comp_widgets)
ansa.ImportCode(os.path.join(PATH_BIN, 'comp_items.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'comp_widgets.py'))
#ansa.ImportCode(os.path.join(PATH_BIN, 'util.py'))

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

		#self.mainWindow = guitk.BCWizardCreate("SmartClip", guitk.constants.BCOnExitHide)
		self.mainWindow = guitk.BCWizardCreate("SmartClip", guitk.constants.BCOnExitDestroy)
		guitk.BCWindowSetInitSize(self.mainWindow, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWindow, False)
		
		self.page0 = comp_widgets.SelectClipTypePage(self, 'Select CLIP Type', 'Select a type of the CLIP')
		self.page1 = comp_widgets.SelectConPage(self, 'Select CON', 'Select the guiding clip edge - CON')
		self.page2 = comp_widgets.SelectClipNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip')
		self.page3 = comp_widgets.SelectClipContraNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip contra side')
		self.page3 = comp_widgets.MirrorClipPage(self, 'Mirror clip', 'Do you want to mirror created clip?')
		
		#self.statusBar = guitk.BCStatusBarCreate(self.mainWindow)
		
		guitk.BCWizardSetCurrentPageChangedFunction(self.mainWindow, self.controller, None)
		
#TODO: how to set this????
		guitk.BCWindowSetAcceptFunction(self.mainWindow, newClip, self)
			
		guitk.BCWindowSetMousePressFunction(self.mainWindow, self.mousePressedFunc, None)
# TODO: This shuts AMSA down.. why???!!!
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
					#self.smartClip.createNodesForConnector()
					self.smartClip.geomType().setStopDistances(hideMeasurements=False)
					self.smartClip.geomType().createCoorSystem()
					#self.smartClip.createConnector()
					
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
    
	def mousePressedFunc(self, w, mb, data):
		
		if mb == guitk.constants.BCLeftButton:
			print("Left mouse button pressed")
		elif mb == guitk.constants.BCMiddleButton:
			print("Middle mouse button pressed")
		elif mb == guitk.constants.BCRightButton:
			print("Right mouse button pressed")
		
		return 1
	
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

@ansa.session.defbutton('Tools', 'SmartClip')
def main():
	
	main.__doc__ = util.DESCRIPTION
	
	try:
		dialog = SmartClipDialog()
	except Exception as e:
		print(str(e))


# ==============================================================================

if __name__ == '__main__':
	
	main()

		