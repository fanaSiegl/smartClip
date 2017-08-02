
import os
import sys

import ansa
from ansa import base, guitk, constants


# ==============================================================================

PATH_BIN = os.path.dirname(os.path.abspath(__file__))
PATH_RES = os.path.normpath(os.path.join(PATH_BIN, '..', 'res'))

try:
	sys.path.append(PATH_BIN)
	import util
	import comp_items
	
#	print('Runnig devel version ', __file__)
	
except ImportError as e:
	ansa.ImportCode(os.path.join(PATH_BIN, 'util.py'))
	ansa.ImportCode(os.path.join(PATH_BIN, 'comp_items.py'))
	
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
   
	def smartClip(self):
		
		 return self.parent.getSmartClip()
			
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
		
		# create buttons for stop distance redefinition
		stopDistances = ['xLow', 'xUp', 'yLow', 'yUp', 'zLow', 'zUp']
		for i, stopDistanceName in enumerate(stopDistances):
			button = guitk.BCPushButtonCreate(self.contentLayout, "Select",
				#lambda buttonWidget, stopDistanceName: self.smartClip().redefineStopDistance(stopDistanceName),
				lambda buttonWidget, stopDistanceName: self.redefineStopDistance(button, stopDistanceName),
			stopDistanceName)
			
			guitk.BCGridLayoutAddWidget(self.contentLayout, button, 2+i, 2, guitk.constants.BCAlignLeft)
	
	#-------------------------------------------------------------------------
    
	def redefineStopDistance(self, buttonWidget, stopDistanceName):
		
		try:
			self.smartClip().redefineStopDistance(stopDistanceName)
		except Exception as e:
			self.parent._showStatusBarMessage(str(e))
		
		self.updateInfo()
	
	#-------------------------------------------------------------------------
    
	def conSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip().selectedCon = None
		self.parent.controller(None, None, 1, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('selectedCONid', 'ID %s' % self.smartClip().geomType().selectedCon._id)
		self._setInfoAttributeValue('xLow', self.smartClip().geomType().xLow)
		self._setInfoAttributeValue('xUp', self.smartClip().geomType().xUp)
		self._setInfoAttributeValue('yLow', self.smartClip().geomType().yLow)
		self._setInfoAttributeValue('yUp', self.smartClip().geomType().yUp)
		self._setInfoAttributeValue('zLow', self.smartClip().geomType().zLow)
		self._setInfoAttributeValue('zUp', self.smartClip().geomType().zUp)
		
		#yLow

# ==============================================================================

class SelectClipNodesPage(StackWidgetPage):
	
	def createContent(self):
				
		# entity info
		self._addContentLine( 'Selected NODES', 'noOfNodes')
		self._addContentLine( 'Beam material ID', 'beamMID')
		
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.nodesSelected, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 1, 2, guitk.constants.BCAlignLeft)
	
	#-------------------------------------------------------------------------
    
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip().beamType().beamsCsDefined = False
		self.parent.controller(None, None, 2, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip().beamType().beamNodesCs))
		
		#self._setInfoAttributeValue('noOfNodes', '%s (%s)' % (len(self.smartClip().beamNodesCs), ' '.join([str(node._id) for node in self.smartClip().beamNodesCs])))
		self._setInfoAttributeValue('beamMID', self.smartClip().beamType().beamCsMID)
		
		
# ==============================================================================

class SelectClipContraNodesPage(SelectClipNodesPage):
	
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip().beamType().beamsCcsDefined = False
		self.parent.controller(None, None, 3, None)
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('noOfNodes', len(self.smartClip().beamType().beamNodesCcs))
		self._setInfoAttributeValue('beamMID', self.smartClip().beamType().beamCcsMID)

# ==============================================================================

class SelectClipTypePage(StackWidgetPage):
	
	def createContent(self):	
		
		# clip type selector
		label = guitk.BCLabelCreate(self.contentLayout, 'Select CLIP geometrical type')
		clipTypeOptions = list(comp_items.clipGeomTypeRegistry.keys())
		self.clipGeomTypeComboBox = guitk.BCComboBoxCreate(self.contentLayout, clipTypeOptions)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, label, 0, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.clipGeomTypeComboBox, 0, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Geomerical type Info:', 'geomTypeInfo')
		
		# manufacturer selector
		label = guitk.BCLabelCreate(self.contentLayout, 'Select CLIP beam type')
		clipTypeOptions = list(comp_items.clipBeamTypeRegistry.keys())
		self.clipBeamTypeComboBox = guitk.BCComboBoxCreate(self.contentLayout, clipTypeOptions)
		
		guitk.BCGridLayoutAddWidget(self.contentLayout, label, 2, 0, guitk.constants.BCAlignLeft)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.clipBeamTypeComboBox, 2, 1, guitk.constants.BCAlignLeft)
		
		# entity info
		self._addContentLine( 'Beam type Info:', 'beamTypeInfo')
		
		# setup connections
		guitk.BCComboBoxSetCurrentIndexChangedFunction(self.clipBeamTypeComboBox, self.beamTypeChanged, None)
		guitk.BCComboBoxSetCurrentIndexChangedFunction(self.clipGeomTypeComboBox, self.geomTypeChanged, None)
				
		# set initial values
		guitk.BCComboBoxSetCurrentItem(self.clipBeamTypeComboBox, self.parent.DFT_TYPE_BEAM)
		guitk.BCComboBoxSetCurrentItem(self.clipGeomTypeComboBox, self.parent.DFT_TYPE_GEOM)


		#guitk.BCLabelSetIconFileName(self.beamTypeInfo_label, self.smartClip().ICON)
		#self._setInfoAttributeValue('beamTypeInfo', self.smartClip().INFO)

#TODO: this will be replaced with other geometrical types loaded from comp_items		
		self.geomTypeChanged(self.clipGeomTypeComboBox, self.parent.DFT_TYPE_GEOM, None)
		self.beamTypeChanged(self.clipBeamTypeComboBox, self.parent.DFT_TYPE_BEAM, None)
	
	#-------------------------------------------------------------------------

	def geomTypeChanged(self, comboBox, index, data):
				
		geomType = guitk.BCComboBoxGetText(comboBox, index)
		self.parent.setTypeGeom(index, geomType)
		
		self._setInfoAttributeValue('geomTypeInfo', self.smartClip().geomType().INFO)
		
		guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, self.smartClip().geomType().ICON)
	
	#-------------------------------------------------------------------------

	def beamTypeChanged(self, comboBox, index, data):
		
		beamType = guitk.BCComboBoxGetText(comboBox, index)
		self.parent.setTypeBeam(index, beamType)
		
		self._setInfoAttributeValue('beamTypeInfo', self.smartClip().beamType().INFO)
				
		guitk.BCLabelSetIconFileName(self.beamTypeInfo_label, self.smartClip().beamType().ICON)
	

		
# ==============================================================================

class MirrorClipPage(StackWidgetPage):
	
	def createContent(self):
		
		# add check box for mirror option
		self.mirrorCheckBox = guitk.BCCheckBoxCreate(self.contentLayout, 'Mirror created clip')
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.mirrorCheckBox, 0, 0, guitk.constants.BCAlignLeft)
		
		# setup connections
		guitk.BCCheckBoxSetToggledFunction(self.mirrorCheckBox, self.mirrorCheckBoxChanged, None)
		
		# set initial values
		guitk.BCCheckBoxSetChecked(self.mirrorCheckBox, self.parent.DFT_MIRROR_CLIP)

	#-------------------------------------------------------------------------

	def mirrorCheckBoxChanged(self, checkBox, state, data):

		self.parent.setDftMirrorClipState(state)