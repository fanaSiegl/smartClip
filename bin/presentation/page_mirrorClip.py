
import os
import sys

import ansa
from ansa import base, guitk, constants


# ==============================================================================

PATH_SELF = os.path.dirname(os.path.realpath(__file__))
PATH_BIN = os.path.dirname(PATH_SELF)

ansa.ImportCode(os.path.join(PATH_SELF, 'base_widgets.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'util.py'))
ansa.ImportCode(os.path.join(PATH_BIN, 'domain', 'comp_items.py'))
		
# ==============================================================================

class MirrorClipPage(base_widgets.BasePage):
	
	TITLE = 'Mirror clip'
	DESCRIPTION =  'Do you want to mirror created clip?'
	INFO = ''

	def initiateData(self):
		
		''' This is a space for the code where underlying data structure can be initialised. '''
		
		self.stepFinished()
		
	#-------------------------------------------------------------------------

	def createContent(self):
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
		
		# add check box for mirror option
		self.mirrorCheckBox = guitk.BCCheckBoxCreate(self.contentLayout, 'Mirror created clip')
		guitk.BCGridLayoutAddWidget(self.contentLayout, self.mirrorCheckBox, 0, 0, guitk.constants.BCAlignLeft)
		
		# setup connections
		guitk.BCCheckBoxSetToggledFunction(self.mirrorCheckBox, self.mirrorCheckBoxChanged, None)
		
		# set initial values
		guitk.BCCheckBoxSetChecked(self.mirrorCheckBox, self.parentApplication.DFT_MIRROR_CLIP)

	#-------------------------------------------------------------------------

	def mirrorCheckBoxChanged(self, checkBox, state, data):

		self.parentApplication.setDftMirrorClipState(state)