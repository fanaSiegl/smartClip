# PYTHON script
import os
import numpy as np
import ansa
 
from ansa import base, constants, guitk


# ==============================================================================

class SmartClipException(Exception): pass

	
# ==============================================================================

class SmartClip(object):
	
	def __init__(self):
		
		self.selectedCon = None
		self.beamNodesCs = None
		self.beamNodesCcs = None
		
		self.stopDistanceMeasurements = list()
	
	#-------------------------------------------------------------------------
    
	def run(self):
		
		try:
			self.setBaseFaces()
			
			self.createNodesForConnector()
			
			self.setStopDistances()
			self.createCoorSystem()
			
			self.createConnector()
			self.createBeams()
		except SmartClipException as e:
			print(str(e))
	    
    #-------------------------------------------------------------------------
    
	def _getPointProjectionCoords(self, faces, pointCoords, vector, tolerance=50, searchedFaceName='face'):
		    	
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
			minDistanceIndex = np.argsort(distances)[0]
			return foundProjection[minDistanceIndex], foundCoordinates[minDistanceIndex]
		
		else:
		#if projectedPointCoords is None:
			showMessage("Projection to given faces not found within given tolerance of %s mm! Please select the %s manually." % (tolerance, searchedFaceName))
			face = set(base.PickEntities(constants.ABAQUS, "FACE"))
			projectedPointCoords =ansa.base.ProjectPointDirectional(
				face, pointCoords[0], pointCoords[1], pointCoords[2],
				vector[0], vector[1], vector[2], tolerance, project_on="faces")
		
		return face, projectedPointCoords

	#-------------------------------------------------------------------------
	
	def _getStopDistance(self, clipFacePoint, mateFacePoint, direction=1):

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
		
		self.stopDistanceMeasurements.append(mFace2face)
		
		return faceDist*direction
	
	#-------------------------------------------------------------------------
    
	def hideAllFaces(self):
		ent = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True )
		status = base.Not(ent, constants.ABAQUS)
		
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
		self.topEdgeMiddleCoords = getConMiddle(oppositeCon)
		
		# guiding face normals
		self.smallFaceNormal = base.GetFaceOrientation(self.smallFace)
		self.largeFaceNormal = base.GetFaceOrientation(self.largeFace)
		
		# find opposite projection
		#self.oppositeProjectionVector = self.middlePointCoords - self.topEdgeMiddleCoords
		#self.oppositeProjectionVector = np.cross(smallFaceNormal, largeFaceNormal)
		
		self.oppositeProjectionVector = -1*np.array(self.largeFaceNormal)
		self.oppositeFace, self.oppositeFacePointCoords = self._getPointProjectionCoords(
			clipFaces, self.middlePointCoords, self.oppositeProjectionVector, searchedFaceName='z lower face - clip side')
		self.oppositeFacePoint = base.Newpoint(*self.oppositeFacePointCoords)
		
		# front face point
		self.frontFacePointCoords = self.middlePointCoords + 1*np.array(self.smallFaceNormal)
		self.frontFacePoint = base.Newpoint(*self.frontFacePointCoords)
		
		self.clipFaces = list(sortEntities(list(clipFaces), base.GetFaceArea))
		self.oppositeFacePointCoords =  self.oppositeFacePointCoords
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.median([self.oppositeFacePointCoords, self.middlePointCoords], axis=0)
		#base.Newpoint(*self.centerCoordPointCoords)
		
		# find side faces		
		searchOnFaces = self.clipFaces[:]
		self.sideProjectionVectorPlus = np.cross(self.smallFaceNormal, self.oppositeProjectionVector)
		self.sideFacePlus, sidePlusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, self.sideProjectionVectorPlus, searchedFaceName='x upper face - clip side')
		# move a point lower
		self.sidePlusPointCoords = sidePlusPointCoords + 1*np.array(self.smallFaceNormal)
		self.sideFacePlusPoint = base.Newpoint(*self.sidePlusPointCoords)
		
		searchOnFaces.remove(self.sideFacePlus)
		self.sideProjectionVectorMinus = np.cross(self.oppositeProjectionVector, self.smallFaceNormal)
		self.sideFaceMinus, sideMinusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, self.sideProjectionVectorMinus, searchedFaceName='x lower face - clip side')
		# move a point lower
		self.sideMinusPointCoords = sideMinusPointCoords + 1*np.array(self.smallFaceNormal)
		self.sideFaceMinusPoint = base.Newpoint(*self.sideMinusPointCoords)
	
	#-------------------------------------------------------------------------
    
	def createNodesForConnector(self):
		
		self.thirdPointCoords = np.array(self.middlePointCoords)+np.array(self.sideProjectionVectorPlus)
				
		# create nodes for entities
		connectorNodeVector = self.middlePointCoords - self.centerCoordPointCoords
		connectorNodeNorm = connectorNodeVector/ np.linalg.norm(connectorNodeVector)
		connectorNodeCoords = self.centerCoordPointCoords+1*connectorNodeNorm
	
		self.connectorNode = base.CreateEntity(constants.ABAQUS, "NODE", 
			 {'X': connectorNodeCoords[0], 'Y': connectorNodeCoords[1], 'Z': connectorNodeCoords[2]})
		self.centerCoordNode = base.CreateEntity(constants.ABAQUS, "NODE", 
			 {'X': self.centerCoordPointCoords[0], 'Y': self.centerCoordPointCoords[1], 'Z': self.centerCoordPointCoords[2]})
	
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
		
		# find opposite projection mate
		self.oppositeNeighbourFace, self.oppositeNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.oppositeFacePointCoords, self.oppositeProjectionVector, searchedFaceName='z lower face - clip contra side')
		self.oppositeNeighbourFacePoint = base.Newpoint(*self.oppositeNeighbourFacePointCoords)
		self.zLow = 1+self._getStopDistance(self.oppositeFacePoint, self.oppositeNeighbourFacePoint, -1)
		
		# find front projection mate
		self.frontNeighbourFace, self.frontNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.frontFacePointCoords, self.largeFaceNormal, searchedFaceName='z upper face - clip contra side')
		self.frontNeighbourFacePoint = base.Newpoint(*self.frontNeighbourFacePointCoords)
		self.zUp = 1+self._getStopDistance(self.frontFacePoint, self.frontNeighbourFacePoint)
		
		# find side plus projection mate
		self.sidePlusNeighbourFace, self.sidePlusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sidePlusPointCoords, self.sideProjectionVectorPlus, searchedFaceName='x upper face - clip contra side')
		self.sidePlusNeighbourFacePoint = base.Newpoint(*self.sidePlusNeighbourFacePointCoords)
		self.xUp = self._getStopDistance(self.sideFacePlusPoint, self.sidePlusNeighbourFacePoint)
		
		# find side minus projection mate
		self.sideMinusNeighbourFace, self.sideMinusNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.sideMinusPointCoords, self.sideProjectionVectorMinus, searchedFaceName='x lower face - clip contra side')
		self.sideMinusNeighbourFacePoint = base.Newpoint(*self.sideMinusNeighbourFacePointCoords)
		self.xLow = self._getStopDistance(self.sideFaceMinusPoint, self.sideMinusNeighbourFacePoint, -1)
		
		# find top projection mate - created after the front gap distance is known - zUp
		#moveNormVector = np.array(self.largeFaceNormal)/ np.linalg.norm(np.array(self.largeFaceNormal))
		#self.topPointCoords = self.middlePointCoords + (self.zUp-1 + 0.1)*moveNormVector
		self.topPointCoords = self.middlePointCoords + (self.zUp-1 + 0.1)*np.array(self.largeFaceNormal)
		self.topPoint = base.Newpoint(*self.topPointCoords)
		
		self.topNeighbourFace, self.topNeighbourFacePointCoords = self._getPointProjectionCoords(
			self.neighbourFaces, self.topPointCoords, self.smallFaceNormal, searchedFaceName='y upper face - clip contra side')
		self.topNeighbourFacePoint = base.Newpoint(*self.topNeighbourFacePointCoords)
		self.yUp = self._getStopDistance(self.topPoint, self.topNeighbourFacePoint)
		
		self.yLow = -1000
		
		#print(xLow, xUp, yUp, yLow, zLow, zUp)
		status = base.And(ent, constants.ABAQUS)
		
		if hideMeasurements:
			self.hideMeasurements()
		
	#-------------------------------------------------------------------------
    
	def hideMeasurements(self):
		
		status = base.Not(self.stopDistanceMeasurements, constants.ABAQUS)
	
	#-------------------------------------------------------------------------
    
	def hidePoints(self):
		
		entities = [
			self.oppositeFacePoint,
			self.frontFacePoint,
			self.sideFacePlusPoint,
			self.sideFaceMinusPoint,
			
			
			self.oppositeNeighbourFacePoint,
			self.frontNeighbourFacePoint,
			self.sidePlusNeighbourFacePoint,
			self.sideMinusNeighbourFacePoint,
			self.topPoint,
			self.topNeighbourFacePoint,
			]
		
		status = base.Not(entities, constants.ABAQUS)
	
	#-------------------------------------------------------------------------
    
	def createCoorSystem(self):
		
		# create coordinate system
		vals = {'Name': 'CLIP_COOR_SYS',
			'A1':  self.centerCoordPointCoords[0], 'A2':  self.centerCoordPointCoords[1], 'A3':  self.centerCoordPointCoords[2],
			'B1':  self.middlePointCoords[0], 'B2':  self.middlePointCoords[1], 'B3':  self.middlePointCoords[2],
			'C1':  self.thirdPointCoords[0], 'C2':  self.thirdPointCoords[1], 'C3':  self.thirdPointCoords[2]}
		self.coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)
	
	#-------------------------------------------------------------------------
    
	def createConnector(self):
		
		# create connector elasticity
		vals = {'Name': 'CONNECTOR ELASTICITY',
			 'COMP': 'YES',
			 'COMP(1)': 'YES', 'El.Stiff.(1)': 50.0,
			 'COMP(2)': 'YES', 'El.Stiff.(2)': 50.0,
			 'COMP(3)': 'YES', 'El.Stiff.(3)': 50.0
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
			'G1':  self.centerCoordNode._id, 'G2': self.connectorNode._id}
		self.connector = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)
	
	#-------------------------------------------------------------------------
    
	def createBeams(self):
		
		self.hideAllFaces()
		
		self.createBeamsConnectorClipSide()
		self.createBeamsConnectorClipContraSide()
	
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipContraSide(self):
		
		# create beams
		print('Select nodes for beam definition: CONNECTOR - CLIP contra side.')
		self.beamNodesCcs = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = self.connectorNode)
		try:
			self.beamNodesCcs.remove(self.connectorNode)
		except:
			self.beamNodesCcs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		if len(self.beamNodesCcs) == 0:
			self.beamNodesCcs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP contra side!'))
		
		elements = base.NodesToElements(self.beamNodesCcs)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		self.beamPropCcs = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(element, 'PID'))
		material = base.GetEntity(constants.ABAQUS, 'MATERIAL', getEntityProperty(self.beamPropCcs, 'MID'))
		
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
				'NODE1': self.connectorNode._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCcs.append(beam)
			
	#-------------------------------------------------------------------------
    
	def createBeamsConnectorClipSide(self):
		
		# create beams
		print('Select nodes for beam definition: CONNECTOR - CLIP.')
		self.beamNodesCs = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = self.centerCoordNode)
		
		try:
			self.beamNodesCs.remove(self.centerCoordNode)
		except:
			self.beamNodesCs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP!'))

		if len(self.beamNodesCs) == 0:
			self.beamNodesCs = None
			raise(SmartClipException('No NODES selected for CONNECTOR - CLIP!'))
		
		elements = base.NodesToElements(self.beamNodesCs)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		self.beamPropCs = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(element, 'PID'))
		material = base.GetEntity(constants.ABAQUS, 'MATERIAL', getEntityProperty(self.beamPropCs, 'MID'))
		
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
				'NODE1': self.centerCoordNode._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			self.beamsCs.append(beam)
		

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

# ==============================================================================

#@ansa.session.defbutton('Mesh', 'SmartClip')
def runSmartClip():
	
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
	
	sc = SmartClip()
	sc.run()
	
# ==============================================================================

#if __name__ == '__main__':
#	
#	runSmartClip()


