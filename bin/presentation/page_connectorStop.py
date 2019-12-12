
import os
import sys

import ansa
from ansa import base, guitk, constants

# ==============================================================================

PATH_SELF = os.path.dirname(os.path.realpath(__file__))
PATH_BIN = os.path.dirname(PATH_SELF)

ansa.ImportCode(os.path.join(PATH_SELF, 'base_widgets.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'util.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'base_items.py'))

# ==============================================================================

class ConnectorStopPage(base_widgets.BasePage):
	
	TITLE = 'STOP distances'
	DESCRIPTION = 'Select faces for connector STOP criteria if necessary'
	INFO = ''
	
	#-------------------------------------------------------------------------
   
	def initiateData(self):
		
		''' This is a space for the code where underlying data structure can be initialised. '''
		
		self.isDefined = False
		
		self.selectButtons = dict()
		self.editButtons = dict()
			
	#-------------------------------------------------------------------------

	def activated(self):
		
		''' This is a space for the code that will be activated when page becomes active'''
		
		if not self.isDefined:
			guitk.BCSetApplicationOverrideCursor(guitk.constants.BCCursorWait)
			
			self.smartClip().geomType().setStopDistances(hideMeasurements=False)
			
			guitk.BCRestoreApplicationOverrideCursor()
						
			self.isDefined = True
			self.stepFinished()
	
	#-------------------------------------------------------------------------
    
	def deactivatedNext(self):
		
		''' Once deactivated is should not be possible to modify values '''
		
		for selectButton in self.selectButtons.values():
			guitk.BCSetEnabled(selectButton, False)
		for editButton in self.editButtons.values():
			guitk.BCSetEnabled(editButton, False)		
			
	#-------------------------------------------------------------------------
			
	def createContent(self):
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
		
		# entity info
		self._addContentLine( 'x Lower Limit', 'xLow')
		self._addContentLine( 'x Upper Limit', 'xUp')
		self._addContentLine( 'y Lower Limit', 'yLow')
		self._addContentLine( 'y Upper Limit', 'yUp')
		self._addContentLine( 'z Lower Limit', 'zLow')
		self._addContentLine( 'z Upper Limit', 'zUp')
				
		# create buttons for stop distance redefinition
		stopDistances = ['xLow', 'xUp', 'yLow', 'yUp', 'zLow', 'zUp']
		for i, stopDistanceName in enumerate(stopDistances):
			button = guitk.BCPushButtonCreate(self.contentLayout, "Select",
				#lambda buttonWidget, stopDistanceName: self.smartClip().redefineStopDistance(stopDistanceName),
				lambda buttonWidget, stopDistanceName: self.redefineStopDistance(button, stopDistanceName),
			stopDistanceName)
			
			editButton = guitk.BCPushButtonCreate(self.contentLayout, "Edit",
				#lambda buttonWidget, stopDistanceName: self.smartClip().redefineStopDistance(stopDistanceName),
				lambda buttonWidget, stopDistanceName: self.editStopDistance(button, stopDistanceName),
			stopDistanceName)
			
			self.selectButtons[stopDistanceName] = button
			self.editButtons[stopDistanceName] = editButton
			
			guitk.BCGridLayoutAddWidget(self.contentLayout, button, 1+i, 2, guitk.constants.BCAlignLeft)
			guitk.BCGridLayoutAddWidget(self.contentLayout, editButton, 1+i, 3, guitk.constants.BCAlignLeft)
	
	#-------------------------------------------------------------------------
    
	def redefineStopDistance(self, buttonWidget, stopDistanceName):
		
		try:
			self.smartClip().redefineStopDistance(stopDistanceName)
		except Exception as e:
			self.showMessage(str(e), critical=True)
		
		self.updateInfo()
		
	#-------------------------------------------------------------------------
    
	def editStopDistance(self, buttonWidget, stopDistanceName):
		
		try:
			initialValue = getattr(self.smartClip().geomType(), stopDistanceName)
			
			ret = guitk.UserInput('Enter %s value:' % stopDistanceName, str(initialValue))
			if ret is None:
				return
			value = float(ret)
		except Exception as e:
			self.showMessage(str(e), critical=True)
			return
		
		try:
			self.smartClip().editStopDistance(stopDistanceName, value)
		except Exception as e:
			self.showMessage(str(e), critical=True)
		
		self.updateInfo()
		
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		self._setInfoAttributeValue('xLow', self.smartClip().geomType().xLow, style='<p style="color:blue">%s</p>')
		self._setInfoAttributeValue('xUp', self.smartClip().geomType().xUp, style='<p style="color:red">%s</p>')
		self._setInfoAttributeValue('yLow', self.smartClip().geomType().yLow, style='<p style="color:blue">%s</p>')
		self._setInfoAttributeValue('yUp', self.smartClip().geomType().yUp, style='<p style="color:red">%s</p>')
		self._setInfoAttributeValue('zLow', self.smartClip().geomType().zLow, style='<p style="color:blue">%s</p>')
		self._setInfoAttributeValue('zUp', self.smartClip().geomType().zUp, style='<p style="color:red">%s</p>')
		
	