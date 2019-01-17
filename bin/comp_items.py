# PYTHON script
import os
import sys
import numpy as np
import ansa
 
from ansa import base, constants, guitk


# ==============================================================================

PATH_BIN = os.path.dirname(os.path.realpath(__file__))

ansa.ImportCode(os.path.join(PATH_BIN, 'util.py'))

# ==============================================================================

def getAnsaVersion():
	
	currentVersion = constants.app_version
	parts = currentVersion.split('.')
	return int(parts[0])
	
# ==============================================================================

class SmartClipException(Exception): pass

# ==============================================================================

clipBeamTypeRegistry = {}
   
class BeamTypeMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(BeamTypeMetaClass, cls).__new__(cls, clsname, bases, attrs)
        
        clipBeamTypeRegistry[newclass.TYPE_NAME] = newclass
        return newclass

# ==============================================================================

clipGeomTypeRegistry = {}
   
class GeomTypeMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(GeomTypeMetaClass, cls).__new__(cls, clsname, bases, attrs)
        
        clipGeomTypeRegistry[newclass.TYPE_NAME] = newclass
        return newclass
        
# ==============================================================================

COLOURS = {
	'r' :	[255, 0, 0],
	'b' :	[0,  0, 255]}

class Types(object):
	NODE = 3918

# ==============================================================================

class SmartClip(object):
	
	coordsDrawState = None
	
	def __init__(self, geomType='Standart', beamType='AUDI'):
		
		self._geomType = None
		self._beamType = None
		
		self.clipEntities= dict()
				
		self._storeF11drawingSettings()
		self._setupF11drawingSettings()
		
		# set default clip types
		self.setGeomType(geomType)
		self.setBeamType(beamType)
	
	#-------------------------------------------------------------------------
    
	def __getattr__(self, name):
		
		''' Try to search for attribute also in the parent clip'''
		
		if hasattr(self.geomType(), name):
			return getattr(self.geomType(), name)
		elif hasattr(self.beamType(), name):
			return getattr(self.beamType(), name)
		elif hasattr(self, name):
			return getattr(self, name)
		else:
			raise AttributeError( "'%s object has no attribute '%s'" % (self.__class__.__name__, name))
			
	#-------------------------------------------------------------------------
	
	def beamType(self):
		return self._beamType
	
	#-------------------------------------------------------------------------
	
	def geomType(self):
		return self._geomType
	
	#-------------------------------------------------------------------------
	
	def setBeamType(self, beamType):
			
		try:
			clipBeamTypeClass = clipBeamTypeRegistry[beamType]
			self._beamType = clipBeamTypeClass(self)
			return
		except KeyError as e:
			showMessage('No such a beam type "%s" defined.' % beamType)
		except Exception as e:
			showMessage(str(e))
		self._beamType = None
	
	#-------------------------------------------------------------------------
	
	def setGeomType(self, geomType):
			
		try:
			clipGeomTypeClass = clipGeomTypeRegistry[geomType]
			self._geomType = clipGeomTypeClass(self)
			return
		except KeyError as e:
			showMessage('No such a geom type "%s" defined.' % geomType)
		except Exception as e:
			showMessage(str(e))
		self._geomType  = None
			
	#-------------------------------------------------------------------------
    
	def run(self):
		
		try:
			self.setBaseFaces()
			self.setStopDistances()
			self.createCoorSystem()
			
			self.createNodesForConnector()
			self.createConnector()
			self.createBeams()
			
		except SmartClipException as e:
			print(str(e))
		    
	#-------------------------------------------------------------------------
	
	@classmethod
	def _storeF11drawingSettings(cls):
		
		#{'value': 50.0, 'status': 'Relative to screen (%)'}
		currentValue = int(ansa.base.F11PresParamsOptionsGet("Coords")['value'])
		if cls.coordsDrawState is None:
			cls.coordsDrawState = currentValue
	
	#-------------------------------------------------------------------------
	
	def _setupF11drawingSettings(self):
		
		base.SetCurrentMenu('TOPO')
		ansa.base.F11PresParamsOptionsSet("Coords", 'Relative to screen (%)', 50.0)
	
	#-------------------------------------------------------------------------
	
	@classmethod
	def _restoreF11drawingSettings(cls):
		
		ansa.base.F11PresParamsOptionsSet("Coords", 'Relative to screen (%)', cls.coordsDrawState)
		cls.coordsDrawState = None
	
# ==============================================================================

class StandartGeomType(metaclass=GeomTypeMetaClass):
	
	TYPE_NAME = 'Standart'
	INFO ='Standart geometrical clip type.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_geom_standart.png')
	
	CONNECTOR_LENGTH = 1.0
	
	NEAR_RADIUS = 10.0
	CLIP_NODE_DIST = 30
	FACE_ANGLE_LIMIT = 30
	
	def __init__(self, parentClip):
		
		self.parentClip = parentClip
		
		self.selectedCon = None
		self.coordSystem = None
		self.clipEntities= self.parentClip.clipEntities
		
		self.stopDistanceMeasurements = dict()
		self.stopDistanceFaceCouples = dict()
		
		self.xLow = -1000
		self.xUp = 1000
		self.yLow = -1000
		self.yUp = 1000
		self.zLow = -1000
		self.zUp = 1000
		
		self.stopDistPoints = list()
			    
    #-------------------------------------------------------------------------
    
	def _getPointProjectionCoords(self, faces, pointCoords, vector, tolerance=50, searchedFaceName='face', minDist=True, recSearch=False):
		    	
    	# check for point projection on opposite face
		foundProjection = list()
		foundCoordinates = list()
		distances = list()
		for face in faces:
			projectedPointCoords =ansa.base.ProjectPointDirectional(
				face, pointCoords[0], pointCoords[1], pointCoords[2],
				vector[0], vector[1], vector[2], tolerance, project_on="faces")
			
			
			if projectedPointCoords is not None:
				distances.append(np.linalg.norm(np.array(pointCoords) - np.array(projectedPointCoords)))
				foundProjection.append(face)
				foundCoordinates.append(projectedPointCoords)
				#return face, projectedPointCoords
		if len(foundProjection) == 1:
			return foundProjection[0], foundCoordinates[0]
		elif len(foundProjection) > 1:
			if minDist:
				minDistanceIndex = np.argsort(distances)[0]
			else:
				minDistanceIndex = np.argsort(distances)[-1]
			return foundProjection[minDistanceIndex], foundCoordinates[minDistanceIndex]
		
		else:
		#if projectedPointCoords is None:
			#showMessage("Projection to given faces not found within given tolerance of %s mm! Please select the %s manually." % (tolerance, searchedFaceName))
			#print("Projection to given faces not found within given tolerance of %s mm! Please select the %s manually." % (tolerance, searchedFaceName))
			#face = set(base.PickEntities(constants.ABAQUS, "FACE"))
			#projectedPointCoords =ansa.base.ProjectPointDirectional(
			#	face, pointCoords[0], pointCoords[1], pointCoords[2],
			#	vector[0], vector[1], vector[2], tolerance, project_on="faces")
			
			# recursive search for projection
			if recSearch:
				recSearchRange = recSearch[0]
				recSearchVector = recSearch[1]
				for inc in recSearchRange:
					pointCoords = pointCoords + 0.5*float(inc)*np.array(recSearchVector)
					face, projectedPointCoords = self._getPointProjectionCoords(faces, pointCoords, vector, tolerance=100)
					
					if projectedPointCoords is not None:
						break
			else:
				face = None
				projectedPointCoords = None
		
		return face, projectedPointCoords

	#-------------------------------------------------------------------------
        
	def _getPointsProjectionCoords(self, faces, pointsCoords, vector, tolerance=50):
		
		''' Returns nearest clipPointCoords, neighbourPointCoords'''
		
		# check for point projection on opposite face
		foundProjection = list()
		facesProjectionFound = list()
		distances = list()
		for face in faces:
			for pointCoords in pointsCoords:
				projectedPointCoords =ansa.base.ProjectPointDirectional(
					face, pointCoords[0], pointCoords[1], pointCoords[2],
					vector[0], vector[1], vector[2], tolerance, project_on="faces")
				
				# projection found for given point on face
				if projectedPointCoords is not None:
					distances.append(np.linalg.norm(np.array(pointCoords) - np.array(projectedPointCoords)))
					foundProjection.append([pointCoords, projectedPointCoords])
					facesProjectionFound.append(face)
		
		if len(distances) == 0:
			print('No projection found')
			return None, None
		
		minDist = np.argmin(np.array(distances))
		minDistPoints = foundProjection[minDist]
		minDistNeighbourFace = facesProjectionFound[minDist]
		
		return minDistPoints, minDistNeighbourFace

	#-------------------------------------------------------------------------
	
	def _getStopDistance(self, clipFacePoint, mateFacePoint, measurementDescription, colour='m'):

		# searching for distances
		mFace2face = ansa.base.CreateMeasurement([clipFacePoint, mateFacePoint], 'DISTANCE')
		faceDist = getEntityProperty(mFace2face, 'RESULT')
				
#		nodeFaceClipDist = np.linalg.norm(np.array(self.centerCoordPointCoords) - np.array(getHotPointCoords(clipFacePoint)))
#		nodeFaceMateDist = np.linalg.norm(np.array(self.centerCoordPointCoords) - np.array(getHotPointCoords(mateFacePoint)))
		
		currentMateProjectionVector = np.array(getHotPointCoords(clipFacePoint)) - np.array(getHotPointCoords(mateFacePoint))
		angle = ansa.calc.CalcAngleOfVectors(currentMateProjectionVector, self.oppositeProjectionVector)
		angle = angle*180/3.14
		
		# check penetrations in z direction
		# check distance location for zUpper limit
		penetration = ''
		if measurementDescription == 'zUp':
			if angle < 90:
				print('Penetration detected! Distance set to: 0.01')
				penetration = '_penetration_detected'
				faceDist = 0.01
		elif measurementDescription == 'zLow':	
			if angle > 90:
				print('Penetration detected! Distance set to: 0.01')
				penetration = '_penetration_detected'
				faceDist = 0.01
		
		if abs(faceDist) < 0.01:
			faceDist = 0.01
		else:
			faceDist = round(faceDist, 2)
				
		# set measurement color
		if colour in COLOURS:
			colourRGB = COLOURS[colour]
			base.SetEntityCardValues(constants.ABAQUS, mFace2face,
				{'Name' : 'Distance_%s' % measurementDescription + penetration,
				'COLOR_R' : colourRGB[0],  'COLOR_G' : colourRGB[1], 'COLOR_B' : colourRGB[2]})		
		
		self.stopDistanceMeasurements[measurementDescription] = mFace2face
		self.stopDistPoints.extend([clipFacePoint, mateFacePoint])
		
		return faceDist

	#-------------------------------------------------------------------------
    
	def _getAngleSortedFaces(self, faces, sortingVector, excludeFaces=list(), angleLimit=45):
		
		def sortFacesFcn(face):
			angle = ansa.calc.CalcAngleOfVectors(base.GetFaceOrientation(face), sortingVector)
			return angle*180/3.14
				
		sortedFaces = list(sortEntities(faces, sortFacesFcn, angleLimit))

		if len(sortedFaces) == 0:
			angleLimit+=10
			print('Increasing angle value for face searching: %s' % angleLimit)
			sortedFaces = self._getAngleSortedFaces(faces, sortingVector, excludeFaces, angleLimit)
		
		for excludeFace in excludeFaces:
			sortedFaces.remove(excludeFace)
		
		return sortedFaces
		
	#-------------------------------------------------------------------------

	def _getFaceNodeCoords(self, faces):
		
		''' Returns coordinetes of nodes created by meshing of given faces.
		Coords are checked for absolute distance from central clip node. '''
		
		nodes = base.CollectEntities(constants.ABAQUS, faces, "NODE")
		
		if len(nodes) == 0:
			ansa.guitk.UserWarning('Clip faces must be meshed prior to use clip tool.\n(E.G. Perimeter length = 0.5)')
			raise(SmartClipException('Faces must be meshed!'))
		
		facesNodeCoords = list()
		for entity in nodes:
			#if entity._type == Types.NODE:
			nodeCoords = [getEntityProperty(entity, 'X'), getEntityProperty(entity, 'Y'), getEntityProperty(entity, 'Z')]
			nodeCenterDistance = np.linalg.norm(np.array(self.centerCoordPointCoords) - np.array(nodeCoords))
			# check node distance			
			if nodeCenterDistance < self.CLIP_NODE_DIST:			
				facesNodeCoords.append(nodeCoords)
		
		return facesNodeCoords
	
	#-------------------------------------------------------------------------

	def _getStopDistancePoints(self, clipVector, neighbourVector, angleLimit=None, preSelectedFaces=None):
		
		if angleLimit is None:
			angleLimit = self.FACE_ANGLE_LIMIT
		
		# if no faces given, search for them by given vectors
		if preSelectedFaces is None:
			sideNeighbourFaces = self._getAngleSortedFaces(self.neighbourFaces, neighbourVector, angleLimit=angleLimit)
			sideClipFaces = self._getAngleSortedFaces(self.clipFaces, clipVector, angleLimit=angleLimit)
		else:
			sideClipFaces = preSelectedFaces[0]
			sideNeighbourFaces = preSelectedFaces[1]
		
		sideClipFacePointCoords = self._getFaceNodeCoords(sideClipFaces)
		minDistPoints, minDistNeighbourFace = self._getPointsProjectionCoords(sideNeighbourFaces, sideClipFacePointCoords, clipVector)
		
		minDistFaces = sideClipFaces
		minDistFaces.append(minDistNeighbourFace)
		
		if minDistPoints is None:
			angleLimit+=10
			print('No projection. Increasing angle value: %s' % angleLimit)
			#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = sideClipFaces)
			#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = sideNeighbourFaces)
			
			minDistPoints, minDistFaces = self._getStopDistancePoints(clipVector, neighbourVector, angleLimit=angleLimit)
		
		return minDistPoints, minDistFaces
	
	#-------------------------------------------------------------------------

	def _searchClipSurroundingArea(self):
		
		# selecting base CON defining the clip position
		print('Select guiding clip edge - CON.')
		selectedCons = base.PickEntities(constants.ABAQUS, "CONS")
		
		if selectedCons is None:
			self.selectedCon = None
			raise(SmartClipException('No guiding CON selected!'))
		
		self.selectedCon = selectedCons[0]
		neighbourFaces = ansa.base.GetFacesOfCons(cons = selectedCons)
		
		sortedFaces = sortEntities(neighbourFaces, base.GetFaceArea)
		self.smallFace = sortedFaces[0]
		self.largeFace = sortedFaces[1]
		
		# set clip property
		self.clipProperty = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(self.largeFace, 'PID'))
		
		# analyse clip surrounding
		
		# searching for distances
		# show only relevant entities
		base.SetEntityVisibilityValues(constants.ABAQUS, {"SHELL":"on"})
		base.SetViewButton({"FE-Mode":"on"})
		base.Or(self.smallFace, constants.ABAQUS)
		base.Near(radius=self.NEAR_RADIUS, dense_search=False, custom_entities=self.largeFace)
		
		# find faces on clip mate geometry
		visibleProps = base.CollectEntities(constants.ABAQUS, None, "SHELL_SECTION", filter_visible=True)
		
		visibleProps.remove(self.clipProperty)
		neighbourFaces = base.CollectEntities(constants.ABAQUS, visibleProps, "FACE", filter_visible=True)
		self.neighbourFaces = sortEntities(neighbourFaces, base.GetFaceArea)
		
		# clip faces
		clipFaces = base.CollectEntities(constants.ABAQUS, [self.clipProperty], "FACE", filter_visible=True)
		self.clipFaces = list(sortEntities(list(clipFaces), base.GetFaceArea))
		
		self.neighbourFaceProperties = base.CollectEntities(constants.NASTRAN, neighbourFaces, 'PSHELL')
		for neighbourFaceProperty in self.neighbourFaceProperties:
			if neighbourFaceProperty in visibleProps:
				visibleProps.remove(neighbourFaceProperty)
		self.clipAreaShells = base.CollectEntities(constants.ABAQUS, visibleProps, "SHELL")#, filter_visible=True)
		#base.SetViewButton({"FE-Mode":"off"})
		
		# guiding face normals
		self.smallFaceNormal = base.GetFaceOrientation(self.smallFace)
		self.largeFaceNormal = base.GetFaceOrientation(self.largeFace)
						
	#-------------------------------------------------------------------------

	def setBaseFaces(self):
						
		self._searchClipSurroundingArea()
		
		self.sideProjectionVectorPlus = np.cross(self.largeFaceNormal, self.smallFaceNormal)
		self.sideProjectionVectorMinus = np.cross(self.smallFaceNormal, self.largeFaceNormal)
		
		# this is correct orthogonal vector that a small face should have in case of 90 degrees...
		self.smallFaceOrthoVector = np.cross(self.largeFaceNormal, self.sideProjectionVectorMinus)
		self.oppositeProjectionVector = -1*np.array(self.largeFaceNormal)
		
		self.middlePointCoords = getConMiddle(self.selectedCon)
		
		# find opposite face
		oppositeFaces = self._getAngleSortedFaces(self.clipFaces, self.oppositeProjectionVector)
		oppositeFace, oppositeFacePointCoords = self._getPointProjectionCoords(
			oppositeFaces, self.middlePointCoords, self.oppositeProjectionVector, searchedFaceName='z upper face - clip side')
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.median([oppositeFacePointCoords, self.middlePointCoords], axis=0)
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
						
	#-------------------------------------------------------------------------

	def setStopDistances(self, hideMeasurements=True):
		
		stopDistanceMethods = [self.findZlowDist, self.findZupDist, self.findXupDist, self.findXlowDist,
			self.findYupDist, self.findYlowDist]
		for stopDistanceMethod in stopDistanceMethods:
			try:
				stopDistanceMethod()
			except Exception as e:
				print(str(e))
				continue
		
		if hideMeasurements:
			self.hideMeasurements()
	
	#-------------------------------------------------------------------------

	def findZupDist(self, preSelectedFaces=None):
		
		# find z minus side = z upper stop distance
		minDistZminusPoints, minDistFaces = self._getStopDistancePoints(
			self.oppositeProjectionVector, self.largeFaceNormal, preSelectedFaces=preSelectedFaces)
		
		self.oppositeFacePoint = createPoint(minDistZminusPoints[0], 'clipZupper')
		self.oppositeNeighbourFacePoint = createPoint(minDistZminusPoints[1], 'neighbourZupper')	
		
		self.zUp = self.CONNECTOR_LENGTH + self._getStopDistance(self.oppositeFacePoint, self.oppositeNeighbourFacePoint, 'zUp' , colour='r')
		
		self.stopDistanceFaceCouples['zUp'] = minDistFaces
		
	#-------------------------------------------------------------------------

	def findZlowDist(self, preSelectedFaces=None):
		
		# find z plus side = z lower stop distance
		minDistZplusPoints, minDistFaces = self._getStopDistancePoints(
			self.largeFaceNormal, self.oppositeProjectionVector, preSelectedFaces=preSelectedFaces)
			
		self.frontFacePoint = createPoint(minDistZplusPoints[0], 'clipZlower')
		self.frontNeighbourFacePoint = createPoint(minDistZplusPoints[1], 'neighbourZlower')
		
		self.zLow = self.CONNECTOR_LENGTH - 1*self._getStopDistance(self.frontFacePoint, self.frontNeighbourFacePoint, 'zLow', colour='b')
		
		self.stopDistanceFaceCouples['zLow'] = minDistFaces
		
	#-------------------------------------------------------------------------

	def findXupDist(self, preSelectedFaces=None):
		
		# find x minus side = x upper stop distance
		minDistXminusPoints, minDistFaces = self._getStopDistancePoints(
			self.sideProjectionVectorMinus, self.sideProjectionVectorPlus, preSelectedFaces=preSelectedFaces)

		self.sideFacePlusPoint = createPoint(minDistXminusPoints[0], 'clipXupper')
		self.sidePlusNeighbourFacePoint = createPoint(minDistXminusPoints[1], 'neighbourXupper')		
		
		self.xUp = self._getStopDistance(self.sideFacePlusPoint, self.sidePlusNeighbourFacePoint, 'xUp', colour='r')
		
		self.stopDistanceFaceCouples['xUp'] = minDistFaces
		
	#-------------------------------------------------------------------------

	def findXlowDist(self, preSelectedFaces=None):
		
		# find x plus side = x lower stop distance
		minDistXplusPoints, minDistFaces = self._getStopDistancePoints(
			self.sideProjectionVectorPlus, self.sideProjectionVectorMinus, preSelectedFaces=preSelectedFaces)
		
		self.sideFaceMinusPoint = createPoint(minDistXplusPoints[0], 'clipXlower')
		self.sideMinusNeighbourFacePoint = createPoint(minDistXplusPoints[1], 'neighbourXlower')
		self.xLow = -1*self._getStopDistance(self.sideFaceMinusPoint, self.sideMinusNeighbourFacePoint, 'xLow', colour='b')
		
		self.stopDistanceFaceCouples['xLow'] = minDistFaces

	#-------------------------------------------------------------------------

	def findYupDist(self, preSelectedFaces=None):		
	
		# find y plus side = y upper stop distance
		minDistYPoints, minDistFaces = self._getStopDistancePoints(
			self.smallFaceNormal, -1*np.array(self.smallFaceNormal), preSelectedFaces=preSelectedFaces)

		self.topPoint = createPoint(minDistYPoints[0], 'clipYupper')
		self.topNeighbourFacePoint = createPoint(minDistYPoints[1], 'neighbourYupper')
		self.yUp = self._getStopDistance(self.topPoint, self.topNeighbourFacePoint, 'yUp', colour='r')
		
		self.stopDistanceFaceCouples['yUp'] = minDistFaces
		
	#-------------------------------------------------------------------------

#	def findYlowDist(self, preSelectedFaces=None):
#		self.yLow = -1000
	def findYlowDist(self, preSelectedFaces=None):
		
		# find y minu side = y lower stop distance
		minDistYPoints, minDistFaces = self._getStopDistancePoints(
			-1*np.array(self.smallFaceNormal), self.smallFaceNormal, preSelectedFaces=preSelectedFaces)

		topPoint = createPoint(minDistYPoints[0], 'clipYlower')
		topNeighbourFacePoint = createPoint(minDistYPoints[1], 'neighbourYlower')
		self.yLow = -1*self._getStopDistance(topPoint, topNeighbourFacePoint, 'ylow', colour='b')
		
		self.stopDistanceFaceCouples['yLow'] = minDistFaces
	
	#-------------------------------------------------------------------------

	def editStopDistance(self, stopDistName, value):
		
		setattr(self, stopDistName, value)
		
		#print('Setting %s = %s' % (stopDistName, value))
		
	#-------------------------------------------------------------------------

	def redefineStopDistance(self, stopDistName, alterName=None):
		
		self.hideMeasurements()
		
		if stopDistName in self.stopDistanceFaceCouples:
			initialFaces = self.stopDistanceFaceCouples[stopDistName]
		else:
			initialFaces = list()
		
		if stopDistName in self.stopDistanceMeasurements:
			base.And(self.stopDistanceMeasurements[stopDistName], constants.ABAQUS)
		
		selectedFaces = base.PickEntities(constants.ABAQUS, 'FACE', initial_entities=initialFaces)
		
		if selectedFaces is None:
			self.showMeasurements()
			raise(SmartClipException('No faces defining STOP distance selected!'))
				
		if len(selectedFaces) < 2:
			self.showMeasurements()
			raise(SmartClipException('Please select just two faces.'))
			
		# find selected clip face and its mate
		selectedClipFaces = list()
		selectedNeighbourFaces = list()
		for face in selectedFaces:
			faceProperty = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(face, 'PID'))
			if faceProperty == self.clipProperty:
				selectedClipFaces.append(face)
			else:
				selectedNeighbourFaces.append(face)
				
		if len(selectedClipFaces) == 0:
			self.showMeasurements()
			raise(SmartClipException('No clip faces selected!'))
		if len(selectedNeighbourFaces) == 0:
			self.showMeasurements()
			raise(SmartClipException('No clip neighbour faces selected!'))
		
		if alterName is not None:
			stopDistName = alterName
		
		if stopDistName in self.stopDistanceMeasurements:
			base.DeleteEntity(self.stopDistanceMeasurements[stopDistName])
		
		stopDistName = stopDistName[0].upper()+stopDistName[1:].lower()
		
		method = getattr(self, 'find%sDist' % stopDistName)
		method(preSelectedFaces=[selectedClipFaces, selectedNeighbourFaces])
		
		self.showMeasurements()
		
	#-------------------------------------------------------------------------

	def hideMeasurements(self):
		
		stopDistanceMeasurements = [v for v in self.stopDistanceMeasurements.values()]

		status = base.Not(stopDistanceMeasurements, constants.ABAQUS)
	
	#-------------------------------------------------------------------------

	def showMeasurements(self):
		
		stopDistanceMeasurements = [v for v in self.stopDistanceMeasurements.values()]

		status = base.And(stopDistanceMeasurements, constants.ABAQUS)
	
	#-------------------------------------------------------------------------

	def hidePoints(self):
		
		entities = list()
		for point in self.stopDistPoints:
			entities.append(point)
		
		status = base.Not(entities, constants.ABAQUS)
	
	#-------------------------------------------------------------------------

	def createCoorSystem(self):
		
		xAxisPointCoords = np.array(self.centerCoordPointCoords)+np.array(self.sideProjectionVectorPlus)
		zAxisPointCoords = np.array(self.centerCoordPointCoords)+np.array(self.largeFaceNormal)
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  zAxisPointCoords[0], 'B2':  zAxisPointCoords[1], 'B3':  zAxisPointCoords[2],
			'C1':  xAxisPointCoords[0], 'C2':  xAxisPointCoords[1], 'C3':  xAxisPointCoords[2]}
		self.coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

	#-------------------------------------------------------------------------
	
	def createSymmetricalCoorSys(self):
		
		centerPointCoords =  np.array([1,-1,1])*(np.array(self.parentClip.centerCoordPointCoords))
		xAxisPointCoords = np.array(centerPointCoords)-np.array([1,-1,1])*np.array(self.sideProjectionVectorPlus)
		zAxisPointCoords = np.array(centerPointCoords)+np.array([1,-1,1])*np.array(self.largeFaceNormal)
		
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  centerPointCoords[0], 'A2':  centerPointCoords[1], 'A3':  centerPointCoords[2],
			'B1':  zAxisPointCoords[0], 'B2':  zAxisPointCoords[1], 'B3':  zAxisPointCoords[2],
			'C1':  xAxisPointCoords[0], 'C2':  xAxisPointCoords[1], 'C3':  xAxisPointCoords[2]}
				
		self.symmCoordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

# ==============================================================================

class ReversedGeomType(StandartGeomType):
	
	TYPE_NAME = 'Reversed'
	INFO ='Reversed geometrical clip type.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_geom_reversed.png')
	
	#-------------------------------------------------------------------------
    
	def setBaseFaces(self):
												
		self._searchClipSurroundingArea()
		# standart type compatible orientation
		self.largeFaceNormal = -1*np.array(self.largeFaceNormal)
		
		self.sideProjectionVectorPlus = np.cross(self.largeFaceNormal, self.smallFaceNormal)
		self.sideProjectionVectorMinus = np.cross(self.smallFaceNormal, self.largeFaceNormal)
		
		# this is correct orthogonal vector that a small face should have in case of 90 degrees...
		self.smallFaceOrthoVector = np.cross(self.largeFaceNormal, self.sideProjectionVectorMinus)
		self.oppositeProjectionVector = -1*np.array(self.largeFaceNormal)
		
		self.middlePointCoords = getConMiddle(self.selectedCon)
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.array(self.middlePointCoords) + 1*self.largeFaceNormal
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
				

# ==============================================================================

class LockGeomType(ReversedGeomType):
	
	TYPE_NAME = 'Lock'
	INFO ='Lock-like geometrical clip type.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_geom_lock.png')

# ==============================================================================

class FlatGeomType(StandartGeomType):
	
	TYPE_NAME = 'Flat'
	INFO ='Flat geometrical clip type without clip. Requires: 1. selection of the guiding CON and 2. top face. Guiding CON must be created by cutting the front face if not present.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_geom_flat.png')
	
	NEAR_RADIUS = 15.0
						
	#-------------------------------------------------------------------------

	def setBaseFaces(self):
						
		self._searchClipSurroundingArea()
		
		# selecting base CON defining the clip position
		print('Select guiding clip top face.')
		selectedFaces = base.PickEntities(constants.ABAQUS, "FACE")
		
		if selectedFaces is None:
			raise(SmartClipException('No guiding FACE selected!'))
		if len(selectedFaces) > 1:
			raise(SmartClipException('Please select just one face.'))
		
		self.smallFace = selectedFaces[0]
		self.smallFaceNormal = -1*np.array(base.GetFaceOrientation(self.smallFace))
		
		self.sideProjectionVectorPlus = np.cross(self.largeFaceNormal, self.smallFaceNormal)
		self.sideProjectionVectorMinus = np.cross(self.smallFaceNormal, self.largeFaceNormal)
		
		# fix local coor sys orintation according to selected CON
		conPointCoords = getConsHotPointCoords(self.selectedCon)
		baseSideVector = np.array(conPointCoords[0]) - np.array(conPointCoords[1])
		angle = (ansa.calc.CalcAngleOfVectors(self.sideProjectionVectorPlus, baseSideVector))*180/3.14
		if angle < 90:
			self.sideProjectionVectorPlus = baseSideVector
			self.sideProjectionVectorMinus = -1*baseSideVector
		else:
			self.sideProjectionVectorPlus = -1*baseSideVector
			self.sideProjectionVectorMinus = baseSideVector
		
		# this is correct orthogonal vector that a small face should have in case of 90 degrees...
		smallFaceOrthoVector = np.cross(self.largeFaceNormal, self.sideProjectionVectorMinus)
		self.smallFaceOrthoVector = smallFaceOrthoVector / np.linalg.norm(smallFaceOrthoVector)
		self.oppositeProjectionVector = -1*np.array(self.largeFaceNormal)
		
		self.middlePointCoords = getConMiddle(self.selectedCon)		
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.array(self.middlePointCoords) + 1*self.oppositeProjectionVector
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
		
	#-------------------------------------------------------------------------

	def findYupDist(self, preSelectedFaces=None):		
		
		self.yUp = 1000
		
		
# ==============================================================================

class AudiBeamType(metaclass=BeamTypeMetaClass):
	
	TYPE_NAME = 'AUDI'
	INFO ='AUDI CONNECTOR type clip consists of 1 connector element and beams joining connector with a clip and its contra side.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_beam_audi.png')
	
	CONNECTOR_ELASTICITY = [50, 50, 50]
	CONNECTOR_LENGTH = 1.0
	
	def __init__(self, parentClip):
		
		self.parentClip = parentClip
		
		self.beamNodesCs = None
		self.beamNodesCcs = None
		self.selectedElementsBeamCs = list()
		self.selectedElementsBeamCcs = list()
		self.beamsCsDefined = False
		self.beamsCcsDefined = False
		
		self.clipEntities = self.parentClip.clipEntities
			
	#-------------------------------------------------------------------------
    
	def __getattr__(self, name):
		
		''' Try to search for attribute also in the parent clip'''
		
		if hasattr(self.parentClip.geomType(), name):
			return getattr(self.parentClip.geomType(), name)
		elif hasattr(self, name):
			return getattr(self, name)
		else:
			raise AttributeError( "'%s object has no attribute '%s'" % (self.__class__.__name__, name))
	
	#-------------------------------------------------------------------------

	def createNodesForConnector(self):
				
		# create nodes for entities		
		connectorNodeCoords = self.centerCoordPointCoords+0.5*self.CONNECTOR_LENGTH*np.array(self.largeFaceNormal)
	
		self.connectingBeamsCenterNode1 = createNode(
			self.centerCoordPointCoords-0.5*self.CONNECTOR_LENGTH*np.array(self.largeFaceNormal))
		self.connectingBeamsCenterNode2 = createNode(connectorNodeCoords)
	
	#-------------------------------------------------------------------------

	def checkClipSideNodeRedefinition(self):

		if 'connector' in self.clipEntities:
			base.DeleteEntity(self.clipEntities['connector'], force=True)
			base.DeleteEntity(self.clipEntities['beams_cs'], force=True)
			
			if 'connector_beams' in self.clipEntities:
				base.DeleteEntity(self.clipEntities['connector_beams'], force=True)

	#-------------------------------------------------------------------------

	def checkClipContraSideNodeRedefinition(self):

		if 'beams_ccs' in self.clipEntities:
			base.DeleteEntity(self.clipEntities['beams_ccs'], force=True)

	#-------------------------------------------------------------------------
	
	def _checkNodeUniqueSelection(self):
		
		''' Check that there are no common nodes for clip side and clip contra side.
		That would mean that clip movement is avoid at all. '''
		
		# check non unique nodes
#		ccsNodeIds = [node._id for node in self.beamNodesCcs]
#		csNodeIds = [node._id for node in self.beamNodesCs]
		ccsPids = [prop._id for prop in base.CollectEntities(
			constants.ABAQUS, self.selectedElementsBeamCcs, "__PROPERTIES__")]
		csPids = [prop._id for prop in base.CollectEntities(
			constants.ABAQUS, self.selectedElementsBeamCs, "__PROPERTIES__")]
		
		if len(set(ccsPids).intersection(set(csPids))) > 0:
#			message = 'Same nodes were selected for clip side and clip contra side!'
			message = 'Selected nodes must not belong to the same property!\nPlease select different nodes.'
			raise(SmartClipException(message))

	#-------------------------------------------------------------------------

	def createConnector(self):
		
		# create connector elasticity
		vals = {'Name': 'CONNECTOR ELASTICITY',
			 'COMP': 'YES',
			 'COMP(1)': 'YES', 'El.Stiff.(1)': self.CONNECTOR_ELASTICITY[0],
			 'COMP(2)': 'YES', 'El.Stiff.(2)': self.CONNECTOR_ELASTICITY[1],
			 'COMP(3)': 'YES', 'El.Stiff.(3)': self.CONNECTOR_ELASTICITY[2],
			}
		self.connectorElasticity = base.CreateEntity(constants.ABAQUS, "CONNECTOR_ELASTICITY", vals)
	
		# create connector stop
		vals = {'Name': 'CONNECTOR STOP',
			 'COMP (1)': 'YES', 'Low.Lim.(1)': self.xLow, 'Up.Lim.(1)': self.xUp, 
			 'COMP (2)': 'YES', 'Low.Lim.(2)': self.yLow, 'Up.Lim.(2)': self.yUp, 
			 'COMP (3)': 'YES', 'Low.Lim.(3)': self.zLow, 'Up.Lim.(3)': self.zUp, 
			}
		self.connectorStop = base.CreateEntity(constants.ABAQUS, "CONNECTOR_STOP", vals)
		
		# create connector behavior
		vals = {'Name': 'CONNECTOR BEHAVIOR',
			'*ELASTICITY': 'YES', 'EL>data': self.connectorElasticity._id,
			'*STOP':'YES', 'STP>data': self.connectorStop._id,
			}
		self.connectorBehavior = base.CreateEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", vals)
		
		# create a connector section
		vals = {'Name': 'CONNECTOR_SECTION',
			 'MID': self.connectorBehavior._id,
			'COMPONENT_1': 'CARDAN', 'COMPONENT_2':  'CARTESIAN', 'ORIENT_1': self.coordSystem._id,
			}
		self.connectorSection = base.CreateEntity(constants.ABAQUS, "CONNECTOR_SECTION", vals)
		
		# create a connector
		vals = {'Name': 'CONNECTOR',
			'PID': self.connectorSection._id,
			'G1':  self.connectingBeamsCenterNode1._id, 'G2': self.connectingBeamsCenterNode2._id}
		self.connector = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)
		
		self.clipEntities['connector'] = [
			self.connectorElasticity,
			self.connectorStop,
			self.connectorBehavior,
			self.connectorSection,
			self.connector]
	
	#-------------------------------------------------------------------------
    
	def createBeams(self):
		
		hideAllFaces()
		
		self.createBeamsConnectorClipSide()
		self.createBeamsConnectorClipContraSide()
		
		self.parentClip._restoreF11drawingSettings()
	
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipContraSide(self):
		
		# find nodes for initial selection
		#searchEntities = base.CollectEntities(constants.ABAQUS, None, "SHELL")
		
		# if no elements were selected before try to find the nearest ones
		if len(self.selectedElementsBeamCcs) == 0:
			# some points may not be defined because of non standart clip shape
			try:
				nearestElements = findNearestElements(
					np.array(getHotPointCoords(self.centerCoordNode)) + 3*np.array(self.largeFaceNormal), self.clipAreaShells)
			except Exception as e:
				print(str(e))
				nearestElements = list()
		else:
#			# delete already created beams
#			base.DeleteEntity(self.beamsCcs, force=True)
			nearestElements = self.selectedElementsBeamCcs
		
		print('Select nodes for beam definition: CONNECTOR - CLIP contra side.')
		selectedElements = base.PickEntities(constants.ABAQUS, "SHELL", initial_entities=nearestElements)
		
		if selectedElements is None:
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		self.beamNodesCcs = base.CollectEntities(constants.ABAQUS, selectedElements, "NODE")
						
		if len(self.beamNodesCcs) == 0:
			self.beamNodesCcs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		# save selected elements for further re-selection
		self.selectedElementsBeamCcs = selectedElements
		self.beamsCcsDefined = True

		# check that there are no common nodes for clip side and clip contra side
		self._checkNodeUniqueSelection()
		
		elements = base.NodesToElements(self.beamNodesCcs)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		self.beamPropCcs = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(element, 'PID'))
		if self.beamPropCcs is None:
			self.beamPropCcs = base.GetEntity(constants.ABAQUS, 'LAMINATE', getEntityProperty(element, 'PID'))
			# create dummy material
			vals = {
				'Name': 'ABS_BEAMS_NO_CREEP',
				'DEFINED' : 'YES',
				'Elasticity' : 'ELASTIC',
				'Plasticity (Rate Indep.)' : 'PLASTIC', 
				'Plasticity (Rate Dep.)' : 'CREEP',
				 '*DENSITY' : 'YES',
				 'DENS' : 7.85E-12, 
				 '*ELASTIC' : 'YES',
				 # 'TYPE' : 'ISOTROPIC',
				 'YOUNG' : 210000, 'POISSON' : 0.3
				 }
								
			beamMaterial = base.CreateEntity(constants.ABAQUS, "MATERIAL", vals)
			self.beamCcsMID = beamMaterial._id
		else:
			self.beamCcsMID = getEntityProperty(self.beamPropCcs, 'MID')
		
		# create beam section
		vals = {'Name': 'BEAM_SECTION',
			'TYPE_':'SECTION', 'MID': self.beamCcsMID,
			'SECTION': 'CIRC', 'TYPE':'B31', 'optional2':'H',
			'RADIUS' : 5, 
			'C1' : 0, 'C2' : 1, 'C3' : -1,
			#'DENSITY' : getEntityProperty(material, 'DENS'),  'POISSON' : getEntityProperty(material, 'POISSON'),
			#'E' : getEntityProperty(material, 'YOUNG'),
			#'G' :  getEntityProperty(material, 'YOUNG')/(2*(1+getEntityProperty(material, 'POISSON')))
				}
		self.beamSectionCcs = base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
		
		self.beamsCcs = list()
		for node in self.beamNodesCcs:
			vals = {'Name': 'BEAM_CLIP_CONTRA_SIDE',
				'PID': self.beamSectionCcs._id,
				'NODE1': self.connectingBeamsCenterNode2._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCcs.append(beam)
		
		self.clipEntities['beams_ccs'] = self.beamsCcs
		self.clipEntities['beams_ccs'].append(self.beamSectionCcs)
		
		base.RedrawAll()
			
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipSide(self):
		
		# find nodes for initial selection
		searchEntities = self.clipAreaShells#base.CollectEntities(constants.ABAQUS, None, "SHELL")
		
		# if no elements were selected before try to find the nearest ones
		if len(self.selectedElementsBeamCs) == 0:
			nearestElements = list()
			# some points may not be defined because of non standart clip shape
			try:
				coords = [np.array(getHotPointCoords(self.centerCoordNode))]
				coords.append(np.array(getHotPointCoords(self.centerCoordNode)) + 4*np.array(self.sideProjectionVectorPlus))
				coords.append(np.array(getHotPointCoords(self.centerCoordNode)) + 4*np.array(self.sideProjectionVectorMinus))
				for coord in coords:
					nearestElements.extend(findNearestElements(coord, searchEntities))
			except Exception as e:
				pass
		else:
#			# delete already created beams
#			base.DeleteEntity(self.beamsCs, force=True)
			nearestElements = self.selectedElementsBeamCs
		
		print('Select nodes for beam definition: CONNECTOR - CLIP.')
		selectedElements = base.PickEntities(constants.ABAQUS, "SHELL", initial_entities=nearestElements)
		
		if selectedElements is None:
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP side!'))
			
		self.beamNodesCs = base.CollectEntities(constants.ABAQUS, selectedElements, "NODE")
		
		# create beams
#		print('Select nodes for beam definition: CONNECTOR - CLIP.')
#		self.beamNodesCs = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = initialNodes)
		
#		try:
#			self.beamNodesCs.remove(self.connectingBeamsCenterNode1)
#		except:
#			self.beamNodesCs = None
#			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP!'))

		if len(self.beamNodesCs) == 0:
			self.beamNodesCs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP!'))
		
		# save selected elements for further re-selection
		self.selectedElementsBeamCs = selectedElements
		self.beamsCsDefined = True
		
		elements = base.NodesToElements(self.beamNodesCs)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		self.beamPropCs = base.GetEntity(constants.ABAQUS, 'SHELL_SECTION', getEntityProperty(element, 'PID'))
		if self.beamPropCs is None:
			self.beamPropCs = base.GetEntity(constants.ABAQUS, 'LAMINATE', getEntityProperty(element, 'PID'))
			# create dummy material
			vals = {
				'Name': 'ABS_BEAMS_NO_CREEP',
				'DEFINED' : 'YES',
				'Elasticity' : 'ELASTIC',
				'Plasticity (Rate Indep.)' : 'PLASTIC', 
				'Plasticity (Rate Dep.)' : 'CREEP',
				 '*DENSITY' : 'YES',
				 'DENS' : 7.85E-12, 
				 '*ELASTIC' : 'YES',
				 # 'TYPE' : 'ISOTROPIC',
				 'YOUNG' : 210000, 'POISSON' : 0.3
				 }
								
			beamMaterial = base.CreateEntity(constants.ABAQUS, "MATERIAL", vals)
			self.beamCsMID = beamMaterial._id
		else:
			self.beamCsMID = getEntityProperty(self.beamPropCs, 'MID')
		
		# create beam section
		vals = {'Name': 'BEAM_SECTION',
			'TYPE_':'SECTION', 'MID': self.beamCsMID,
			'SECTION': 'CIRC', 'TYPE':'B31', 'optional2':'H',
			'RADIUS' : 5, 
			'C1' : 0, 'C2' : 1, 'C3' : -1,
			#'DENSITY' : getEntityProperty(material, 'DENS'),  'POISSON' : getEntityProperty(material, 'POISSON'),
			#'E' : getEntityProperty(material, 'YOUNG'),
			#'G' :  getEntityProperty(material, 'YOUNG')/(2*(1+getEntityProperty(material, 'POISSON')))
				}
		self.beamSectionCs = base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
		
		self.beamsCs = list()
		for node in self.beamNodesCs:
			vals = {'Name': 'BEAM_CLIP_SIDE',
				'PID': self.beamSectionCs._id,
				'NODE1': self.connectingBeamsCenterNode1._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCs.append(beam)
		
		self.clipEntities['beams_cs'] = self.beamsCs
		self.clipEntities['beams_cs'].append(self.beamSectionCs)
		
		base.RedrawAll()
		

# ==============================================================================

class SkodaBeamType(AudiBeamType):
	
	TYPE_NAME = 'SKODA'
	INFO = 'SKODA CONNECTOR type clip consists of 3 connectors joined together with steel beams of very low density and beams joining connector with a clip and its contra side.'
	ICON = os.path.join(util.PATH_RES, 'icons', 'clip_beam_skoda.png')
	
	CONNECTOR_ELASTICITY = [1, 1, 1, 10, 10, 10]
	CONNECTOR_DISTANCE = 5.0
	CONNECTING_BEAM_SECTION_ID = 5001
	
	#-------------------------------------------------------------------------
	
	def createNodesForConnector(self):
				
		# create nodes for entities
		#zVector = self.middlePointCoords - self.centerCoordPointCoords
		#zVectorNorm = zVector/ np.linalg.norm(zVector)
		zVectorNorm = np.array(self.largeFaceNormal)
		
		xVectorNorm = self.sideProjectionVectorPlus/ np.linalg.norm(self.sideProjectionVectorPlus)
				
		xMove = self.CONNECTOR_DISTANCE*xVectorNorm
		yMove = -1*self.CONNECTOR_DISTANCE*np.array(self.smallFaceOrthoVector)#smallFaceNormal)
		zMove = self.CONNECTOR_LENGTH*zVectorNorm
				
		# connector C1
		con1Node1Coords = self.centerCoordPointCoords - xMove - 0.5*zMove
		con1Node2Coords = self.centerCoordPointCoords - xMove + 0.5*zMove
		
		self.con1Node1 =createNode(con1Node1Coords)
		self.con1Node2 = createNode(con1Node2Coords)
		
		# connector C2
		con2Node1Coords = self.centerCoordPointCoords + xMove - 0.5*zMove
		con2Node2Coords = self.centerCoordPointCoords + xMove + 0.5*zMove
		
		self.con2Node1 =createNode(con2Node1Coords)
		self.con2Node2 = createNode(con2Node2Coords)
		
		# connector C3
		con3Node1Coords = self.centerCoordPointCoords + yMove - 0.5*zMove
		con3Node2Coords = self.centerCoordPointCoords + yMove + 0.5*zMove
		
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
		
		self.con3Node1 =createNode(con3Node1Coords)
		self.con3Node2 =createNode(con3Node2Coords)
		
		# center nodes
		self.connectingBeamsCenterNode1 = createNode(np.median([con1Node1Coords, con2Node1Coords], axis=0))
		self.connectingBeamsCenterNode2 = createNode(np.median([con1Node2Coords, con2Node2Coords], axis=0))
					 
	#-------------------------------------------------------------------------
	
	def createConnector(self):
				
		# create connector elasticity
		vals = {'Name': 'CONNECTOR_ELASTICITY',
			 'COMP': 'YES',
			 'COMP(1)': 'YES', 'El.Stiff.(1)': self.CONNECTOR_ELASTICITY[0],
			 'COMP(2)': 'YES', 'El.Stiff.(2)': self.CONNECTOR_ELASTICITY[1],
			 'COMP(3)': 'YES', 'El.Stiff.(3)': self.CONNECTOR_ELASTICITY[2],
			 'COMP(4)': 'YES', 'El.Stiff.(4)': self.CONNECTOR_ELASTICITY[3],
			 'COMP(5)': 'YES', 'El.Stiff.(5)': self.CONNECTOR_ELASTICITY[4],
			 'COMP(6)': 'YES', 'El.Stiff.(6)': self.CONNECTOR_ELASTICITY[5]
			}
		self.connectorElasticity = base.CreateEntity(constants.ABAQUS, "CONNECTOR_ELASTICITY", vals)
	
		# create connector stop
		vals = {'Name': 'CONNECTOR_STOP_C1_C2',
			 'COMP (1)': 'YES', 'Low.Lim.(1)': self.xLow, 'Up.Lim.(1)': self.xUp, 
			 'COMP (2)': 'YES', 'Low.Lim.(2)': self.yLow, 'Up.Lim.(2)': self.yUp, 
			 'COMP (3)': 'YES', 'Low.Lim.(3)': self.zLow, 'Up.Lim.(3)': self.zUp, 
			}
		self.connectorStop = base.CreateEntity(constants.ABAQUS, "CONNECTOR_STOP", vals)
		
		# create connector behavior
		vals = {'Name': 'CONNECTOR_BEHAVIOR_C1_C2',
			'*ELASTICITY': 'YES', 'EL>data': self.connectorElasticity._id,
			'*STOP':'YES', 'STP>data': self.connectorStop._id,
			}
		self.connectorBehavior = base.CreateEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", vals)
		
		# create a connector section
		vals = {'Name': 'CONNECTOR_SECTION_C1_C2',
			 'MID': self.connectorBehavior._id,
			'COMPONENT_1': 'CARDAN', 'COMPONENT_2':  'CARTESIAN', 'ORIENT_1': self.coordSystem._id,
			}
		self.connectorSection = base.CreateEntity(constants.ABAQUS, "CONNECTOR_SECTION", vals)
				
		# create a connector C1
		vals = {'Name': 'CONNECTOR_C1',
			'PID': self.connectorSection._id,
			'G1':  self.con1Node1._id, 'G2': self.con1Node2._id}
		self.connectorC1 = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)
		
		# create a connector C2
		vals = {'Name': 'CONNECTOR_C2',
			'PID': self.connectorSection._id,
			'G1':  self.con2Node1._id, 'G2': self.con2Node2._id}
		self.connectorC2 = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)
		
		
		
		# create connector stop for CONNECTOR C3
		vals = {'Name': 'CONNECTOR_STOP_C3',
			 'COMP (3)': 'YES', 'Low.Lim.(3)': self.zLow, 'Up.Lim.(3)': self.zUp, 
			}
		self.connectorStopC3 = base.CreateEntity(constants.ABAQUS, "CONNECTOR_STOP", vals)
		
		# create connector behavior for CONNECTOR C3
		vals = {'Name': 'CONNECTOR_BEHAVIOR_C3',
			'*ELASTICITY': 'YES', 'EL>data': self.connectorElasticity._id,
			'*STOP':'YES', 'STP>data': self.connectorStopC3._id,
			}
		self.connectorBehaviorC3 = base.CreateEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", vals)
		
		# create a connector section for CONNECTOR C3
		vals = {'Name': 'CONNECTOR_SECTION_C3',
			 'MID': self.connectorBehaviorC3._id,
			'COMPONENT_1': 'CARDAN', 'COMPONENT_2':  'CARTESIAN', 'ORIENT_1': self.coordSystem._id,
			}
		self.connectorSectionC3 = base.CreateEntity(constants.ABAQUS, "CONNECTOR_SECTION", vals)
		
		# create a connector C3
		vals = {'Name': 'CONNECTOR_C3',
			'PID': self.connectorSectionC3._id,
			'G1':  self.con3Node1._id, 'G2': self.con3Node2._id}
		self.connectorC3 = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)
		
		self.clipEntities['connector'] = [
			self.connectorElasticity,
			self.connectorStop,
			self.connectorBehavior,
			self.connectorSection,
			self.connectorC1, self.connectorC2,
			self.connectorStopC3,
			self.connectorBehaviorC3,
			self.connectorSectionC3,
			self.connectorC3]
		
		self.connectConnectorsWithBeams()
	
	#-------------------------------------------------------------------------
	
	def connectConnectorsWithBeams(self):
		
		def getBeamSection():
			beamSection = base.GetEntity(constants.ABAQUS, 'BEAM_SECTION', self.CONNECTING_BEAM_SECTION_ID)

			if beamSection is None:
#TODO: this parameter inconsistency is solved in ANSA V18. (TYPE -> ELASTIC_TYPE, etc.)
				# create material for beam section
				vals = {
					'Name': 'CONNECTOR_BODY_STEEL_LIGHT',
					'DEFINED' : 'YES',
					'Elasticity' : 'ELASTIC',
					'Plasticity (Rate Indep.)' : 'PLASTIC', 
					'Plasticity (Rate Dep.)' : 'CREEP',
					 '*DENSITY' : 'YES',
					 'DENS' : 7.85E-12, 
					 '*EXPANSION' : 'YES', 
					 #'TYPE' : 'ISO',
					 'a' : 1.2E-5,
					 '*ELASTIC' : 'YES',
					 # 'TYPE' : 'ISOTROPIC',
					 'YOUNG' : 210000, 'POISSON' : 0.3
					 }
									
				beamMaterial = base.CreateEntity(constants.ABAQUS, "MATERIAL", vals)
						
				# create a new beam section for connecting beams
				vals = {'Name': 'CONNECTOR_BODY_BEAM_SECTION',
					'PID': self.CONNECTING_BEAM_SECTION_ID,
					'TYPE_':'SECTION', 'MID': beamMaterial._id,
					'SECTION': 'CIRC', 'TYPE':'B31', 'optional2':'H',
					'RADIUS' : 5, 'C1' : 0, 'C2' : 1, 'C3' : -1}
				beamSection = base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
				
			return beamSection
						
		self.connectingBeamsSection = getBeamSection()
		
		# create connecting beams
		self.connectingBeams = list()
		for node in [self.con1Node1, self.con2Node1, self.con3Node1]:
			vals = {'Name': 'BEAM_CONNECTOR_CLIP_SIDE',
				'PID': self.connectingBeamsSection._id,
				'NODE1': self.connectingBeamsCenterNode1._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.connectingBeams.append(beam)
		for node in [self.con1Node2, self.con2Node2, self.con3Node2]:
			vals = {'Name': 'BEAM_CONNECTOR_CLIP_CONTRA_SIDE',
				'PID': self.connectingBeamsSection._id,
				'NODE1': self.connectingBeamsCenterNode2._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.connectingBeams.append(beam)
		
		self.clipEntities['connector_beams'] = self.connectingBeams

# ==============================================================================

class SymmetricalClip(object):
	
	PASTE_TOLERANCE = 0.2
	
	def __init__(self, parentClip):
		
		self.parentClip = parentClip
		
		self.parentClip.createSymmetricalCoorSys()
		self.mirrorClip()
		self.updateConnectorOrienation()
		self.showNearElements()
	
	#-------------------------------------------------------------------------
	
	def mirrorClip(self):
		
		entities = list()
		for ents in self.parentClip.clipEntities.values(): 
			if type(ents) is list:
				entities.extend(ents)
			else:
				entities.append(ents)
		
		collector = base.CollectNewModelEntities(constants.ABAQUS, "CONNECTOR")
		base.GeoSymmetry("COPY", "AUTO_OFFSET", "SAME PART", "NONE", entities, keep_connectivity=True)
		self.newConnectors = collector.report()
	
	#-------------------------------------------------------------------------
	
	def updateConnectorOrienation(self):
		
		# find the PID of the new mirrored connectors		
		newConnectorSections = base.CollectEntities(constants.ABAQUS, self.newConnectors, "CONNECTOR_SECTION", recursive=True)
	
		# update individually each connector section
		for newConnectorSection in newConnectorSections:
			newConnectorBehaviorID = getEntityProperty(newConnectorSection, 'MID')
			newConnectorBehavior = base.GetEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", newConnectorBehaviorID)
			
			connectorStopID =  getEntityProperty(newConnectorBehavior, 'STP>data')
			connectorStop = base.GetEntity(constants.ABAQUS, "CONNECTOR_STOP", connectorStopID)
			
			vals = dict()
			vals['Name'] = getEntityProperty(connectorStop, 'Name')
			xLow = getEntityProperty(connectorStop, 'COMP (1)')
			if xLow == 'YES':
				vals.update({'COMP (1)': 'YES', 'Low.Lim.(1)': -1*self.parentClip.xUp, 'Up.Lim.(1)': -1*self.parentClip.xLow,
				 'COMP (2)': 'YES', 'Low.Lim.(2)': self.parentClip.yLow, 'Up.Lim.(2)': self.parentClip.yUp})
			
			vals.update({ 'COMP (3)': 'YES', 'Low.Lim.(3)': self.parentClip.zLow, 'Up.Lim.(3)': self.parentClip.zUp})
			
			# create the new connector stop
			newConnectorStop = base.CreateEntity(constants.ABAQUS, "CONNECTOR_STOP", vals)
		
			# create the new connector behavior
			vals = {'Name': getEntityProperty(newConnectorBehavior, 'Name'),
				'*ELASTICITY': 'YES', 'EL>data': self.parentClip.connectorElasticity._id,
				'*STOP':'YES', 'STP>data': newConnectorStop._id,
				}
			newConnectorBehavior = base.CreateEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", vals)
			
			# update coor sys and connector behaviour
			vals = {
				'ORIENT_1': self.parentClip.symmCoordSystem._id,
				'MID' : newConnectorBehavior._id}
			base.SetEntityCardValues(constants.ABAQUS, newConnectorSection, vals)
	
	#-------------------------------------------------------------------------
	
	def showNearElements(self):
		
		base.Near(radius=10., dense_search=True, custom_entities=self.newConnectors)
		# hide geometry
		ent = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True )
		status = base.Not(ent, constants.ABAQUS)
		
		#entities = self.parentClip.clipEntities
		#entities.extend(self.newConnectors)
		#base.BestView(self.symmCoordSystem)
		
		base.SetViewAngles(f_key="F5")
		
		# autopaste
		ansa.mesh.AutoPaste(visible = True, project_on_geometry=False, project_2nd_order_nodes=False, move_to="FE pos", distance=self.PASTE_TOLERANCE, preserve_id = 'min')
		

# ==============================================================================

def createPoint(pointCoords, name=''):
	
	try:
		newPointEntity = base.Newpoint(*pointCoords)
		base.SetEntityCardValues(constants.ABAQUS, newPointEntity, {'Name': name})
	except Exception as e:
		raise SmartClipException(str(e))
	
	return newPointEntity
			
# ==============================================================================

def createNode(nodeCoords):
		
	newNodeEntity = base.CreateEntity(constants.ABAQUS, "NODE",  {'X': nodeCoords[0], 'Y': nodeCoords[1], 'Z': nodeCoords[2]})
	
	return newNodeEntity
		
# ==============================================================================

def showMessage(message):
	#w = guitk.BCWindowCreate('Missing entity', guitk.constants.BCOnExitDestroy)
	#f = guitk.BCFrameCreate(w)
	#l = guitk.BCBoxLayoutCreate(f, guitk.constants.BCHorizontal)
	#label =guitk.BCLabelCreate(l, message)
	#guitk.BCDialogButtonBoxCreate(w)
	#guitk.BCShow(w)
	
	messageWindow = guitk.BCMessageWindowCreate(guitk.constants.BCMessageBoxInformation, message, True)
	guitk.BCMessageWindowSetAcceptButtonText(messageWindow, "OK")
	guitk.BCMessageWindowSetRejectButtonVisible(messageWindow, False)
	answer = guitk.BCMessageWindowExecute(messageWindow)
	
# ==============================================================================
'''
def getStopDistance(clipFace, mateFace, centerCoordNode, direction=1):
	# searching for distances
	
	
	mNodeClipFace = ansa.base.CreateMeasurement([clipFace, centerCoordNode], 'DISTANCE_SURFACE')
	mNodeMateFace = ansa.base.CreateMeasurement([mateFace, centerCoordNode], 'DISTANCE_SURFACE')	
	mFace2face = ansa.base.CreateMeasurement([clipFace, mateFace], 'DISTANCE_GEOMETRY')
	
	faceDist = getEntityProperty(mFace2face, 'RESULT')
	
	nodeFaceClipDist = getEntityProperty(mNodeClipFace, 'RESULT')
	nodeFaceMateDist = getEntityProperty(mNodeMateFace, 'RESULT')
	#print(nodeFaceClipDist, nodeFaceMateDist)

	if nodeFaceClipDist > nodeFaceMateDist:
		print('Penetration detected! Distance set to: 0.01')
		faceDist = 0.01
	
	if abs(faceDist) < 0.01:
		faceDist = 0.01
	else:
		faceDist = round(faceDist, 2)
	
	base.DeleteEntity(mNodeClipFace)
	base.DeleteEntity(mNodeMateFace)
	
	return faceDist*direction
'''	
# ==============================================================================

def getFaceNeighbourFaces(faceEntity, exclude=list()):
	
	faceCons = base.CollectEntities(constants.ABAQUS, faceEntity, "CONS")
	neighbourFaces = ansa.base.GetFacesOfCons(cons = faceCons)
	
	# remove parent faces
	if type(faceEntity) is list:
		exclude.extend(faceEntity)
	else:
		exclude.append(faceEntity)
	
	for face in exclude:
		if face in neighbourFaces:
			neighbourFaces.remove(face)
	
	return neighbourFaces

# ==============================================================================

def getConMiddle(con):
	
	coords = getConsHotPointCoords(con)
	middlePointCoords = np.median(coords, axis=0)
	
	return middlePointCoords
	
	

# ==============================================================================

def sortEntities(entities, sortFunction, valueLimit=None):
	
	values = list()
	filteredEntities = list()
	for entity in entities:
		currentValue = sortFunction(entity)
		if valueLimit is not None and currentValue>valueLimit:
			continue
		values.append(currentValue)
		filteredEntities.append(entity)
		
	indexes = np.argsort(np.array(values))
	sortedEntities = np.array(filteredEntities)[indexes]
	
	return sortedEntities

# ==============================================================================

def getConLength(conEntity):
		
	cardField = base.GetEntityCardValues(constants.ABAQUS, conEntity, ['Length', 'Num. of Nodes'])
	return cardField['Length']

# ==============================================================================

def getConsHotPointCoords(conEntity):
	
		# hot points of the first con
		hotPoints = base.CollectEntities(constants.ABAQUS, conEntity, "HOT POINT")
		
		coords = list()
		for hotPoint in hotPoints:	
				coords.append(getHotPointCoords(hotPoint))
		
		return coords

# ==============================================================================

def getHotPointCoords(hotPoint):
		coord = list()
		coord.append(getEntityProperty(hotPoint, 'X'))
		coord.append(getEntityProperty(hotPoint, 'Y'))
		coord.append(getEntityProperty(hotPoint, 'Z'))
				
		return coord

#==============================================================================

def getEntityProperty(entity, propertyName):
		
		cardField = base.GetEntityCardValues(constants.ABAQUS, entity, [propertyName])
		return cardField[propertyName]

#==============================================================================

def findNearestElements(coords, searchEntities=None, maxIter=50):
	
	if searchEntities is None:
		searchEntities = base.CollectEntities(constants.ABAQUS, None, "SHELL")
		
	tolerance = 0.1
	increment = 0.1
	i = 0
	nearElements = None
	while nearElements is None: #len(nearElements) == 0:#
		nearElements = base.NearElements(search_entities=searchEntities, coordinates=coords, tolerance=tolerance)
		tolerance += increment
		
		if i > maxIter:
			return None
			break
		i += 1	
			
	return nearElements[0]

#==============================================================================
    
def hideAllFaces():
	ent = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True )
	status = base.Not(ent, constants.ABAQUS)
		

# ==============================================================================

#@ansa.session.defbutton('Mesh', 'SmartClip')
def runSmartClip(geomType='Standart', beamType='AUDI'):
	
	'''"SmartClip" tool is an utility to make the clip definition as easy as possible.
	
According to the guiding CON that must be selected by a user, searches for normals of neighbour faces and defines a base
coordinate system orientation. Projects points to its boundaries in the correspondent vectors and searches for their projection to
the clip contra part. Measures projection distance and defines CONNECTOR STOP property.
In the second step, the user is requested to select nodes for the beam definition connecting the connector element with the clip
itself and the contra part.

Usage:
	1. select guiding CON
	2. select nodes connecting the connector element and the clip contra part
	3. select nodes connecting the connector element and the clip itself

NOTE:
	SmartClip requires geometry and FEM model loaded into the one session.
	Keep FEM model visible (visib switch on) in the time of guiding CON selection for the best result.
'''
	
	sc = SmartClip(geomType, beamType)
	sc.run()
	
# ==============================================================================

#if __name__ == '__main__':
#	runSmartClip('Reversed', 'SKODA')
#	runSmartClip('Standart', 'SKODA')
#	runSmartClip('Standart', 'AUDI')
#	runSmartClip('Reversed', 'AUDI')

