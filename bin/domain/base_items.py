# PYTHON script
import os
import itertools
import math
import numpy as np

import ansa

from ansa import base, constants, guitk

PATH_SELF = os.path.dirname(os.path.realpath(__file__))

# ==============================================================================

class SmartClipException(Exception): pass

# ==============================================================================

class CoorSysException(Exception): pass
			
# ==============================================================================

class ClipCoorSys(object):
	
	def __init__(self, parentClip):
		
		self.parentClip = parentClip
		self.coorSysEntity = None
		self.id = None
					
	#-------------------------------------------------------------------------

	def create(self):
		
		self.originCoords =  np.array(self.parentClip.geomType().centerCoordPointCoords)
		
		self.vectorZ =  np.array(self.parentClip.geomType().largeFaceNormal)
		self.vectorX =  np.array(self.parentClip.geomType().sideProjectionVectorPlus)
		self.vectorY = np.cross(self.vectorX, self.vectorZ)
				
		xAxisPointCoords = self.originCoords + self.vectorX
		zAxisPointCoords = self.originCoords + self.vectorZ
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.originCoords[0], 'A2':  self.originCoords[1], 'A3':  self.originCoords[2],
			'B1':  zAxisPointCoords[0], 'B2':  zAxisPointCoords[1], 'B3':  zAxisPointCoords[2],
			'C1':  xAxisPointCoords[0], 'C2':  xAxisPointCoords[1], 'C3':  xAxisPointCoords[2]}
		self.coorSysEntity = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)
		self.id = self.coorSysEntity._id
						
	#-------------------------------------------------------------------------

	def _checkCurrentPosition(self):
		
		vals = ("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3")
		card = base.GetEntityCardValues(constants.ABAQUS, self.coorSysEntity, vals)
		
		self.vectorZ = np.array([float(card['B1']), float(card['B2']), float(card['B3'])]) - np.array(self.originCoords)
		self.vectorX = np.array([float(card['C1']), float(card['C2']), float(card['C3'])]) - np.array(self.originCoords)
		self.vectorY = np.cross(self.vectorX, self.vectorZ)

	#-------------------------------------------------------------------------

	def rotateX(self, direction):
		
		self._checkCurrentPosition()
		
		base.GeoRotate("MOVE", 1, "SAME PART", "NONE",
			self.originCoords[0], self.originCoords[1], self.originCoords[2],
			self.originCoords[0] + self.vectorX[0], self.originCoords[1] + self.vectorX[1], self.originCoords[2] + self.vectorX[2],
			direction*1.0,
			[self.coorSysEntity], draw_results=True)
		
		self._checkCurrentPosition()
		self.parentClip.geomType().updateVectors()

	#-------------------------------------------------------------------------

	def rotateY(self, direction):
		
		self._checkCurrentPosition()
		
		base.GeoRotate("MOVE", 1, "SAME PART", "NONE",
			self.originCoords[0], self.originCoords[1], self.originCoords[2],
			self.originCoords[0] + self.vectorY[0], self.originCoords[1] + self.vectorY[1], self.originCoords[2] + self.vectorY[2],
			direction*1.0,
			[self.coorSysEntity], draw_results=True)
		
		self._checkCurrentPosition()
		self.parentClip.geomType().updateVectors()
			
	#-------------------------------------------------------------------------

	def rotateZ(self, direction):

		self._checkCurrentPosition()
				
		base.GeoRotate("MOVE", 1, "SAME PART", "NONE",
			self.originCoords[0], self.originCoords[1], self.originCoords[2],
			self.originCoords[0] + self.vectorZ[0], self.originCoords[1] + self.vectorZ[1], self.originCoords[2] + self.vectorZ[2],
			direction*1.0,
			[self.coorSysEntity], draw_results=True)
		
		self._checkCurrentPosition()
		self.parentClip.geomType().updateVectors()
		
# ==============================================================================
