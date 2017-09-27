# PYTHON script
import os
import sys
import numpy as np
import ansa
 
from ansa import base, constants, guitk


# ==============================================================================

PATH_BIN = os.path.dirname(os.path.abspath(__file__))
PATH_RES = os.path.normpath(os.path.join(PATH_BIN, '..', 'res'))
try:
	sys.path.append(PATH_BIN)
	import util
	
	print('Runnig devel version ', __file__)
	
except ImportError as e:
	ansa.ImportCode(os.path.join(PATH_BIN, 'util.py'))
	
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

class SmartClip(object):
	
	coordsDrawState = None
	
	def __init__(self, geomType='Standart', beamType='AUDI'):
		
		self._geomType = None
		self._beamType = None
		
		self.clipEntities= list()
				
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
	ICON = os.path.join(PATH_RES, 'icons', 'clip_geom_standart.png')
	
	CONNECTOR_LENGTH = 1.0
	
	def __init__(self, parentClip):
		
		self.parentClip = parentClip
		
		self.selectedCon = None
		self.clipEntities= self.parentClip.clipEntities
		
		self.stopDistanceMeasurements = dict()
		self.stopDistanceFaceCouples = dict()
		
		self.xLow = -1000
		self.xUp = 1000
		self.yLow = -1000
		self.yUp = 1000
		self.zLow = -1000
		self.zUp = 1000
			    
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
	
	def _getStopDistance(self, clipFacePoint, mateFacePoint, measurementDescription):

# TODO: get rid of redundant measurement entities and use just 2 point distance
# np.linalg.norm(np.array(clipFacePoint) - np.array(self.centerCoordNode))

		# searching for distances
		mNodeClipFace = ansa.base.CreateMeasurement([clipFacePoint, self.centerCoordNode], 'DISTANCE')
		mNodeMateFace = ansa.base.CreateMeasurement([mateFacePoint, self.centerCoordNode], 'DISTANCE')	
		mFace2face = ansa.base.CreateMeasurement([clipFacePoint, mateFacePoint], 'DISTANCE')
		
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
		
		
		self.stopDistanceMeasurements[measurementDescription] = mFace2face
		
		return faceDist
				
	#-------------------------------------------------------------------------
    
	def setBaseFaces(self):
						
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
		
		smallFaceCons = base.CollectEntities(constants.ABAQUS, self.smallFace, "CONS")
		smallFaceCons.remove(self.selectedCon)
		largeFaceCons = base.CollectEntities(constants.ABAQUS, self.largeFace, "CONS")
		largeFaceCons.remove(self.selectedCon)
		
		# find opposite con to selected one belonging to the smaller face
		sortedCons = sortEntities(smallFaceCons, getConLength)
		oppositeCon = sortedCons[-1]
		smallFaceCons.remove(oppositeCon)
		
		# find all faces on clip
		cons = [oppositeCon]
		for i in range(8):
			clipFaces = set(ansa.base.GetFacesOfCons(cons))
			clipFaces.discard(self.smallFace)
			clipFaces.discard(self.largeFace)
			
			cons = base.CollectEntities(constants.ABAQUS, clipFaces, "CONS")
			#newFaces = clipFaces.difference(checkedfaces)
		#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = clipFaces)
		
		# create points for coordinate system
		self.middlePointCoords = getConMiddle(self.selectedCon)
		self.topPointCoords = np.median([self.middlePointCoords, getConMiddle(oppositeCon)], axis=0)
		
		# guiding face normals
		self.smallFaceNormal = base.GetFaceOrientation(self.smallFace)
		self.largeFaceNormal = base.GetFaceOrientation(self.largeFace)
		
		# find opposite projection
		#self.oppositeProjectionVector = self.middlePointCoords - self.topEdgeMiddleCoords
		#self.oppositeProjectionVector = np.cross(smallFaceNormal, largeFaceNormal)
		
		self.oppositeProjectionVector = -1*np.array(self.largeFaceNormal)
		self.oppositeFace, self.oppositeFacePointCoords = self._getPointProjectionCoords(
			clipFaces, self.middlePointCoords, self.oppositeProjectionVector, searchedFaceName='z lower face - clip side')
		if self.oppositeFacePointCoords is not None:
			self.oppositeFacePoint = base.Newpoint(*self.oppositeFacePointCoords)
		
		# front face point
		self.frontFacePointCoords = self.middlePointCoords + 1*np.array(self.smallFaceNormal)
		self.frontFacePoint = base.Newpoint(*self.frontFacePointCoords)
		
		self.clipFaces = list(sortEntities(list(clipFaces), base.GetFaceArea))
		self.oppositeFacePointCoords =  self.oppositeFacePointCoords
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.median([self.oppositeFacePointCoords, self.middlePointCoords], axis=0)
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
		#base.Newpoint(*self.centerCoordPointCoords)
		
		# find side faces		
		searchOnFaces = self.clipFaces[:]
		self.sideProjectionVectorPlus = np.cross(self.smallFaceNormal, self.oppositeProjectionVector)
		self.sideFacePlus, sidePlusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, self.sideProjectionVectorPlus, searchedFaceName='x upper face - clip side')
		# move a point lower
		if sidePlusPointCoords is not None:
			sideFaceTangent = np.cross(self.largeFaceNormal, base.GetFaceOrientation(self.sideFacePlus))
			self.sidePlusPointCoords = sidePlusPointCoords + 1*sideFaceTangent#+ 1*np.array(self.smallFaceNormal)
			self.sideFacePlusPoint = base.Newpoint(*self.sidePlusPointCoords)
		
		searchOnFaces.remove(self.sideFacePlus)
		self.sideProjectionVectorMinus = np.cross(self.oppositeProjectionVector, self.smallFaceNormal)
		self.sideFaceMinus, sideMinusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, self.sideProjectionVectorMinus, searchedFaceName='x lower face - clip side')
		# move a point lower
		if sideMinusPointCoords is not None:
			sideFaceTangent = np.cross(base.GetFaceOrientation(self.sideFaceMinus), self.largeFaceNormal)
			self.sideMinusPointCoords = sideMinusPointCoords + 1*sideFaceTangent#+ 1*np.array(self.smallFaceNormal)
			self.sideFaceMinusPoint = base.Newpoint(*self.sideMinusPointCoords)
		
		# this is correct orthogonal vector that a small face should have in case of 90 degrees...
		self.smallFaceOrthoVector = np.cross(self.largeFaceNormal, self.sideProjectionVectorMinus)
		
	#-------------------------------------------------------------------------

	def setStopDistances(self, hideMeasurements=True):
		
		# searching for distances
		# show only relevant entities
		base.All()
		base.Or(self.largeFace, constants.ABAQUS)
		base.Near(radius=10., dense_search=True, custom_entities=self.largeFace)
		# hide property
		ent = base.CollectEntities(constants.ABAQUS, [self.clipProperty], "FACE", filter_visible=True )
		status = base.Not(ent, constants.ABAQUS)
	
		# find faces on clip mate geometry
		neighbourFaces = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True)
		self.neighbourFaces = sortEntities(neighbourFaces, base.GetFaceArea)
		
		#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = self.neighbourFaces)
		
		stopDistanceMethods = [self.findZlowDist, self.findZupDist, self.findXupDist, self.findXlowDist,
			self.findYupDist, self.findYlowDist]
		for stopDistanceMethod in stopDistanceMethods:
			try:
				stopDistanceMethod()
			except Exception as e:
				continue
					
		status = base.And(ent, constants.ABAQUS)
		
		if hideMeasurements:
			self.hideMeasurements()
	
	#-------------------------------------------------------------------------

	def findZupDist(self):
		# find opposite projection mate
		self.oppositeNeighbourFace, self.oppositeNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.oppositeFacePointCoords, self.oppositeProjectionVector, searchedFaceName='z upper face - clip contra side')
		self.oppositeNeighbourFacePoint = base.Newpoint(*self.oppositeNeighbourFacePointCoords)
		self.zUp = self.CONNECTOR_LENGTH + self._getStopDistance(self.oppositeFacePoint, self.oppositeNeighbourFacePoint, 'zUp')
		
		self.stopDistanceFaceCouples['zUp'] = [self.oppositeFace, self.oppositeNeighbourFace]
		
	#-------------------------------------------------------------------------

	def findZlowDist(self):
		# find front projection mate
		self.frontNeighbourFace, self.frontNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.frontFacePointCoords, self.largeFaceNormal, searchedFaceName='z lower face - clip contra side')
		self.frontNeighbourFacePoint = base.Newpoint(*self.frontNeighbourFacePointCoords)
		self.zLow = self.CONNECTOR_LENGTH - 1*self._getStopDistance(self.frontFacePoint, self.frontNeighbourFacePoint, 'zLow')
		
		self.stopDistanceFaceCouples['zLow'] = [self.largeFace, self.frontNeighbourFace]
		
	#-------------------------------------------------------------------------

	def findXupDist(self):
		# find side plus projection mate
		self.sidePlusNeighbourFace, self.sidePlusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sidePlusPointCoords, self.sideProjectionVectorPlus, searchedFaceName='x upper face - clip contra side')
		self.sidePlusNeighbourFacePoint = base.Newpoint(*self.sidePlusNeighbourFacePointCoords)
		self.xUp = self._getStopDistance(self.sideFacePlusPoint, self.sidePlusNeighbourFacePoint, 'xUp')
		
		self.stopDistanceFaceCouples['xUp'] = [self.sideFacePlus, self.sidePlusNeighbourFace]
		
	#-------------------------------------------------------------------------

	def findXlowDist(self):
		# find side minus projection mate
		self.sideMinusNeighbourFace, self.sideMinusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sideMinusPointCoords, self.sideProjectionVectorMinus, searchedFaceName='x lower face - clip contra side')
		self.sideMinusNeighbourFacePoint = base.Newpoint(*self.sideMinusNeighbourFacePointCoords)
		self.xLow = -1*self._getStopDistance(self.sideFaceMinusPoint, self.sideMinusNeighbourFacePoint, 'xLow')
		
		self.stopDistanceFaceCouples['xLow'] = [self.sideFaceMinus, self.sideMinusNeighbourFace]

	#-------------------------------------------------------------------------

	def findYupDist(self):		
		# find top neighbour face
		self.topNeighbourFace, self.topNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.topPointCoords, self.smallFaceNormal, searchedFaceName='y upper face - clip contra side')
		
		# 1. find the edge of the front neighbour face and top neighbour face
		# 2. find the projection of the front neighbour point on this edge
		# 3. find projection of this point on the neighbour edge to the plane of the small clip face
		# 4. this should be the smallest distance in Y direction
		
		# 1. find the edge of the front neighbour face and top neighbour face
		def findEdge(face1, face2):
			face1cons = base.CollectEntities(constants.ABAQUS, face1, "CONS")
			for face1con in face1cons:
				neighbourFaces = base.GetFacesOfCons(face1con)
				if face2 in neighbourFaces:
					return face1con
			return None
		
		
		neighbourTopEdgeCon = findEdge(self.frontNeighbourFace, self.topNeighbourFace)
		if neighbourTopEdgeCon is None:
# TODO: this is maybe enought?
			frontNeighbourFaceCons = set(base.CollectEntities(constants.ABAQUS, self.frontNeighbourFace, "CONS"))
			topNeighbourFaceCons = set(base.CollectEntities(constants.ABAQUS, self.topNeighbourFace, "CONS"))
			neighbourTopEdgeCon = list(frontNeighbourFaceCons.intersection(topNeighbourFaceCons))[0]
		
		
		# 2. find the projection of the front neighbour point on this edge
		self.topNeighbourFacePointCoords = ansa.calc.ProjectPointToCons(self.frontNeighbourFacePointCoords, neighbourTopEdgeCon)[0]
		self.topNeighbourFacePoint = base.Newpoint(*self.topNeighbourFacePointCoords)
			
		# 3. find projection of this point on the neighbour edge to the plane of the small clip face
		self.topPointCoords = base.ProjectPointToPlane(self.topNeighbourFacePointCoords, 
			self.middlePointCoords, self.smallFaceNormal)
		self.topPoint = base.Newpoint(*self.topPointCoords)
		
		# 4. this should be the smallest distance in Y direction
		self.yUp = self._getStopDistance(self.topPoint, self.topNeighbourFacePoint, 'yUp')
		
		self.stopDistanceFaceCouples['yUp'] = [self.smallFace, self.topNeighbourFace]
		
	#-------------------------------------------------------------------------

	def findYlowDist(self):
		self.yLow = -1000
	
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
			
		
		if len(selectedFaces) != 2:
			self.showMeasurements()
			raise(SmartClipException('Please select just two faces.'))
			
		# find selected clip face and its mate
		mateProperty = None
		faceProperties = dict()
		for face in selectedFaces:
			faceProperty = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(face, 'PID'))
			faceProperties[faceProperty] = face
			if faceProperty != self.clipProperty:
				mateProperty = faceProperty
				
		if mateProperty is None:
			self.showMeasurements()
			raise(SmartClipException('Selected faces must have different property!'))
		
		clipFace = faceProperties[self.clipProperty]
		mateFace = faceProperties[mateProperty]
		
		if alterName is not None:
			stopDistName = alterName
		
		stopDistanceDirections = {
			'zUp' : self.oppositeProjectionVector,
			'zLow' : self.largeFaceNormal,
			'xUp' :  self.sideProjectionVectorPlus,
			'xLow' :  self.sideProjectionVectorMinus,
			'yUp' : self.smallFaceOrthoVector,
			'yLow' : -1*self.smallFaceOrthoVector
			}
		
		projectionVector = stopDistanceDirections[stopDistName]
		
		# apply non-normal face measurement
		if stopDistName in ['xUp', 'xLow']:			
			# find points and their distance
			measurementEntity = None
			# move the middle point until the projection is found
			for inc in range(-20, 20):
				pointCoords = self.centerCoordPointCoords + 0.5*float(inc)*np.array(self.smallFaceOrthoVector)
				face, matePointCoords = self._getPointProjectionCoords([mateFace], pointCoords, projectionVector, tolerance=100)
				
				if matePointCoords is not None:
					face, clipPointCoords = self._getPointProjectionCoords([clipFace], pointCoords, projectionVector, tolerance=100)
					
					if clipPointCoords is not None:
						matePoint = base.Newpoint(*matePointCoords)
						clipPoint = base.Newpoint(*clipPointCoords)
						measurementEntity = ansa.base.CreateMeasurement([clipPoint, matePoint], 'DISTANCE')
						break

			if measurementEntity is None:
				measurementEntity = ansa.base.CreateMeasurement(selectedFaces, 'DISTANCE_GEOMETRY')
		
		else:
			baseMeasurementEntity = ansa.base.CreateMeasurement(selectedFaces, 'DISTANCE_GEOMETRY')
			
			try:
				# find the point that belongs to the clip plane
				firstPointCoordsDict = base.GetEntityCardValues(constants.ABAQUS, baseMeasurementEntity, ['POINT1_X', 'POINT1_Y', 'POINT1_Z'])
				firstPointCoords = [firstPointCoordsDict[k] for k in ['POINT1_X', 'POINT1_Y', 'POINT1_Z']]
				secondPointCoordsDict = base.GetEntityCardValues(constants.ABAQUS, baseMeasurementEntity, ['POINT2_X', 'POINT2_Y', 'POINT2_Z'])
				secondPointCoords = [secondPointCoordsDict[k] for k in ['POINT2_X', 'POINT2_Y', 'POINT2_Z']]
				
				def getPointDistance(pointCoords):
					face, clipPointCoords = self._getPointProjectionCoords([clipFace], pointCoords, projectionVector)
					distance = np.linalg.norm(np.array(pointCoords) - np.array(clipPointCoords))
					return distance
				
				distances = sortEntities([
					firstPointCoords, secondPointCoords], getPointDistance)
				matePoint = base.Newpoint(*distances[-1])
				
				face, clipPointCoords = self._getPointProjectionCoords([clipFace], distances[-1], projectionVector)
				clipPoint = base.Newpoint(*clipPointCoords)
				
				# delete base measurement and create local - orthogonal between two new points
				measurementEntity = ansa.base.CreateMeasurement([clipPoint, matePoint], 'DISTANCE')
				base.DeleteEntity(baseMeasurementEntity, force=True)
			except Exception as e:
				print(str(e))
				measurementEntity = ansa.base.CreateMeasurement(selectedFaces, 'DISTANCE_GEOMETRY')
			
			
		distance = round(getEntityProperty(measurementEntity, 'RESULT'), 2)

# TODO: this should be solved some other way!! :(
		# change name in order to different coordinate system direction
		if alterName is not None:
			stopDistName = alterName
		
		# fix directions
		if stopDistName == 'zLow':
			distance = self.CONNECTOR_LENGTH - 1*distance
		elif stopDistName == 'zUp':
			distance = self.CONNECTOR_LENGTH + distance
		elif stopDistName == 'xLow':
			distance = - 1*distance
		elif stopDistName == 'yLow':
			distance = - 1*distance
		
		try:
			base.DeleteEntity(self.stopDistanceMeasurements[stopDistName], force=True)
		except:
			pass
		
		# set the new entities
		self.stopDistanceMeasurements[stopDistName] = measurementEntity
		self.stopDistanceFaceCouples[stopDistName] = selectedFaces
		setattr(self, stopDistName, distance)
		
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
		
		pointNames = [
			'oppositeFacePoint',
			'frontFacePoint',
			'sideFacePlusPoint',
			'sideFaceMinusPoint',
			
			'oppositeNeighbourFacePoint',
			'frontNeighbourFacePoint',
			'sidePlusNeighbourFacePoint',
			'sideMinusNeighbourFacePoint',
			'topPoint',
			'topNeighbourFacePoint',
			]
		entities = list()
		for pointName in pointNames:
			if hasattr(self, pointName):
				entities.append(getattr(self, pointName))
		
		status = base.Not(entities, constants.ABAQUS)
	
	#-------------------------------------------------------------------------

	def createCoorSystem(self):
		
		self.thirdPointCoords = np.array(self.middlePointCoords)+np.array(self.sideProjectionVectorPlus)
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  self.middlePointCoords[0], 'B2':  self.middlePointCoords[1], 'B3':  self.middlePointCoords[2],
			'C1':  self.thirdPointCoords[0], 'C2':  self.thirdPointCoords[1], 'C3':  self.thirdPointCoords[2]}
		self.coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

	#-------------------------------------------------------------------------
	
	def createSymmetricalCoorSys(self):
		
		thirdPointCoords = np.array([1,-1,1])*np.array(self.parentClip.middlePointCoords)+np.array([1,-1,1])*np.array(self.parentClip.sideProjectionVectorMinus)
		
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.parentClip.centerCoordPointCoords[0], 'A2':  -1*self.parentClip.centerCoordPointCoords[1], 'A3':  self.parentClip.centerCoordPointCoords[2],
			'B1':  self.parentClip.middlePointCoords[0], 'B2':  -1*self.parentClip.middlePointCoords[1], 'B3':  self.parentClip.middlePointCoords[2],
			'C1':  thirdPointCoords[0], 'C2':  thirdPointCoords[1], 'C3':  thirdPointCoords[2]}
				
		self.symmCoordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

# ==============================================================================

class ReversedGeomType(StandartGeomType):
	
	TYPE_NAME = 'Reversed'
	INFO ='Reversed geometrical clip type.'
	ICON = os.path.join(PATH_RES, 'icons', 'clip_geom_reversed.png')
	
	#-------------------------------------------------------------------------
    
	def setBaseFaces(self):
						
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
		
		smallFaceCons = base.CollectEntities(constants.ABAQUS, self.smallFace, "CONS")
		smallFaceCons.remove(self.selectedCon)
		largeFaceCons = base.CollectEntities(constants.ABAQUS, self.largeFace, "CONS")
		largeFaceCons.remove(self.selectedCon)
		
		# find opposite con to selected one belonging to the smaller face
		sortedCons = sortEntities(smallFaceCons, getConLength)
		oppositeCon = sortedCons[-1]
		smallFaceCons.remove(oppositeCon)
		
		# find all faces on clip
		cons = [oppositeCon]
		for i in range(8):
			clipFaces = set(ansa.base.GetFacesOfCons(cons))
			clipFaces.discard(self.smallFace)
			clipFaces.discard(self.largeFace)
			
			cons = base.CollectEntities(constants.ABAQUS, clipFaces, "CONS")
			#newFaces = clipFaces.difference(checkedfaces)
		#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = clipFaces)
		
		self.clipFaces = list(sortEntities(list(clipFaces), base.GetFaceArea))
		
		# create points for coordinate system
		self.middlePointCoords = getConMiddle(self.selectedCon)
		#self.topEdgeMiddleCoords = getConMiddle(oppositeCon)
		
		# guiding face normals
		self.smallFaceNormal = base.GetFaceOrientation(self.smallFace)
		self.largeFaceNormal = base.GetFaceOrientation(self.largeFace)
		
		self.sideProjectionVectorPlus = np.cross(self.smallFaceNormal, self.largeFaceNormal)
		self.sideProjectionVectorMinus = np.cross(self.largeFaceNormal, self.smallFaceNormal)
		self.oppositeProjectionVector = self.largeFaceNormal
		
		# find opposite point
		self.oppositeFace = self.largeFace
		self.largeFaceOrthoVector = np.cross(self.sideProjectionVectorPlus, self.largeFaceNormal)
		self.oppositeFacePointCoords = self.middlePointCoords +1*np.array(self.largeFaceOrthoVector)
		#self.oppositeFacePoint = base.Newpoint(*self.oppositeFacePointCoords)

		# front face point
		searchOnFaces = self.clipFaces[:]
		self.frontFaceProjectionVector = -1*np.array(self.largeFaceNormal)
		self.frontFace, self.frontFacePointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.oppositeFacePointCoords, self.frontFaceProjectionVector, searchedFaceName='z upper face - clip side',
			recSearch=[range(50), self.largeFaceOrthoVector])
		#self.frontFacePoint = base.Newpoint(*self.frontFacePointCoords)
		#raise SmartClipException('stop')
		
		# projection to the small face
		face, self.topPointCoords =  self._getPointProjectionCoords(
			[self.smallFace], self.frontFacePointCoords, -1*self.largeFaceOrthoVector)
		#self.topPoint = base.Newpoint(*self.topPointCoords)
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.median([self.oppositeFacePointCoords, self.frontFacePointCoords], axis=0)
		self.centerCoordNode = createNode(self.centerCoordPointCoords)
		#base.Newpoint(*self.centerCoordPointCoords)
		
		# find side faces
		sideBasePointCoords = self.oppositeFacePointCoords + 0.5*self.frontFaceProjectionVector
		# move a point lower
		sideBasePointCoords = sideBasePointCoords + 1*np.array(self.smallFaceNormal)
		
		sideBasePointCoords = sideBasePointCoords + 10*self.sideProjectionVectorMinus
		self.sideFacePlus, self.sidePlusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, sideBasePointCoords, self.sideProjectionVectorPlus, searchedFaceName='x upper face - clip side', minDist=False)
		self.sideFacePlusPoint = base.Newpoint(*self.sidePlusPointCoords)
		
		searchOnFaces.remove(self.sideFacePlus)
		
		sideBasePointCoords = sideBasePointCoords + 10*self.sideProjectionVectorPlus
		self.sideFaceMinus, self.sideMinusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, sideBasePointCoords, self.sideProjectionVectorMinus, searchedFaceName='x lower face - clip side', minDist=False)
		self.sideFaceMinusPoint = base.Newpoint(*self.sideMinusPointCoords)
		
		# this is correct orthogonal vector that a small face should have in case of 90 degrees...
		self.smallFaceOrthoVector = np.cross(self.largeFaceNormal, self.sideProjectionVectorMinus)

		# find front and opposite points not in the middle of the clip but on the one side		
# TODO: find really the nearest point on geometry !!	
		oppositeFrontBasePointCoords = self.sidePlusPointCoords + 1*self.sideProjectionVectorMinus
		#base.Newpoint(*oppositeFrontBasePointCoords)
		#raise SmartClipException('stop')
		
		searchOnFaces = self.clipFaces[:]
		frontFace, self.frontFacePointCoords = self._getPointProjectionCoords(
			searchOnFaces, oppositeFrontBasePointCoords, self.frontFaceProjectionVector, searchedFaceName='z upper face - clip side')
		self.frontFacePoint = base.Newpoint(*self.frontFacePointCoords)

		searchOnFaces = self.clipFaces[:]
		searchOnFaces.append(self.largeFace)
		oppositeFace, self.oppositeFacePointCoords = self._getPointProjectionCoords(
			searchOnFaces, oppositeFrontBasePointCoords, self.oppositeProjectionVector, searchedFaceName='z lower face - clip side')
		self.oppositeFacePoint = base.Newpoint(*self.oppositeFacePointCoords)
		
		#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = clipFaces)
		
		# fix normal direction for clip orientation
		self.largeFaceNormal = -1*np.array(self.largeFaceNormal)
		self.smallFaceOrthoVector = -1*self.smallFaceOrthoVector
		
	#-------------------------------------------------------------------------

	def findXlowDist(self):
		# find side plus projection mate
		self.sidePlusNeighbourFace, self.sidePlusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sidePlusPointCoords, self.sideProjectionVectorPlus, searchedFaceName='x lower face - clip contra side')
		self.sidePlusNeighbourFacePoint = base.Newpoint(*self.sidePlusNeighbourFacePointCoords)
		self.xLow = -1*self._getStopDistance(self.sideFacePlusPoint, self.sidePlusNeighbourFacePoint, 'xLow')
		
		self.stopDistanceFaceCouples['xLow'] = [self.sideFacePlus, self.sidePlusNeighbourFace]
		
	#-------------------------------------------------------------------------

	def findXupDist(self):
		# find side minus projection mate
		self.sideMinusNeighbourFace, self.sideMinusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sideMinusPointCoords, self.sideProjectionVectorMinus, searchedFaceName='x upper face - clip contra side')
		self.sideMinusNeighbourFacePoint = base.Newpoint(*self.sideMinusNeighbourFacePointCoords)
		self.xUp = self._getStopDistance(self.sideFaceMinusPoint, self.sideMinusNeighbourFacePoint, 'xUp')
		
		self.stopDistanceFaceCouples['xUp'] = [self.sideFaceMinus, self.sideMinusNeighbourFace]
		
	#-------------------------------------------------------------------------
    
	def createCoorSystem(self):
		
		self.thirdPointCoords = np.array(self.centerCoordPointCoords)+np.array(self.sideProjectionVectorPlus)
		
		zPointCoords = self.centerCoordPointCoords + self.largeFaceNormal
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  zPointCoords[0], 'B2':  zPointCoords[1], 'B3':  zPointCoords[2],
			'C1':  self.thirdPointCoords[0], 'C2':  self.thirdPointCoords[1], 'C3':  self.thirdPointCoords[2]}
		self.coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

	#-------------------------------------------------------------------------
	
	def createSymmetricalCoorSys(self):
		
		thirdPointCoords = np.array([1,-1,1])*np.array(self.centerCoordPointCoords) - np.array([1,-1,1])*np.array(self.sideProjectionVectorPlus)
		
		zPointCoords = self.centerCoordPointCoords + self.largeFaceNormal
		
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  -1*self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  zPointCoords[0], 'B2':  -1*zPointCoords[1], 'B3':  zPointCoords[2],
			'C1':  thirdPointCoords[0], 'C2':  thirdPointCoords[1], 'C3':  thirdPointCoords[2]}
				
		self.symmCoordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)

# ==============================================================================

class LockGeomType(ReversedGeomType):
	
	TYPE_NAME = 'Lock'
	INFO ='Lock-like geometrical clip type.'
	ICON = os.path.join(PATH_RES, 'icons', 'clip_geom_lock.png')

	#-------------------------------------------------------------------------
    
	def createCoorSystem(self):
		
		self.thirdPointCoords = np.array(self.centerCoordPointCoords)+np.array(self.sideProjectionVectorMinus)
		
		zPointCoords = self.centerCoordPointCoords - self.largeFaceNormal
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  zPointCoords[0], 'B2':  zPointCoords[1], 'B3':  zPointCoords[2],
			'C1':  self.thirdPointCoords[0], 'C2':  self.thirdPointCoords[1], 'C3':  self.thirdPointCoords[2]}
		self.coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)
		
		# fix normal direction for clip orientation
		self.largeFaceNormal = -1*np.array(self.largeFaceNormal)
	
	#-------------------------------------------------------------------------

	def redefineStopDistance(self, stopDistName):
		
		# reverse direction for xLow and xUp
		if stopDistName == 'xLow':
			super(LockGeomType, self).redefineStopDistance('xUp', 'xLow')
		elif stopDistName == 'xUp':
			super(LockGeomType, self).redefineStopDistance('xLow', 'xUp')
		else:
			super(LockGeomType, self).redefineStopDistance(stopDistName)
	
	#-------------------------------------------------------------------------
	
	def createSymmetricalCoorSys(self):
		
		thirdPointCoords = np.array([1,-1,1])*np.array(self.centerCoordPointCoords) + np.array([1,-1,1])*np.array(self.sideProjectionVectorPlus)
		
		zPointCoords = self.centerCoordPointCoords + self.largeFaceNormal
		
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  -1*self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  zPointCoords[0], 'B2':  -1*zPointCoords[1], 'B3':  zPointCoords[2],
			'C1':  thirdPointCoords[0], 'C2':  thirdPointCoords[1], 'C3':  thirdPointCoords[2]}
				
		self.symmCoordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)
	
# ==============================================================================

class AudiBeamType(metaclass=BeamTypeMetaClass):
	
	TYPE_NAME = 'AUDI'
	INFO ='AUDI CONNECTOR type clip consists of 1 connector element and beams joining connector with a clip and its contra side.'
	ICON = os.path.join(PATH_RES, 'icons', 'clip_beam_audi.png')
	
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
		
		self.clipEntities= self.parentClip.clipEntities
			
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
		#connectorNodeVector = self.middlePointCoords - self.centerCoordPointCoords
		#connectorNodeNorm = connectorNodeVector/ np.linalg.norm(connectorNodeVector)
		#connectorNodeCoords = self.centerCoordPointCoords+self.CONNECTOR_LENGTH*connectorNodeNorm
		
		connectorNodeCoords = self.centerCoordPointCoords+self.CONNECTOR_LENGTH*np.array(self.largeFaceNormal)
	
		#self.centerCoordNode = createNode(self.centerCoordPointCoords)
	
		self.connectingBeamsCenterNode1 = createNode(self.centerCoordPointCoords)
		self.connectingBeamsCenterNode2 = createNode(connectorNodeCoords)
		
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
		
		self.clipEntities.append(self.connector)
	
	#-------------------------------------------------------------------------
    
	def createBeams(self):
		
		hideAllFaces()
		
		self.createBeamsConnectorClipSide()
		self.createBeamsConnectorClipContraSide()
		
		self.parentClip._restoreF11drawingSettings()
	
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipContraSide(self):
		
		# find nodes for initial selection
		searchEntities = base.CollectEntities(constants.ABAQUS, None, "SHELL")
		
		# if no elements were selected before try to find the nearest ones
		if len(self.selectedElementsBeamCcs) == 0:
			# some points may not be defined because of non standart clip shape
			try:
				nearestElements = findNearestElements(
					self.frontNeighbourFacePointCoords + 0.2*np.array(self.largeFaceNormal), searchEntities)
			except Exception as e:
				nearestElements = list()
		else:
			# delete already created beams
			base.DeleteEntity(self.beamsCcs, force=True)
			nearestElements = self.selectedElementsBeamCcs
		
		print('Select nodes for beam definition: CONNECTOR - CLIP contra side.')
		selectedElements = base.PickEntities(constants.ABAQUS, "SHELL", initial_entities=nearestElements)
		
		if selectedElements is None:
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		self.beamNodesCcs = base.CollectEntities(constants.ABAQUS, selectedElements, "NODE")
		
		# create beams
#		print('Select nodes for beam definition: CONNECTOR - CLIP contra side.')
#		self.beamNodesCcs = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = self.connectingBeamsCenterNode2)
#		try:
#			self.beamNodesCcs.remove(self.connectingBeamsCenterNode2)
#		except:
#			self.beamNodesCcs = None
#			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		if len(self.beamNodesCcs) == 0:
			self.beamNodesCcs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		# save selected elements for further re-selection
		self.selectedElementsBeamCcs = selectedElements
		self.beamsCcsDefined = True
		
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
			vals = {'Name': 'BEAM',
				'PID': self.beamSectionCcs._id,
				'NODE1': self.connectingBeamsCenterNode2._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCcs.append(beam)
		
		self.clipEntities.extend(self.beamsCcs)
		
		base.RedrawAll()
			
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipSide(self):
		
		# find nodes for initial selection
		searchEntities = base.CollectEntities(constants.ABAQUS, None, "SHELL")
		
		# if no elements were selected before try to find the nearest ones
		if len(self.selectedElementsBeamCs) == 0:
			nearestElements = list()
			# some points may not be defined because of non standart clip shape
			try:
				for coords in [self.sidePlusPointCoords, self.centerCoordPointCoords, self.sideMinusPointCoords]:
					nearestElements.extend(findNearestElements(coords, searchEntities))
			except Exception as e:
				pass
		else:
			# delete already created beams
			base.DeleteEntity(self.beamsCs, force=True)
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
		self.beamSectionCs= base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
		
		self.beamsCs = list()
		for node in self.beamNodesCs:
			vals = {'Name': 'BEAM',
				'PID': self.beamSectionCs._id,
				'NODE1': self.connectingBeamsCenterNode1._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCs.append(beam)
		
		self.clipEntities.extend(self.beamsCs)
		
		base.RedrawAll()
		

# ==============================================================================

class SkodaBeamType(AudiBeamType):
	
	TYPE_NAME = 'SKODA'
	INFO = 'SKODA CONNECTOR type clip consists of 3 connectors joined together with steel beams of very low density and beams joining connector with a clip and its contra side.'
	ICON = os.path.join(PATH_RES, 'icons', 'clip_beam_skoda.png')
	
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
		
		self.clipEntities.extend([self.connectorC1, self.connectorC2, self.connectorC3])
		
		self.connectConnectorsWithBeams()
	
	#-------------------------------------------------------------------------
	
	def connectConnectorsWithBeams(self):
		
		def getBeamSection():
			beamSection = base.GetEntity(constants.ABAQUS, 'BEAM_SECTION', self.CONNECTING_BEAM_SECTION_ID)

			if beamSection is None:
								
				# create material for beam section
				vals = {
					'Name': 'CONNECTOR_BODY_STEEL_LIGHT',
					'DEFINED' : 'YES',
					'Elasticity' : 'ELASTIC',
					'Plasticity (Rate Indep.)' : 'PLASTIC', 
					'Plasticity (Rate Dep.)' : 'CREEP',
					 '*DENSITY' : 'YES',
					 'DENS' : 7.85E-12, 
					 '*EXPANSION' : 'YES', 'TYPE' : 'ISO',
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
			vals = {'Name': 'BEAM',
				'PID': self.connectingBeamsSection._id,
				'NODE1': self.connectingBeamsCenterNode1._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.connectingBeams.append(beam)
		for node in [self.con1Node2, self.con2Node2, self.con3Node2]:
			vals = {'Name': 'BEAM',
				'PID': self.connectingBeamsSection._id,
				'NODE1': self.connectingBeamsCenterNode2._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.connectingBeams.append(beam)
		
		self.clipEntities.extend(self.connectingBeams)

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
		
		entities = self.parentClip.clipEntities
		
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

def sortEntities(entities, sortFunction):
	
	values = [sortFunction(entity) for entity in entities]
	
	indexes = np.argsort(np.array(values))
	sortedEntities = np.array(entities)[indexes]
	
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

