# PYTHON script
import os
import numpy as np
import ansa
from ansa import base, constants

# ==============================================================================

def main():
	
	print('Starting...')
	#selectedFaces = base.PickEntities(constants.ABAQUS, "FACE")
	selectedCons = base.PickEntities(constants.ABAQUS, "CONS")
	selectedCon = selectedCons[0]
	print(selectedCon)
	neighbourFaces = ansa.base.GetFacesOfCons(cons = selectedCons)
	
	sortedFaces = sortEntities(neighbourFaces, base.GetFaceArea)
#TODO: check if there are two faces
	smallFace = sortedFaces[0]
	largeFace = sortedFaces[1]
	#print(sortedFaces)
	smallFaceCons = base.CollectEntities(constants.ABAQUS, smallFace, "CONS")
	smallFaceCons.remove(selectedCon)
	largeFaceCons = base.CollectEntities(constants.ABAQUS, largeFace, "CONS")
	largeFaceCons.remove(selectedCon)
	
	
	# find opposite con to selected one belonging to the smaller face
	sortedCons = sortEntities(smallFaceCons, getConLength)
	oppositeCon = sortedCons[-1]
	smallFaceCons.remove(oppositeCon)
	#print(sortedCons)
	#print(oppositeCon)
	
	# get clip side faces
	neighbourFacesSmallFace = ansa.base.GetFacesOfCons(cons = smallFaceCons)
	neighbourFacesSmallFace.remove(smallFace)
	neighbourFacesLargeFace = ansa.base.GetFacesOfCons(cons = largeFaceCons)
	neighbourFacesLargeFace.remove(largeFace)

	sideFaces = list(set(neighbourFacesSmallFace).intersection(neighbourFacesLargeFace))
	
	#get top face
	topFace =  ansa.base.GetFacesOfCons(cons = oppositeCon)
	topFace.remove(smallFace)
	topFace = topFace[0]
	
	#get opposite face
	largeFaceOrientation = base.GetFaceOrientation(largeFace)
	exclude = neighbourFacesSmallFace[:]
	exclude.extend(neighbourFacesLargeFace)
	exclude.append(smallFace)
	exclude.append(largeFace)
	
	# create points for coordinate system
	middlePointCoords = getConMiddle(selectedCon)
#	middlePoint = base.Newpoint(*middlePointCoords)

	topEdgeMiddleCoords = getConMiddle(oppositeCon)
	projectionVector = middlePointCoords - topEdgeMiddleCoords
	
	topNeighbourFaces = list()
	angleErrors = dict()
	for i in range(10):
		topFaces = getFaceNeighbourFaces(topFace, exclude)
		sortedTopFaces = sortEntities(topFaces, base.GetFaceArea)
		
		if len(sortedTopFaces) == 0:
			continue
		
		largesFace = sortedTopFaces[-1]
		
		#base.PickEntities(constants.ABAQUS, "FACE", initial_entities = largesFace)
		
#		# check too large face
#		index = -2
#		while base.GetFaceArea(largesFace) > 5* base.GetFaceArea(largeFace):
#			largesFace = sortedTopFaces[index]
#			index -= 1
		
		orientation = base.GetFaceOrientation(largesFace)
		
		cosang = np.dot(largeFaceOrientation, orientation)
		sinang = np.linalg.norm(np.cross(largeFaceOrientation, orientation))
		angle = np.arctan2(sinang, cosang)
		
		angleError = angle*180/np.pi - 180
		# set angle error
		angleErrors[largesFace] = np.abs(angleError)
		topNeighbourFaces.append(largesFace)
		
		#base.PickEntities(constants.ABAQUS, "FACE", initial_entities = largesFace)
		
		topFace = largesFace
		
		#m =ansa.base.ProjectPointDirectional(
		#	topFace, middlePointCoords[0], middlePointCoords[1], middlePointCoords[2],
		#	projectionVector[0], projectionVector[1], projectionVector[2], 10, project_on="faces")
	
		#print(m, topFace)
	
	topFaces = sortEntities(topNeighbourFaces[2:], lambda face: angleErrors[face])
	oppositeFace = topFaces[0]
	
	#base.PickEntities(constants.ABAQUS, "FACE", initial_entities = topFaces)
	#base.PickEntities(constants.ABAQUS, "FACE", initial_entities = oppositeFace)
	
	#print(oppositeFace)

	
	
#TODO: check if there is a better function for point projection!!!
# E.G. this one???:
#ansa.base.ProjectPointDirectional(target, point_x, point_y, point_z, vec_x, vec_y, vec_z, tolerance, project_on)
	mat = ansa.calc.ProjectPointToContainer(middlePointCoords, oppositeFace)
	#print(mat[0][0], mat[0][1], mat[0][2])
	oppositeFacePointCoords = [mat[0][0], mat[0][1], mat[0][2]]
#	newPoint = base.Newpoint(*oppositeFacePointCoords)
	#print(oppositeFacePointCoords)
	#return
	centerCoordPointCoords = np.median([oppositeFacePointCoords, middlePointCoords], axis=0)
#	centerCoordPoint = base.Newpoint(*centerCoordPointCoords)
	
	fstHPcoords, scndHPcoords = getConsHotPointCoords(selectedCon)
	#print(fstHPcoords, scndHPcoords)
	thirdPointCoords = np.median([scndHPcoords, middlePointCoords], axis=0)
#	newPoint = base.Newpoint(*thirdPointCoords)
	
	# create nodes for entities
	connectorNodeVector = middlePointCoords - centerCoordPointCoords
	connectorNodeNorm = connectorNodeVector/ np.linalg.norm(connectorNodeVector)
	connectorNodeCoords = centerCoordPointCoords+1*connectorNodeNorm
#	base.Newpoint(*connectorNodeCoords)

	connectorNode = base.CreateEntity(constants.ABAQUS, "NODE", 
		 {'X': connectorNodeCoords[0], 'Y': connectorNodeCoords[1], 'Z': connectorNodeCoords[2]})
	centerCoordNode = base.CreateEntity(constants.ABAQUS, "NODE", 
		 {'X': centerCoordPointCoords[0], 'Y': centerCoordPointCoords[1], 'Z': centerCoordPointCoords[2]})


	# searching for distances
	# show only relevant entities
	prop = base.GetEntity(constants.NASTRAN, 'PSHELL', getEntityProperty(largeFace, 'PID'))
	base.Or(largeFace, constants.ABAQUS)
	base.Near(radius=10., dense_search=True, custom_entities=largeFace)
	# hide property
	ent = base.CollectEntities(constants.ABAQUS, [prop], "FACE", filter_visible=True )
	status = base.Not(ent, constants.ABAQUS)
	
	
	
	
	smallFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = smallFace)
	smallFaceMate.remove(smallFace)
	yUp = getStopDistance(smallFace, smallFaceMate[0], centerCoordNode)
	
	largeFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = largeFace)
	largeFaceMate.remove(largeFace)
	zUp = 1+getStopDistance(largeFace, largeFaceMate[0], centerCoordNode)
	
	oppositeFaceMate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = oppositeFace)
	oppositeFaceMate.remove(oppositeFace)
	zLow = 1+getStopDistance(oppositeFace, oppositeFaceMate[0], centerCoordNode, -1)
	
	sideFaces1Mate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = sideFaces[0])
	sideFaces1Mate.remove(sideFaces[0])
	xLow = getStopDistance(sideFaces[0], sideFaces1Mate[0], centerCoordNode, -1)
	
	sideFaces2Mate = base.PickEntities(constants.ABAQUS, "FACE", initial_entities = sideFaces[1])
	sideFaces2Mate.remove(sideFaces[1])
	xUp = getStopDistance(sideFaces[1], sideFaces2Mate[0], centerCoordNode)
	
	yLow = -1000
	
	#print(xLow, xUp, yUp, yLow, zLow, zUp)
	status = base.And(ent, constants.ABAQUS)
	
	ent = base.CollectEntities(constants.ABAQUS, None, "MEASUREMENT", filter_visible=True )
	status = base.Not(ent, constants.ABAQUS)

	# create coordinate system
	vals = {'Name': 'CLIP_COOR_SYS',
		'A1':  centerCoordPointCoords[0], 'A2':  centerCoordPointCoords[1], 'A3':  centerCoordPointCoords[2],
		'B1':  middlePointCoords[0], 'B2':  middlePointCoords[1], 'B3':  middlePointCoords[2],
		'C1':  thirdPointCoords[0], 'C2':  thirdPointCoords[1], 'C3':  thirdPointCoords[2]}
	coordSystem = base.CreateEntity(constants.ABAQUS, "ORIENTATION_R", vals)
	
	# create connector elasticity
	vals = {'Name': 'CONNECTOR ELASTICITY',
		 'COMP': 'YES',
		 'COMP(1)': 'YES', 'El.Stiff.(1)': 50.0,
		 'COMP(2)': 'YES', 'El.Stiff.(2)': 50.0,
		 'COMP(3)': 'YES', 'El.Stiff.(3)': 50.0
		}
	connectorElasticity = base.CreateEntity(constants.ABAQUS, "CONNECTOR_ELASTICITY", vals)

	# create connector stop
	vals = {'Name': 'CONNECTOR STOP',
		 'COMP (1)': 'YES', 'Low.Lim.(1)': xLow, 'Up.Lim.(1)': xUp, 
		 'COMP (2)': 'YES', 'Low.Lim.(2)': yLow, 'Up.Lim.(2)': yUp, 
		 'COMP (3)': 'YES', 'Low.Lim.(3)': zLow, 'Up.Lim.(3)': zUp, 
		}
	connectorStop = base.CreateEntity(constants.ABAQUS, "CONNECTOR_STOP", vals)
	

	# create connector behavior
	vals = {'Name': 'CONNECTOR BEHAVIOR',
		'*ELASTICITY': 'YES', 'EL>data': connectorElasticity._id,
		'*STOP':'YES', 'STP>data': connectorStop._id,
		}
	connectorBehavior = base.CreateEntity(constants.ABAQUS, "CONNECTOR BEHAVIOR", vals)
	
	# create a connector section
	vals = {'Name': 'CONNECTOR_SECTION',
		 'MID': connectorBehavior._id,
		'COMPONENT_1': 'CARDAN', 'COMPONENT_2':  'CARTESIAN', 'ORIENT_1': coordSystem._id,
		}
	connectorSection = base.CreateEntity(constants.ABAQUS, "CONNECTOR_SECTION", vals)
	
	# create a connector
	vals = {'Name': 'CONNECTOR',
		'PID':connectorSection._id,
		'G1':  centerCoordNode._id, 'G2': connectorNode._id}
	connector = base.CreateEntity(constants.ABAQUS, "CONNECTOR", vals)


	# hide geometry
	ent = base.CollectEntities(constants.ABAQUS, None, "FACE", filter_visible=True )
	status = base.Not(ent, constants.ABAQUS)
	
	# create beams
	beamNodes = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = connectorNode)
	beamNodes.remove(connectorNode)
	
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
			'NODE1': connectorNode._id,
			'NODE2': node._id,
			'Orient': 'With Vector', 'C1' : 0, 'C2' : 1, 'C3' : -1,}
		beam = base.CreateEntity(constants.ABAQUS, "BEAM", vals)
		



	
	beamNodes = base.PickEntities(constants.ABAQUS, "NODE", initial_entities = centerCoordNode)
	beamNodes.remove(centerCoordNode)
	
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
			'NODE1': centerCoordNode._id,
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
if __name__ == '__main__':
	main()

