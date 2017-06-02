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
		
		try:
			self.setBaseFaces()
			
			return
			self.createNodesForConnector()
			self.setStopDistances()
			self.createCoorSystem()
			self.createConnector()
			self.createBeams()
		except SmartClipException as e:
			print(str(e))
	    
    #-------------------------------------------------------------------------
    
	def _getPointProjectionCoords(self, faces, pointCoords, vector, tolerance=50):
    	
    	# check for point projection on opposite face
		for face in faces:
			projectedPointCoords =ansa.base.ProjectPointDirectional(
				face, pointCoords[0], pointCoords[1], pointCoords[2],
				vector[0], vector[1], vector[2], tolerance, project_on="faces")
			if projectedPointCoords is not None:
				return face, projectedPointCoords
		
		if projectedPointCoords is None:
			showMessage("Clip button face not found! Please select the face manually.")
			face = set(base.PickEntities(constants.ABAQUS, "FACE"))
			projectedPointCoords =ansa.base.ProjectPointDirectional(
				face, pointCoords[0], pointCoords[1], pointCoords[2],
				vector[0], vector[1], vector[2], tolerance, project_on="faces")
		
		return face, projectedPointCoords

	#-------------------------------------------------------------------------
    
	def setBaseFaces(self):
		
		# selecting base CON defining the clip position
		selectedCons = base.PickEntities(constants.ABAQUS, "CONS")
		
		if selectedCons is None:
			raise(SmartClipException('No guiding CON selected!'))
			
			
		self.selectedCon = selectedCons[0]
		neighbourFaces = ansa.base.GetFacesOfCons(cons = selectedCons)
		
		sortedFaces = sortEntities(neighbourFaces, base.GetFaceArea)
		self.smallFace = sortedFaces[0]
		self.largeFace = sortedFaces[1]
		
		smallFaceCons = base.CollectEntities(constants.ABAQUS, self.smallFace, "CONS")
		smallFaceCons.remove(self.selectedCon)
		largeFaceCons = base.CollectEntities(constants.ABAQUS, self.largeFace, "CONS")
		largeFaceCons.remove(self.selectedCon)
		
		
		# find opposite con to selected one belonging to the smaller face
		sortedCons = sortEntities(smallFaceCons, getConLength)
		oppositeCon = sortedCons[-1]
		smallFaceCons.remove(oppositeCon)
		
		# create points for coordinate system
		self.middlePointCoords = getConMiddle(self.selectedCon)
		self.topEdgeMiddleCoords = getConMiddle(oppositeCon)
		oppositeProjectionVector = self.middlePointCoords - self.topEdgeMiddleCoords
		'''
		cons = [oppositeCon]
		
		#base.PickEntities(constants.ABAQUS, "CONS",  initial_entities = cons)
		oppositeFacePointCoords = None
		checkedfaces = set()
		counter = 0
		while oppositeFacePointCoords is None:
			clipFaces = set(ansa.base.GetFacesOfCons(cons))
			clipFaces.discard(self.smallFace)
			clipFaces.discard(self.largeFace)
			
			#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = clipFaces)
			
			cons = base.CollectEntities(constants.ABAQUS, clipFaces, "CONS")
			
			newFaces = clipFaces.difference(checkedfaces)
			
			# check maximum number of iterations
			if counter > 10:
				showMessage("Clip button face not found! Please select the face manually.")
				newFaces = set(base.PickEntities(constants.ABAQUS, "FACE"))
			
			# check for point projection on opposite face
			for newFace in newFaces:
				
				oppositeFacePointCoords =ansa.base.ProjectPointDirectional(
					newFace, self.middlePointCoords[0], self.middlePointCoords[1], self.middlePointCoords[2],
					oppositeProjectionVector[0], oppositeProjectionVector[1], oppositeProjectionVector[2], 10, project_on="faces")

				
				if oppositeFacePointCoords is not None:
					self.oppositeFace = newFace
					break
				checkedfaces.add(newFace)

			counter += 1
		'''
		cons = [oppositeCon]
		for i in range(8):
			clipFaces = set(ansa.base.GetFacesOfCons(cons))
			clipFaces.discard(self.smallFace)
			clipFaces.discard(self.largeFace)
			
			cons = base.CollectEntities(constants.ABAQUS, clipFaces, "CONS")
			#newFaces = clipFaces.difference(checkedfaces)
		#base.PickEntities(constants.ABAQUS, "FACE",  initial_entities = clipFaces)
		

		self.oppositeFace, self.oppositeFacePointCoords = self._getPointProjectionCoords(
			clipFaces, self.middlePointCoords, oppositeProjectionVector)
		
		
		
		#print(oppositeFacePointCoords, self.oppositeFace)
		base.Newpoint(*self.oppositeFacePointCoords)
		base.Newpoint(*self.topEdgeMiddleCoords)
		
		self.clipFaces = list(sortEntities(list(clipFaces), base.GetFaceArea))
		self.oppositeFacePointCoords =  self.oppositeFacePointCoords
		
		# find coordinates for coordinate system
		self.centerCoordPointCoords = np.median([self.oppositeFacePointCoords, self.middlePointCoords], axis=0)
		
		# find side faces
		smallFaceNormal = base.GetFaceOrientation(self.smallFace)
		
		searchOnFaces = self.clipFaces
		sideProjectionVectorPlus = np.cross(smallFaceNormal, oppositeProjectionVector)
		sideFacePlus, sidePlusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, sideProjectionVectorPlus)
		base.Newpoint(*sidePlusPointCoords)
		print(sideFacePlus, sidePlusPointCoords)
		
		searchOnFaces.remove(sideFacePlus)
		sideProjectionVectorMinus = np.cross(oppositeProjectionVector, smallFaceNormal)
		sideFaceMinus, sideMinusPointCoords = self._getPointProjectionCoords(
			searchOnFaces, self.centerCoordPointCoords, sideProjectionVectorMinus)
		base.Newpoint(*sideMinusPointCoords)
		print(sideFaceMinus, sideMinusPointCoords)
		
		
		
		
		
		
		
		return
		# get clip side faces
		neighbourFacesSmallFace = ansa.base.GetFacesOfCons(cons = smallFaceCons)
		neighbourFacesSmallFace.remove(self.smallFace)
		neighbourFacesLargeFace = ansa.base.GetFacesOfCons(cons = largeFaceCons)
		neighbourFacesLargeFace.remove(self.largeFace)
	
		self.sideFaces = list(set(neighbourFacesSmallFace).intersection(neighbourFacesLargeFace))
		
		#get top face
		topFace =  base.GetFacesOfCons(cons = oppositeCon)
		topFace.remove(self.smallFace)
		self.topFace = topFace[0]
		
		#get opposite face
		largeFaceOrientation = base.GetFaceOrientation(self.largeFace)
		exclude = neighbourFacesSmallFace[:]
		exclude.extend(neighbourFacesLargeFace)
		exclude.append(self.smallFace)
		exclude.append(self.largeFace)
	
	#-------------------------------------------------------------------------
    
	def createNodesForConnector(self):
		
		
		
		fstHPcoords, scndHPcoords = getConsHotPointCoords(self.selectedCon)
		self.thirdPointCoords = np.median([scndHPcoords, self.middlePointCoords], axis=0)
		
		# create nodes for entities
		connectorNodeVector = self.middlePointCoords - self.centerCoordPointCoords
		connectorNodeNorm = connectorNodeVector/ np.linalg.norm(connectorNodeVector)
		connectorNodeCoords = self.centerCoordPointCoords+1*connectorNodeNorm
	
		self.connectorNode = base.CreateEntity(constants.ABAQUS, "NODE", 
			 {'X': connectorNodeCoords[0], 'Y': connectorNodeCoords[1], 'Z': connectorNodeCoords[2]})
		self.centerCoordNode = base.CreateEntity(constants.ABAQUS, "NODE", 
			 {'X': self.centerCoordPointCoords[0], 'Y': self.centerCoordPointCoords[1], 'Z': self.centerCoordPointCoords[2]})
	
	#-------------------------------------------------------------------------
    
	def setStopDistances(self):
		
		# searching for distances
		# show only relevant entities
		prop = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(self.largeFace, 'PID'))
		base.Or(self.largeFace, constants.ABAQUS)
		base.Near(radius=10., dense_search=True, custom_entities=self.largeFace)
		# hide property
		ent = base.CollectEntities(constants.ABAQUS, [prop], "FACE", filter_visible=True )
		status = base.Not(ent, constants.ABAQUS)
		
		
		smallFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = self.smallFace)
		smallFaceMate.remove(self.smallFace)
		self.yUp = getStopDistance(self.smallFace, smallFaceMate[0], self.centerCoordNode)
		
		largeFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = self.largeFace)
		largeFaceMate.remove(self.largeFace)
		self.zUp = 1+getStopDistance(self.largeFace, largeFaceMate[0], self.centerCoordNode)
		
		oppositeFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = self.oppositeFace)
		oppositeFaceMate.remove(self.oppositeFace)
		self.zLow = 1+getStopDistance(self.oppositeFace, oppositeFaceMate[0], self.centerCoordNode, -1)
		
		sideFaces1Mate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = self.sideFaces[0])
		sideFaces1Mate.remove(self.sideFaces[0])
		self.xLow = getStopDistance(self.sideFaces[0], sideFaces1Mate[0], self.centerCoordNode, -1)
		
		sideFaces2Mate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = self.sideFaces[1])
		sideFaces2Mate.remove(self.sideFaces[1])
		self.xUp = getStopDistance(self.sideFaces[1], sideFaces2Mate[0], self.centerCoordNode)
		
		self.yLow = -1000
		
		#print(xLow, xUp, yUp, yLow, zLow, zUp)
		status = base.And(ent, constants.ABAQUS)
		
		ent = base.CollectEntities(constants.ABAQUS, None, "MEASUREMENT")#, filter_visible=True)
		status = base.Not(ent, constants.ABAQUS)
	
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
		
		# hide geometry
		ent = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True )
		status = base.Not(ent, constants.ABAQUS)
		
		# create beams
		beamNodes = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = self.connectorNode)
		beamNodes.remove(self.connectorNode)
		
		elements = base.NodesToElements(beamNodes)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		prop = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(element, 'PID'))
		material = base.GetEntity(constants.ABAQUS, 'MATERIAL', getEntityProperty(prop, 'MID'))
		
		# create beam section
		vals = {'Name': 'BEAM_SECTION',
			'TYPE_':'SECTION', 'MID': getEntityProperty(prop, 'MID'),
			'SECTION': 'CIRC', 'TYPE':'B31', 'optional2':'H',
			'RADIUS' : 5, 
			'C1' : 0, 'C2' : 1, 'C3' : -1,
			#'DENSITY' : getEntityProperty(material, 'DENS'),  'POISSON' : getEntityProperty(material, 'POISSON'),
			#'E' : getEntityProperty(material, 'YOUNG'),
			#'G' :  getEntityProperty(material, 'YOUNG')/(2*(1+getEntityProperty(material, 'POISSON')))
				}
		self.beamSection = base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
		
		for node in beamNodes:
			vals = {'Name': 'BEAM',
				'PID': self.beamSection._id,
				'NODE1': self.connectorNode._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
			
	
	
	
		
		beamNodes = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = self.centerCoordNode)
		beamNodes.remove(self.centerCoordNode)
		
		elements = base.NodesToElements(beamNodes)
	#TODO: check if all nodes belong to the one property!!
		allElements = list()
		for elements in list(elements.values()):
			allElements.extend(elements)
		element = sortEntities(allElements, allElements.count)[-1]
		
		# beam properties
		prop = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(element, 'PID'))
		material = base.GetEntity(constants.ABAQUS, 'MATERIAL', getEntityProperty(prop, 'MID'))
		
		# create beam section
		vals = {'Name': 'BEAM_SECTION',
			'TYPE_':'SECTION', 'MID': getEntityProperty(prop, 'MID'),
			'SECTION': 'CIRC', 'TYPE':'B31', 'optional2':'H',
			'RADIUS' : 5, 
			'C1' : 0, 'C2' : 1, 'C3' : -1,
			#'DENSITY' : getEntityProperty(material, 'DENS'),  'POISSON' : getEntityProperty(material, 'POISSON'),
			#'E' : getEntityProperty(material, 'YOUNG'),
			#'G' :  getEntityProperty(material, 'YOUNG')/(2*(1+getEntityProperty(material, 'POISSON')))
				}
		beamSection = base.CreateEntity(constants.ABAQUS, "BEAM_SECTION", vals)
		
		for node in beamNodes:
			vals = {'Name': 'BEAM',
				'PID': beamSection._id,
				'NODE1': self.centerCoordNode._id,
				'NODE2': node._id,
				'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
			beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
		
		
		#base.PickEntities(constants.ABAQUS, "CONS", initial_entities = smallFaceCons)#[selectedCon, opositeCon])
		#base.PickEntities(constants.ABAQUS, "CONS", initial_entities = largeFaceCons)
		
		#ansa.calc.ProjectPointToCons(x_y_z, cons)
		#ansa.calc.ProjectPointToContainer(coords, entities)
		#ansa.base.Newpoint(x, y, z)
		#ansa.base.Neighb(number_of_steps)
		#mat = base.GetFaceOrientation(face)
		#status = base.Or(deck=constants.ABAQUS, keyword = "MAT1", id = 23)
		#nsa.base.DeleteEntity(entities, force)

# ==============================================================================

def showMessage(message):
	w = guitk.BCWindowCreate('Missing entity', guitk.constants.BCOnExitDestroy)
	f = guitk.BCFrameCreate(w)
	l = guitk.BCBoxLayoutCreate(f, guitk.constants.BCHorizontal)
	label =guitk.BCLabelCreate(l, message)
	guitk.BCDialogButtonBoxCreate(w)
	guitk.BCShow(w)

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

@ansa.session.defbutton('Mesh', 'SmartClip')
def smartClip():
	
	smartClip = SmartClip()
	
# ==============================================================================

if __name__ == '__main__':
	smartClip()

