
import os
import sys

import ansa
from ansa import base, guitk, constants

PATH_SELF = os.path.dirname(os.path.realpath(__file__))
PATH_MAIN = os.path.dirname(PATH_SELF)

PATH_BIN = os.path.dirname(PATH_MAIN)
PATH_RES = os.path.join(PATH_BIN, 'res')

ansa.ImportCode(os.path.join(PATH_SELF, 'base_widgets.py'))
ansa.ImportCode(os.path.join(PATH_MAIN, 'domain', 'base_items.py'))

# ==============================================================================

class CoorSysModificationPage(base_widgets.BasePage):
	
	TITLE = 'Select CON'
	DESCRIPTION = 'Select the guiding clip edge - CON'
	INFO = ''
		
	def initiateData(self):
		
		''' This is a space for the code where underlying data structure can be initialised. '''
		
		self.coordSystem = self.smartClip().geomType().coordSystem
				
	#-------------------------------------------------------------------------

	def activated(self):
		
		''' This is a space for the code that will be activated when page becomes active'''
		
		if not self.isFinished:
			self.conSelect()
			base.RedrawAll()

			guitk.BCRestoreApplicationOverrideCursor()
				
	#-------------------------------------------------------------------------
    
	def createContent(self):
		
		''' This is a space for the code where page widget definition should/can be done.
		
		Please keep "self.contentLayout" attribute name for main page layout.'''
		
#		self.contentLayout = guitk.BCBoxLayoutCreate(self.frame, guitk.constants.BCVertical)			
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 3, 4)
		
		self._addContentLine( 'Select CON', 'selectedCONid')
		
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.conSelect, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 1, 2, guitk.constants.BCAlignLeft)
		
		# rotate coor sys
		labelWidget = guitk.BCLabelCreate(self.contentLayout, 'Rotate coor sys')
		guitk.BCGridLayoutAddWidget(self.contentLayout, labelWidget, 2, 0, guitk.constants.BCAlignLeft)

#		self.coorSysIdLabelWidget = guitk.BCLabelCreate(gridLayout, 'Count: -')
#		guitk.BCGridLayoutAddWidget(gridLayout, self.coorSysIdLabelWidget, 0, 1, guitk.constants.BCAlignHCenter)
#
#		self.pushButtonSelectCoorSys = guitk.BCPushButtonCreate(gridLayout, "", self.selectCoorSys, None)
#		guitk.BCButtonSetIconFileName(self.pushButtonSelectCoorSys, self.PICK_ICON_PATH)
#		guitk.BCGridLayoutAddWidget(gridLayout, self.pushButtonSelectCoorSys, 0, 2, guitk.constants.BCAlignLeft)
		
		# rotate X
		self.pushButtonRotXminus = guitk.BCPushButtonCreate(self.contentLayout, "-X", self.rotateXminus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotXminus, 2, 1, guitk.constants.BCAlignLeft)
		
		self.pushButtonRotXplus = guitk.BCPushButtonCreate(self.contentLayout, "+X", self.rotateXplus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotXplus, 2, 2, guitk.constants.BCAlignLeft)
		
		self.rotXspinBox = guitk.BCSpinBoxCreate(self.contentLayout)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.rotXspinBox, 2, 3, guitk.constants.BCAlignLeft)
		guitk.BCSpinBoxSetValue(self.rotXspinBox, 5)
		
		# rotate Y
		self.pushButtonRotYminus = guitk.BCPushButtonCreate(self.contentLayout, "-Y", self.rotateYminus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotYminus, 3, 1, guitk.constants.BCAlignLeft)
		
		self.pushButtonRotYplus = guitk.BCPushButtonCreate(self.contentLayout, "+Y", self.rotateYplus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotYplus, 3, 2, guitk.constants.BCAlignLeft)

		self.rotYspinBox = guitk.BCSpinBoxCreate(self.contentLayout)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.rotYspinBox, 3, 3, guitk.constants.BCAlignLeft)
		guitk.BCSpinBoxSetValue(self.rotYspinBox, 5)
		
		# rotate Z
		self.pushButtonRotZminus = guitk.BCPushButtonCreate(self.contentLayout, "-Z", self.rotateZminus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotZminus, 4, 1, guitk.constants.BCAlignLeft)
		
		self.pushButtonRotZplus = guitk.BCPushButtonCreate(self.contentLayout, "+Z", self.rotateZplus, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonRotZplus, 4, 2, guitk.constants.BCAlignLeft)
		
		self.rotZspinBox = guitk.BCSpinBoxCreate(self.contentLayout)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.rotZspinBox, 4, 3, guitk.constants.BCAlignLeft)
		guitk.BCSpinBoxSetValue(self.rotZspinBox, 5)
		
		self._setRotationButtonsEnabled(False)	

	#-------------------------------------------------------------------------
    
	def conSelect(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
#		self.smartClip().geomType().selectedCon = None
#		self.parentApplication.controller(None, None, 1, None)
		
		self.smartClip().geomType().setBaseFaces()
		self.smartClip().geomType().createCoorSystem()
					
		if self.smartClip().geomType().coordSystem.coorSysEntity is not None:
			self._setRotationButtonsEnabled(True)
			self.stepFinished()

	#-------------------------------------------------------------------------
	
	def _setRotationButtonsEnabled(self, state):
		
		ansa.guitk.BCSetEnabled(self.pushButtonRotXminus, state)
		ansa.guitk.BCSetEnabled(self.pushButtonRotXplus, state)
		ansa.guitk.BCSetEnabled(self.pushButtonRotYminus, state)
		ansa.guitk.BCSetEnabled(self.pushButtonRotYplus, state)
		ansa.guitk.BCSetEnabled(self.pushButtonRotZminus, state)
		ansa.guitk.BCSetEnabled(self.pushButtonRotZplus, state)
				
	#-------------------------------------------------------------------------
    
	def rotateXminus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotXspinBox)
		self.coordSystem.rotateX(-1*value)
		
	#-------------------------------------------------------------------------
    
	def rotateXplus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotXspinBox)
		self.coordSystem.rotateX(+1*value)

	#-------------------------------------------------------------------------
    
	def rotateYminus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotYspinBox)
		self.coordSystem.rotateY(-1*value)
		
	#-------------------------------------------------------------------------
    
	def rotateYplus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotYspinBox)
		self.coordSystem.rotateY(+1*value)
			
	#-------------------------------------------------------------------------
    
	def rotateZminus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotZspinBox)
		self.coordSystem.rotateZ(-1*value)
		
	#-------------------------------------------------------------------------
    
	def rotateZplus(self, buttonWidget=None, data=None):
		
		value = guitk.BCSpinBoxGetInt(self.rotZspinBox)
		self.coordSystem.rotateZ(+1*value)

	#-------------------------------------------------------------------------

	def _setInfoAttributeValue(self, valueAttrName, value, style=False):

		valueWidget = getattr(self, valueAttrName)
		
		if style:
			guitk.BCLabelSetText(valueWidget, style % value)
		else:
			guitk.BCLabelSetText(valueWidget, '%s' % value)
			
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		if self.smartClip().geomType().selectedCon is not None:
			self._setInfoAttributeValue('selectedCONid', 'ID %s' % self.smartClip().geomType().selectedCon._id)		