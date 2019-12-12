
import os
import sys

import ansa
from ansa import base, guitk, constants


# ==============================================================================

PATH_SELF = os.path.dirname(os.path.realpath(__file__))
PATH_BIN = os.path.dirname(PATH_SELF)

ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'util.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'comp_items.py'))
ansa.ImportCode(os.path.join(PATH_SELF, 'base_widgets.py'))


# ==============================================================================

class SelectClipTypePage(base_widgets.BasePage):
	
	TITLE = 'Select CLIP Type'
	DESCRIPTION = 'Select a type of the CLIP'
	INFO = ''
		
	def initiateData(self):
		
		''' This is a space for the code where underlying data structure can be initialised. '''
		
		self.isFinished = True

	#-------------------------------------------------------------------------
    
	def deactivatedNext(self):
		
		''' Once deactivated is should not be possible to modify selected CON '''
		
		guitk.BCSetEnabled(self.clipBeamTypeComboBox, False)
		guitk.BCSetEnabled(self.clipGeomTypeComboBox, False)
		
	#-------------------------------------------------------------------------
    		
	def createContent(self):	
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
		
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
		guitk.BCComboBoxSetCurrentItem(self.clipBeamTypeComboBox, self.parentApplication.DFT_TYPE_BEAM)
		guitk.BCComboBoxSetCurrentItem(self.clipGeomTypeComboBox, self.parentApplication.DFT_TYPE_GEOM)

#TODO: this will be replaced with other geometrical types loaded from comp_items		
		self.geomTypeChanged(self.clipGeomTypeComboBox, self.parentApplication.DFT_TYPE_GEOM, None)
		self.beamTypeChanged(self.clipBeamTypeComboBox, self.parentApplication.DFT_TYPE_BEAM, None)
	
	#-------------------------------------------------------------------------

	def geomTypeChanged(self, comboBox, index, data):
				
		geomType = guitk.BCComboBoxGetText(comboBox, index)
		self.parentApplication.setTypeGeom(index, geomType)
		
		self._setInfoAttributeValue('geomTypeInfo', self.smartClip().geomType().INFO)
		
		guitk.BCLabelSetIconFileName(self.geomTypeInfo_label, self.smartClip().geomType().ICON)
	
	#-------------------------------------------------------------------------

	def beamTypeChanged(self, comboBox, index, data):
		
		beamType = guitk.BCComboBoxGetText(comboBox, index)
		self.parentApplication.setTypeBeam(index, beamType)
		
		self._setInfoAttributeValue('beamTypeInfo', self.smartClip().beamType().INFO)
				
		guitk.BCLabelSetIconFileName(self.beamTypeInfo_label, self.smartClip().beamType().ICON)
	