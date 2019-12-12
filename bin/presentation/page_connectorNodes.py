
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
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'comp_items.py'))

# ==============================================================================

class SelectClipNodesPage(base_widgets.BasePage):
	
	TITLE = 'Select clip NODES'
	DESCRIPTION = 'Select NODES for CONNECTOR on the clip'
	INFO = ''
	
	#-------------------------------------------------------------------------

	def activated(self):
		
		''' This is a space for the code that will be activated when page becomes active'''
		
		if not self.smartClip().beamType().beamsCsDefined:
			try:
				self.smartClip().beamType().checkClipSideNodeRedefinition()
				
				self.smartClip().beamType().createNodesForConnector()
				self.smartClip().beamType().createConnector()
				
				self.smartClip().geomType().hideMeasurements()
				self.smartClip().geomType().hidePoints()
				comp_items.hideAllFaces()
				self.smartClip().beamType().createBeamsConnectorClipSide()
								
				if self.smartClip().beamType().beamsCsDefined:
					self.stepFinished()
				else:
					self.isFinished = False

			except base_items.SmartClipException as e:
				self.stepFinished(False)
				self.showMessage(str(e), critical=True)
						
	#-------------------------------------------------------------------------

	def createContent(self):
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
		
		# entity info
		self._addContentLine( 'Selected NODES', 'noOfNodes')
		self._addContentLine( 'Beam material ID', 'beamMID')
		
		self.pushButtonSelectCon = guitk.BCPushButtonCreate(self.contentLayout, "Select", self.nodesSelected, None)
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.pushButtonSelectCon, 1, 2, guitk.constants.BCAlignLeft)
	
	#-------------------------------------------------------------------------
    
	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip().beamType().beamsCsDefined = False
		
		self.activated()
		self.updateInfo()
			
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		if self.smartClip().beamType().beamNodesCs is not None:
			self._setInfoAttributeValue('noOfNodes', len(self.smartClip().beamType().beamNodesCs))
			self._setInfoAttributeValue('beamMID', self.smartClip().beamType().beamCsMID)
		
		
# ==============================================================================

class SelectClipOppositeNodesPage(SelectClipNodesPage):

	TITLE = 'Select opposite NODES'
	DESCRIPTION = 'Select NODES for CONNECTOR on the clip opposite side'
	INFO = ''
	
	#-------------------------------------------------------------------------

	def activated(self):
		
		''' This is a space for the code that will be activated when page becomes active'''
		
		if not self.smartClip().beamType().beamsCcsDefined:
			try:
				comp_items.hideAllFaces()
				self.smartClip().beamType().checkClipContraSideNodeRedefinition()
				self.smartClip().beamType().createBeamsConnectorClipContraSide()
								
				if self.smartClip().beamType().beamsCcsDefined:
					self.stepFinished()
				else:
					self.isFinished = False

			except base_items.SmartClipException as e:
				self.stepFinished(False)
				self.showMessage(str(e), critical=True)
	
	#-------------------------------------------------------------------------

	def nodesSelected(self, buttonWidget=None, data=None):
		
		# reset selection and propt the new one
		self.smartClip().beamType().beamsCcsDefined = False
		
		self.activated()
		self.updateInfo()
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		if self.smartClip().beamType().beamNodesCcs is not None:
			self._setInfoAttributeValue('noOfNodes', len(self.smartClip().beamType().beamNodesCcs))
			self._setInfoAttributeValue('beamMID', self.smartClip().beamType().beamCcsMID)

# ==============================================================================
