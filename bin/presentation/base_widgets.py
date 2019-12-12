
import os
import sys

import ansa
from ansa import base, guitk, constants

# ==============================================================================

class PageCheckerException(Exception): pass

# ==============================================================================

class BasePage(object):
	
	TITLE = ''
	DESCRIPTION = ''
	INFO = ''
	PICK_ICON_PATH = 'pick_16.png'
	
	def __init__(self, parentApplication):
		
		self.parentApplication = parentApplication
		self.parentWizard = self.parentApplication.mainWizard
		
		self.inputCheckers = list()
		self.currentChecker = BasePageChecker(self)
		self.infoAttributeNames = list()
		self.isFinished = False
		
		# create content
		self.initiateData()
		self.createBaseContent()
		self.createContent()
		
		guitk.BCSpacerCreate(self.contentLayout)

	#-------------------------------------------------------------------------
   
	def initiateData(self):
		
		''' This is a space for the code where underlying data structure can be initialised. '''
		
		pass
		
	#-------------------------------------------------------------------------
   
	def createBaseContent(self):
		
		self.frame = guitk.BCFrameCreate(self.parentWizard)
	
	#-------------------------------------------------------------------------
   
	def getFrame(self):
		
		return self.frame
		
	#-------------------------------------------------------------------------
    
	def createContent(self):
		
		''' This is a space for the code where page widget definition should/can be done.
		
		Please keep "self.contentLayout" attribute name for main page layout.'''
		
		self.contentLayout = guitk.BCGridLayoutCreate(self.frame, 5, 3)
	
	#-------------------------------------------------------------------------
    
	def activated(self):
		
		''' This is a space for the code that will be activated when page becomes active'''
		
		pass	
#		print('page %s activated' % self.TITLE)
	
	#-------------------------------------------------------------------------
    
	def deactivated(self):
		
		''' This is a space for the code that will be activated when page becomes inactive'''
		
		pass
	
	#-------------------------------------------------------------------------
    
	def deactivatedBack(self):
		
		''' This is a space for the code that will be activated when page becomes inactive'''
		
		pass
	
	#-------------------------------------------------------------------------
    
	def deactivatedNext(self):
		
		''' This is a space for the code that will be activated when page becomes inactive'''
		
		pass
		
	#-------------------------------------------------------------------------

	def stepFinished(self, value=True):
		
		self.isFinished = value
		self.parentApplication.stepFinished()
	
	#-------------------------------------------------------------------------
	
	def showMessage(self, message, critical=False):
		
		self.parentApplication.showMessage(message, critical)
	
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
   
	def smartClip(self):
		
		 return self.parentApplication.getSmartClip()
	
	#-------------------------------------------------------------------------
    
	def updateInfo(self):
		
		pass
	    
    #-------------------------------------------------------------------------

	def _setInfoAttributeValue(self, valueAttrName, value, style=False):

		valueWidget = getattr(self, valueAttrName)
		
		if style:
			guitk.BCLabelSetText(valueWidget, style % value)
		else:
			guitk.BCLabelSetText(valueWidget, '%s' % value)
	
	#-------------------------------------------------------------------------

	def resetInfo(self):
		
		for infoAttributeName in self.infoAttributeNames:
			self._setInfoAttributeValue(infoAttributeName, '-')
			
# ==============================================================================

class BasePageChecker(object):
	
	def __init__(self, parentPage):
		
		self.parentPage = parentPage
		self.parentApplication = self.parentPage.parentApplication
		
		self.report = list()
		self.parameters = dict()
	 
	#-------------------------------------------------------------------------
	
	def check(self):
		
		pass

	#-------------------------------------------------------------------------
	
	def checkFilePath(self, description, widgetAttributeName):
		
		editPathWidget = getattr(self.parentPage, widgetAttributeName)
		
		path = guitk.BCLineEditPathSelectedFilePaths(editPathWidget)
		
		if path is None:		
			self.report.append('%s: Given file does not exist!' % description)
		else:
			self.parameters[widgetAttributeName] = path
	
	#-------------------------------------------------------------------------
	
	def checkLineEditTextLength(self, description, widgetAttributeName):
		
		lineEditWidget = getattr(self.parentPage, widgetAttributeName)
		
		text = guitk.BCLineEditGetText(lineEditWidget)
		if len(text) == 0:
			self.report.append('%s: No text given!' % description)
		else:
			self.parameters[widgetAttributeName] = text
	
	#-------------------------------------------------------------------------
	
	def checkComboBoxText(self, description, widgetAttributeName):
		
		comboBoxWidget = getattr(self.parentPage, widgetAttributeName)
		
		text = guitk.BCComboBoxCurrentText(comboBoxWidget)
		
		self.parameters[widgetAttributeName] = text
	
	#-------------------------------------------------------------------------
	
	def showReport(self):
		
		reportText = ''
		for record in self.report:
			reportText += '\n%s' % record
		
		if len(reportText):			
			raise(PageCheckerException(reportText))
	
	#-------------------------------------------------------------------------
	
	def getParameters(self):
		
		return self.parameters