
import os
import sys

import ansa
from ansa import guitk
from ansa import constants

import smartClip

import imp
#imp.reload(smartClip)


# ==============================================================================

PATH_SELF = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================

class StackedWidgetsContainer(object):
	
	content = list()
	parentStackWidget = None
	
	@classmethod
	def registerWidget(cls, widget):
		
		cls.parentStackWidget = widget.parentStackWidget
		cls.content.append(widget)
		
		return len(cls.content) - 1 
	
	#-------------------------------------------------------------------------
   
	@classmethod
	def next(cls):
		
		currentStackId = guitk.BCWidgetStackCurrentId(cls.parentStackWidget)
		newWidgetId = currentStackId+1
		
		#if newWidgetId == len(cls.content):
		#	return currentStackId
			
		guitk.BCWidgetStackRaiseId(cls.parentStackWidget, newWidgetId)
		
		cls.enableCurrentWidget()
		
		return newWidgetId
	
	#-------------------------------------------------------------------------
   
	@classmethod
	def back(cls):
		
		currentStackId = guitk.BCWidgetStackCurrentId(cls.parentStackWidget)
		newWidgetId = currentStackId-1
		
		if newWidgetId < 0:
			return 0
		
		guitk.BCWidgetStackRaiseId(cls.parentStackWidget, newWidgetId)
		
		cls.enableCurrentWidget()
		
		return newWidgetId
		
	#-------------------------------------------------------------------------
   
	@classmethod
	def enableCurrentWidget(cls):
		
		currentId =guitk.BCWidgetStackCurrentId(cls.parentStackWidget)
		
		for stackedWidget in cls.content:
			if stackedWidget == cls.content[currentId]:
				guitk.BCSetEnabled(stackedWidget.labelWidget, True)
				guitk.BCLabelSetText(stackedWidget.labelWidget,  '<b>%s</b>' % stackedWidget.label)
			else:
				guitk.BCSetEnabled(stackedWidget.labelWidget, False)
				guitk.BCLabelSetText(stackedWidget.labelWidget, stackedWidget.label)
	
	#-------------------------------------------------------------------------
   
	@classmethod
	def activateWidget(cls, newWidgetId):
		
		guitk.BCWidgetStackRaiseId(cls.parentStackWidget, newWidgetId)
		
		cls.enableCurrentWidget()
	
	#-------------------------------------------------------------------------
	
	@classmethod
	def updateCurrentWidgetInfo(cls):
		
		currentId =guitk.BCWidgetStackCurrentId(cls.parentStackWidget)
		currentWidget = cls.content[currentId]
		
		currentWidget.updateInfo()
	
	#-------------------------------------------------------------------------
	
	@classmethod
	def resetInfo(cls):
		
		for stackedWidget in cls.content:
			stackedWidget.resetInfo()
		

# ==============================================================================

class StackWidgetPage(object):
	
	def __init__(self, parentWidget, label, description=''):
		
		self.parentWidget =parentWidget
		self.smartClip = self.parentWidget.smartClip
		self.label = label
		self.description = description
		self.parentStackWidget = self.parentWidget.stackWidget
		self.parentPageLabelsLayout = self.parentWidget.pageLabelsLayout
		
		self.infoAttributeNames = list()
		
		# create content
		self.createBaseContent()
		self.createContent()
		
		# register the new page
		self.stackWidgetId = StackedWidgetsContainer.registerWidget(self)
		
		guitk.BCSpacerCreate(self.layout)
		guitk.BCWidgetStackAddWidget(self.parentStackWidget, self.layout, self.stackWidgetId)
		
		StackedWidgetsContainer.enableCurrentWidget()
	
	#-------------------------------------------------------------------------
   
	def createBaseContent(self):
		
		#self.labelWidget = guitk.BCLabelTickerCreate(self.parentPageLabelsLayout, '<b>%s</b>' % self.label)
		self.labelWidget = guitk.BCLabelCreate(self.parentPageLabelsLayout, '<b>%s</b>' % self.label)
		

		self.layout = guitk.BCVBoxCreate(self.parentStackWidget)
		
		guitk.BCLabelTickerCreate(self.layout,  '<b>%s</b>' % self.description)
		guitk.BCSeparatorCreate(self.layout)
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.layout, 5, 2)
		
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
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.layout, 5, 3)
				
		# selector
		#label = guitk.BCLabelTickerCreate(self.contentLayout, 'Select CON')
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.conSelected, None)
		
		#guitk.BCGridLayoutAddWidget(self.contentLayout, label, 0, 0, guitk.constants.BCAlignLeft)
		#guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 0, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Select CON', 'selectedCONid')
		self._addContentLine( 'x Lower Limit', 'xLow')
		self._addContentLine( 'x Upper Limit', 'xUp')
		self._addContentLine( 'y Lower Limit', 'yLow')
		self._addContentLine( 'y Upper Limit', 'yUp')
		self._addContentLine( 'z Lower Limit', 'zLow')
		self._addContentLine( 'z Upper Limit', 'zUp')
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 0, 2, guitk.constants.BCAlignLeft)
		
	
	#-------------------------------------------------------------------------
    
	def conSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.selectedCon = None
		self.parentWidget.controller(1)
	
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
	
	#-------------------------------------------------------------------------
    
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.beamNodesCs = None
		self.parentWidget.controller(2)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip.beamNodesCs))
		#self._setInfoAttributeValue('noOfNodes', '%s (%s)' % (len(self.smartClip.beamNodesCs), ' '.join([str(node._id) for node in self.smartClip.beamNodesCs])))
		
		
# ==============================================================================

class SelectClipContraNodesPage(SelectClipNodesPage):
	
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip.beamNodesCcs = None
		self.parentWidget.controller(3)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip.beamNodesCcs))

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
		self.beamTypeChanged(self.clipBeamTypeComboBox, 0, None)
		self.geomTypeChanged(self.clipGeomTypeComboBox, 0, None)
	
	#-------------------------------------------------------------------------

	def geomTypeChanged(self, comboBox, index, data):
		
		self._setInfoAttributeValue('geomTypeInfo', 'This is an info about clip topology of the type: %s.' % index)
		
		
		
		if index == 0:
			guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, os.path.join(PATH_SELF, 'image02_s.png'))
		elif index == 1:
			guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, os.path.join(PATH_SELF, 'image03_s.png'))
	
	#-------------------------------------------------------------------------

	def beamTypeChanged(self, comboBox, index, data):
		
		self._setInfoAttributeValue('beamTypeInfo', 'This is an info about beam structure of the type: %s.' % index)
		
		
		guitk.BCLabelSetIconFileName(self.beamTypeInfo_label, os.path.join(PATH_SELF, 'image04_s.png'))
		
# ==============================================================================

class SmartClipDialog(object):
	
	WIDTH = 600
	HEIGTH = 400
	
	def __init__(self):
		
		self.smartClip = smartClip.SmartClip()
		
		self.mainWindow = guitk.BCWindowCreate("SmartClip", guitk.constants.BCOnExitDestroy)
		guitk.BCWindowSetInitSize(self.mainWindow, self.WIDTH, self.HEIGTH)
		guitk.BCWindowSetSaveSettings(self.mainWindow, False)
		
		
		self.mainFrame = guitk.BCFrameCreate(self.mainWindow)
		baseLayout = guitk.BCBoxLayoutCreate(self.mainFrame, guitk.constants.BCHorizontal)
		self.pageLabelsLayout = guitk.BCVBoxCreate(baseLayout)
		
		BCSeparator_1 = guitk.BCSeparatorCreate(baseLayout)
		
		self.stackWidget = guitk.BCWidgetStackCreate(baseLayout)
		
		page0 = SelectClipTypePage(self, 'Select CLIP Type', 'Select a type of the CLIP')
		page1 = SelectConPage(self, 'Select CON', 'Select the guiding clip edge - CON')
		page2 = SelectClipNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip')
		page3 = SelectClipContraNodesPage(self, 'Select NODES', 'Select NODES for CONNECTOR on the clip contra side')
		
		BCSpacer_1 = guitk.BCSpacerCreate(self.pageLabelsLayout)
		
		# create buttons
		guitk.BCSeparatorSetOrientation(BCSeparator_1, guitk.constants.BCVertical)
		dbb = guitk.BCDialogButtonBoxCreate(self.mainWindow)
		
		#BCSpacer_44 = guitk.BCSpacerCreate(dbb)
		dialogButtonLayout = guitk.BCDialogButtonBoxGetGridLayout(dbb)
		guitk.BCGridLayoutSetColStretch(dialogButtonLayout, 0, 1)
		okButton = guitk.BCDialogButtonBoxGetAcceptButton(dbb)
		#guitk.BCSetVisible(okButton, False)
		
		self.pushButtonBack = guitk.BCPushButtonCreate(dbb, "< Back", self.back, self.stackWidget)
		self.pushButtonNext = guitk.BCPushButtonCreate(dbb, "Next >", self.next, self.stackWidget)
		guitk.BCDialogButtonBoxAddButton(dbb, self.pushButtonBack)
		guitk.BCDialogButtonBoxAddButton(dbb, self.pushButtonNext)
			
		guitk.BCWindowSetMousePressFunction(self.mainWindow, self.mousePressedFunc, None)
		
		guitk.BCShow(self.mainWindow)
	
	#-------------------------------------------------------------------------

	def controller(self, stepId):
		
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
					
					StackedWidgetsContainer.updateCurrentWidgetInfo()
					
					#self.next()
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					guitk.BCSetEnabled(self.pushButtonNext, False)
				
			else:
				guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
				
		elif stepId == 2:
			
			if self.smartClip.beamNodesCs is None:
				try:
					self.smartClip.hideMeasurements()
					self.smartClip.hidePoints()
					self.smartClip.hideAllFaces()
					self.smartClip.createBeamsConnectorClipSide()
					
					StackedWidgetsContainer.updateCurrentWidgetInfo()
					
					self.next()
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					guitk.BCSetEnabled(self.pushButtonNext, False)
			else:
				guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
		elif stepId == 3:
			
			if self.smartClip.beamNodesCcs is None:
				try:
					self.smartClip.hideAllFaces()
					self.smartClip.createBeamsConnectorClipContraSide()
					
					StackedWidgetsContainer.updateCurrentWidgetInfo()
					
					guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
				except smartClip.SmartClipException as e:
					self.showCriticalMessage(str(e))
					guitk.BCSetEnabled(self.pushButtonNext, False)
			else:
				guitk.BCButtonSetText(self.pushButtonNext, 'Finish')
		
		elif stepId == 4:
			# initiate a new step
			StackedWidgetsContainer.activateWidget(0)
			guitk.BCButtonSetText(self.pushButtonNext, 'Next >')
			
			# reset smartClip
			self.resetSmartClip()
			
			self.next()
			
	#-------------------------------------------------------------------------
    
	def resetSmartClip(self):
		
		
		StackedWidgetsContainer.resetInfo()
		self.smartClip.__init__()
		

	#-------------------------------------------------------------------------
    
	def next(self, buttonWidget=None, stackWidget=None):
	
		stepId = StackedWidgetsContainer.next()
		self.controller(stepId)
	
	#-------------------------------------------------------------------------
    
	def back(self, buttonWidget=None, stackWidget=None):
	
		stepId = StackedWidgetsContainer.back()
		
		guitk.BCSetEnabled(self.pushButtonNext, True)
		
		self.controller(stepId)
	
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

@ansa.session.defbutton('Mesh', 'SmartClip')
def runSmartClip():
	try:
		dialog = SmartClipDialog()
	except Exception as e:
		print(str(e))

# ==============================================================================

#if __name__ == '__main__':
#	runSmartClip()

		