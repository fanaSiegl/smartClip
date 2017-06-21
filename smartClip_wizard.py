
import os
import sys

import ansa
from ansa import base, guitk, constants


# ==============================================================================

PATH_SELF = os.path.dirname(os.path.abspath(__file__))

try:
	sys.path.append(PATH_SELF)
	import smartClip

except ImportError as e:
	ansa.ImportCode(os.path.join(PATH_SELF, 'smartClip.py'))

#import imp
#imp.reload(smartClip)

# ==============================================================================

class PageContainer(object):
	
	def __init__(self):
		
		self.content = list()
		self.parentWizard = None
	
	#-------------------------------------------------------------------------
   
	def registerWidget(self, widget):
		
		self.parentWizard = widget.parentWidget
		self.content.append(widget)
		
		return len(self.content) - 1 
		
	#-------------------------------------------------------------------------

	def enableCurrentWidget(self):
		
		currentId =guitk.BCWizardCurrentIndex(self.parentWizard)
		
		for stackedWidget in self.content:
			if stackedWidget == self.content[currentId]:
				guitk.BCSetEnabled(stackedWidget.labelWidget, True)
				guitk.BCLabelSetText(stackedWidget.labelWidget,  '<b>%s</b>' % stackedWidget.label)
			else:
				guitk.BCSetEnabled(stackedWidget.labelWidget, False)
				guitk.BCLabelSetText(stackedWidget.labelWidget, stackedWidget.label)
	
	#-------------------------------------------------------------------------

	def activateWidget(self, newWidgetId):
		
		guitk.BCWidgetStackRaiseId(self.parentWizard, newWidgetId)
		
		self.enableCurrentWidget()
	
	#-------------------------------------------------------------------------
	
	def updateCurrentWidgetInfo(self):
		
		currentId =guitk.BCWizardCurrentIndex(self.parentWizard)
		currentWidget = self.content[currentId]
		
		currentWidget.updateInfo()
	
	#-------------------------------------------------------------------------
	
	def resetInfo(self):
		
		for stackedWidget in self.content:
			stackedWidget.resetInfo()
		

# ==============================================================================

class StackWidgetPage(object):
	
	def __init__(self, parent, label, description=''):
		
		self.parent =parent
		self.smartClip = self.parent.smartClip
		self.label = label
		self.description = description
		self.parentWidget = self.parent.mainWindow
		
		self.infoAttributeNames = list()
		
		# create content
		self.createBaseContent()
		self.createContent()
		
		# register the new page
		self.stackWidgetId = self.parent.pageContainer.registerWidget(self)

		guitk.BCSpacerCreate(self.contentLayout)

		guitk.BCWizardAddPage(self.parentWidget, self.frame, self.label, self.description,  "")
			
	#-------------------------------------------------------------------------
   
	def createBaseContent(self):
		
		self.frame = guitk.BCFrameCreate(self.parentWidget)
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
		
	#-------------------------------------------------------------------------
    
	def createContent(self):
		
		for i in self.description.split():
			self._addContentLine(i, i)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		pass
	
	#-------------------------------------------------------------------------

	def _addContentLine(self, label, valueAttrName):
			
		rowCount = guitk.BCGridLayoutRows(self.contentLayout)
		
		labelWidget = guitk.BCLabelCreate(self.contentLayout, label)
		valueWidget = guitk.BCLabelTickerCreate(self.contentLayout, '-')
		
		setattr(self, valueAttrName+'_label', labelWidget)
		setattr(self, valueAttrName, valueWidget)
		self.infoAttributeNames.append(valueAttrName)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, labelWidget, rowCount, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, valueWidget, rowCount, 1, guitk.constants.BCAlignLeft)
    
    #-------------------------------------------------------------------------

	def _setInfoAttributeValue(self, valueAttrName, value):

		valueWidget = getattr(self, valueAttrName)

		guitk.BCLabelSetText(valueWidget, '%s' % value)
	
	#-------------------------------------------------------------------------

	def resetInfo(self):
		
		for infoAttributeName in self.infoAttributeNames:
			self._setInfoAttributeValue(infoAttributeName, '-')

# ==============================================================================

class SelectConPage(StackWidgetPage):
	
	def createContent(self):
				
		# entity info
		self._addContentLine( 'Select CON', 'selectedCONid')
		self._addContentLine( 'x Lower Limit', 'xLow')
		self._addContentLine( 'x Upper Limit', 'xUp')
		self._addContentLine( 'y Lower Limit', 'yLow')
		self._addContentLine( 'y Upper Limit', 'yUp')
		self._addContentLine( 'z Lower Limit', 'zLow')
		self._addContentLine( 'z Upper Limit', 'zUp')
		
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.conSelected, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 1, 2, guitk.constants.BCAlignLeft)
		
	
	#-------------------------------------------------------------------------
    
	def conSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.selectedCon = None
		self.parent.controller(None, None, 1, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('selectedCONid', 'ID %s' % self.smartClip.selectedCon._id)
		self._setInfoAttributeValue('xLow', self.smartClip.xLow)
		self._setInfoAttributeValue('xUp', self.smartClip.xUp)
		self._setInfoAttributeValue('yLow', self.smartClip.yLow)
		self._setInfoAttributeValue('yUp', self.smartClip.yUp)
		self._setInfoAttributeValue('zLow', self.smartClip.zLow)
		self._setInfoAttributeValue('zUp', self.smartClip.zUp)
		
		#yLow

# ==============================================================================

class SelectClipNodesPage(StackWidgetPage):
	
	def createContent(self):
		
		# selector
		label = guitk.BCLabelTickerCreate(self.contentLayout, 'Select NODES')
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.nodesSelected, None)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, label, 0, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 0, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Selected NODES number', 'noOfNodes')
		self._addContentLine( 'Beam material ID', 'beamMID')
	
	#-------------------------------------------------------------------------
    
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.beamNodesCs = None
		self.parent.controller(None, None, 2, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip.beamNodesCs))
		
		#self._setInfoAttributeValue('noOfNodes', '%s (%s)' % (len(self.smartClip.beamNodesCs), ' '.join([str(node._id) for node in self.smartClip.beamNodesCs])))
		self._setInfoAttributeValue('beamMID', self.smartClip.beamCsMID)
		
		
# ==============================================================================

class SelectClipContraNodesPage(SelectClipNodesPage):
	
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.beamNodesCcs = None
		self.parent.controller(None, None, 3, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip.beamNodesCcs))
		self._setInfoAttributeValue('beamMID', self.smartClip.beamCcsMID)

# ==============================================================================

class SelectClipTypePage(StackWidgetPage):
	
	def createContent(self):	
		
		# clip type selector
		label = guitk.BCLabelCreate(self.contentLayout, 'Select CLIP geometrical type')
		clipTypeOptions = ['Standart', 'Example 2']
		self.clipGeomTypeComboBox = guitk.BCComboBoxCreate(self.contentLayout, clipTypeOptions)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, label, 0, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.clipGeomTypeComboBox, 0, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Geomerical type Info:', 'geomTypeInfo')
		
		# manufacturer selector
		label = guitk.BCLabelCreate(self.contentLayout, 'Select CLIP beam type')
		clipTypeOptions = ['AUDI', 'SKODA']
		self.clipBeamTypeComboBox = guitk.BCComboBoxCreate(self.contentLayout, clipTypeOptions)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, label, 2, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.clipBeamTypeComboBox, 2, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Beam type Info:', 'beamTypeInfo')
		
		# setup connections
		guitk.BCComboBoxSetCurrentIndexChangedFunction(self.clipBeamTypeComboBox, self.beamTypeChanged, None)
		guitk.BCComboBoxSetCurrentIndexChangedFunction(self.clipGeomTypeComboBox, self.geomTypeChanged, None)
				
		# set initial values
		guitk.BCComboBoxSetCurrentItem(self.clipBeamTypeComboBox, SmartClipDialog.DFT_TYPE_BEAM)
		guitk.BCComboBoxSetCurrentItem(self.clipGeomTypeComboBox, SmartClipDialog.DFT_TYPE_GEOM)
		
		self.geomTypeChanged(self.clipGeomTypeComboBox, SmartClipDialog.DFT_TYPE_GEOM, None)
		self.beamTypeChanged(self.clipBeamTypeComboBox, SmartClipDialog.DFT_TYPE_BEAM, None)
	
	#-------------------------------------------------------------------------

	def geomTypeChanged(self, comboBox, index, data):
		
		self._setInfoAttributeValue('geomTypeInfo', 'This is an info about clip topology of the type: %s.' % index)
		
		
		
		if index == 0:
			guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, os.path.join(PATH_SELF, 'image02_s.png'))
		elif index == 1:
			guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, os.path.join(PATH_SELF, 'image03_s.png'))
		
		SmartClipDialog.DFT_TYPE_GEOM = index
	
	#-------------------------------------------------------------------------

	def beamTypeChanged(self, comboBox, index, data):
		
		self._setInfoAttributeValue('beamTypeInfo', 'This is an info about beam structure of the type: %s.' % index)
		
		
		guitk.BCLabelSetIconFileName(self.beamTypeInfo_label, os.path.join(PATH_SELF, 'image04_s.png'))
		
		SmartClipDialog.DFT_TYPE_BEAM = index
		
# ==============================================================================

class SmartClipDialog(object):
	
	WIDTH = 600
	HEIGTH = 400
	
	DFT_TYPE_BEAM = 0
	DFT_TYPE_GEOM = 0
	
	def __init__(self):
		
		self.initialEntities = base.CollectEntities(constants.ABAQUS, None, ['SHELL', 'FACE', 'BEAM', 'CONNECTOR', 'ORIENTATION_R'], filter_visible=True )
		self.smartClip = smartClip.SmartClip()
		self.pageContainer = PageContainer()

		self.mainWindow = guitk.BCWizardCreate("SmartClip", guitk.constants.BCOnExitDestroy)
		guitk.BCWindowSetInitSize(self.mainWindow, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWindow, False)
		
		page0 = SelectClipTypePage(self, 'Select CLIP Type', 'Select a type of the CLIP')
		page1 = SelectConPage(self, 'Select CON', 'Select the guiding clip edge - CON')
		page2 = SelectClipNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip')
		page3 = SelectClipContraNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip contra side')
		
		guitk.BCWizardSetCurrentPageChangedFunction(self.mainWindow, self.controller, None)

#TODO: how to set this????
		guitk.BCWindowSetAcceptFunction(self.mainWindow, newClip, self)
			
		guitk.BCWindowSetMousePressFunction(self.mainWindow, self.mousePressedFunc, None)
		
		guitk.BCWindowSetSaveSettings(self.mainWindow, True)
		guitk.BCShow(self.mainWindow)
	
	#-------------------------------------------------------------------------

	def controller(self, wizard, oldIndex, stepId, data):
		
		if stepId == 0:
			print(stepId)
		elif stepId == 1:
			
			if self.smartClip.selectedCon is None:
				try:
					self.smartClip.setBaseFaces()
					self.smartClip.createNodesForConnector()
					self.smartClip.setStopDistances(hideMeasurements=False)
					self.smartClip.createCoorSystem()
					self.smartClip.createConnector()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#self.next()
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)
				
			else:
				
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
				
		elif stepId == 2:
			
			if self.smartClip.beamNodesCs is None:
				try:
					self.smartClip.hideMeasurements()
					self.smartClip.hidePoints()
					self.smartClip.hideAllFaces()
					self.smartClip.createBeamsConnectorClipSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#self.next()
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
		elif stepId == 3:
			
			if self.smartClip.beamNodesCcs is None:
				try:
					self.smartClip.hideAllFaces()
					self.smartClip.createBeamsConnectorClipContraSide()
					
					self.pageContainer.updateCurrentWidgetInfo()
					
					#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
					if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
						guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					#guitk.BCSetEnabled(self.pushButtonNext, False)
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, False)
			else:
				if not guitk.BCWizardIsNextButtonEnabled(self.mainWindow):
					guitk.BCWizardSetNextButtonEnabled(self.mainWindow, True)
				#guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
		
		elif stepId == 4:
			# initiate a new step
			self.pageContainer.activateWidget(0)
			#guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
			# reset smartClip
			self.resetSmartClip()
			
			#self.next()
			
	#-------------------------------------------------------------------------
    
	def resetSmartClip(self, window=None, data=None):
		
		self.pageContainer.resetInfo()
		self.smartClip.__init__()
		
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
    
	def showInfoMessage(self, message):
		
		#"Some <b>errors</b> have been detected.<br>Do you want to proceed?"
		messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxInformation, message, True)
		guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "OK")
		#guitk.BCMessageWindowSetRejectButtonText(messageWindow, "No")
		guitk.BCMessageWindowSetRejectButtonVisible(messageWindow, False)
		answer = guitk.BCMessageWindowExecute(messageWindow)
		if answer == guitk.constants.BCRetKey:
			print("Accept")
		elif answer == guitk.constants.BCEscKey:
			print("Reject")
		elif answer == guitk.constants.BCQuitAll:
			print("Quitall")
	
	#-------------------------------------------------------------------------
    
	def showCriticalMessage(self, message):
		
		messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxCritical, message, True)
		#guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "Yes")
		#guitk.BCMessageWindowSetRejectButtonText(messageWindow, "No")
		guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "OK")
		guitk.BCMessageWindowSetRejectButtonVisible(messageWindow, False)
		
		#guitk.BCWindowSetInitGeometry(messageWindow, 100, 100, 200, 200)
		#guitk.BCWindowSetPosition(messageWindow, 500, 500)
		guitk.BCWindowSetSaveSettings(messageWindow, True)
		answer = guitk.BCMessageWindowExecute(messageWindow)
		if answer == guitk.constants.BCRetKey:
			print("Accept")
		elif answer == guitk.constants.BCEscKey:
			print("Reject")
		elif answer == guitk.constants.BCQuitAll:
			print("Quitall")

# ==============================================================================

def newClip(window, parent):
		
		initialEntities = parent.initialEntities
		
		guitk.BCDestroyLater(window)
		#guitk.BCDestroy(window)
		
		print('Initialising a new CLIP')
		
		status = base.And(initialEntities)
		
		main()
		
# ==============================================================================

@ansa.session.defbutton('Tool', 'SmartClip')
def main():
	try:
		dialog = SmartClipDialog()
	except Exception as e:
		print(str(e))

# ==============================================================================

#if __name__ == '__main__':
#	main()

		