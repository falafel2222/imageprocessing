from math import sqrt
from PIL import Image
import time
import random
import svgwrite

IMAGE_NAME = "wallpaper4"
THRESHOLD = 500				# minimum variace that can be split
WORKING_WIDTH = 1600			#width of the image while getting triangles
SCALE_FACTOR = 1			# how many times the image is blown up from its thumbnail size
MAX_VARIANCE = 99999999 	
MIN_SIDE_LENGTH = 1			#the minimum side length that can be split
MAX_WIDTH_TO_HEIGHT = 3.0	# maximum width to height ratio
SAVE_TYPE = "svg"			# the format in which the image will be saved

def average(pixels):
	"returns the average of a set of pixels"
	if not pixels:
		return (255,255,255)
	mean = [0,0,0]
	for i in range(len(mean)):
		for pixel in pixels:
			mean[i] += pixel[i]
		mean[i] /= len(pixels)
	return tuple(mean)

def variance(pixels):
	""" returns the variance of a set of pixels """
	if not pixels:
		return -1
	var = 0
	mean = average(pixels)
	for i in range(len(mean)):
		for pixel in pixels:
			var += (mean[i]-pixel[i])**2
	return var/len(pixels)


def dotProduct(v1,v2):
	return v1[0]*v2[0] + v1[1]*v2[1]


def inTriangle(P, A, B, C):
	""" returns true if point P is in triangle ABC 
		algorithm used from http://www.blackpawn.com/texts/pointinpoly/, all credit goes there"""
	AP = (P[0]-A[0],P[1]-A[1])	# create vectors from A to P, A to B, and A to C
	AB = (B[0]-A[0],B[1]-A[1])
	AC = (C[0]-A[0],C[1]-A[1])

	dotCC = dotProduct(AC,AC)	# compute dot products of those vectors
	dotCB = dotProduct(AC,AB)
	dotBB = dotProduct(AB,AB)
	dotCP = dotProduct(AC,AP)
	dotBP = dotProduct(AB,AP)
	if (dotBB * dotCC - dotCB * dotCB) == 0:
		return False
	invDenom = 1.0 / (dotBB * dotCC - dotCB * dotCB)	# math to find barymetric coordinates
	u = (dotBB * dotCP - dotCB * dotBP) * invDenom
	v = (dotCC * dotBP - dotCB * dotCP) * invDenom

	return u >= 0 and v >= 0 and u + v <= 1	# checks if P's barymetric coordinates are in the triangle

def pointsIn((point1,point2,point3),interval=1):
	"""takes in a tuple of 3 points represented by tuples
		returns a list of the points contained inside the triangle bounded by those points"""
	xList = [point1[0],point2[0],point3[0]]
	yList = [point1[1],point2[1],point3[1]]

	pointList = []
	for x in range(int(min(xList)),int(max(xList)+.99)):		
		for y in range(int(min(yList)),int(max(yList)+.99)):
			if inTriangle((x,y),point1,point2,point3):
				pointList.append((x,y))
	return pointList

def midpoint(point1, point2):
	return ((point2[0] + point1[0])/2.0,(point2[1]+point1[1])/2.0)

def distance(point1,point2):
	return sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)

def area(triangle):
	A,B,C = triangle
	return (A[0]*(B[1]-C[1]) + B[0]*(C[1]-A[1]) + C[0]*(A[1]-B[1]))/2.0

def height(tip, basePoints):
	A = tip
	B,C = basePoints

	return (A[0]*(B[1]-C[1]) + B[0]*(C[1]-A[1]) + C[0]*(A[1]-B[1]))/distance(B,C)


def split(pointPixelList,midpoint,tipPoint,referencePoint):
	half1 = []
	half2 = []
	line = (tipPoint[0]-midpoint[0],tipPoint[1] - midpoint[1])	# vector from midpoint to tipPoint

	for point,pixel in pointPixelList:
		v = (point[0]-midpoint[0],point[1] - midpoint[1])	# vector from midpoint to each point
		
		if line[0]*v[1]-line[1]*v[0] > 0:	# if the cross-product of line and v is positive
			half1.append((point,pixel))
		else:
			half2.append((point,pixel))
	#print len(half1),len(half2)
	
	v = (referencePoint[0]-midpoint[0],referencePoint[1] - midpoint[1])	# vector from midpoint to referencePoint
	
	if line[0]*v[1]-line[1]*v[0] > 0:	#make sure the half that has referencePoint is returned first
		return half1,half2
	else:
		return half2,half1


def getTriangles(image,triangle, pointPixelList):
	""" takes in an image and 3 points that represent a triangle
		and returns a list of smaller triangles that make up 
		the big triangle and their respective average colors"""
	
	pixelList = [pixel for p, pixel in pointPixelList]
	
	if variance(pixelList) < THRESHOLD:	# if the colors in the box are similar or the box is too small
		color = average(pixelList)
		return [(triangle,color)]	# return the triangle and the color it should be
	
	else:
		bestVariance = MAX_VARIANCE		# find the way to split the triangle with the least total variance
		triangle1 = None

		for point in triangle:

			otherpoints = [p for p in triangle if p != point]

			mid = midpoint(otherpoints[0],otherpoints[1])

			pointPixelList1,pointPixelList2 = split(pointPixelList, point, mid, otherpoints[0])

			pixelList1 = [pixel for p,pixel in pointPixelList1]
			pixelList2 = [pixel for p,pixel in pointPixelList2]

			variance1 = variance(pixelList1)
			variance2 = variance(pixelList2)
			
			if distance(otherpoints[0],otherpoints[1])**2/(2.0*MAX_WIDTH_TO_HEIGHT) > area(triangle) and pixelList1 and pixelList2:
				triangle1 = (mid,point,otherpoints[0])		# split the triangle this way if it's too wide for its height
				triangle2 = (mid,point,otherpoints[1])
				bestPPList1 = pointPixelList1
				bestPPList2 = pointPixelList2
				break

			if variance1 + variance2 <= bestVariance and pixelList1 and pixelList2:		# if the combined variances are the smallest, this is the best way to split it
				bestVariance = variance1 + variance2
				triangle1 = (mid,point,otherpoints[0])
				triangle2 = (mid,point,otherpoints[1])
				bestPPList1 = pointPixelList1
				bestPPList2 = pointPixelList2

		if triangle1:	# if there is a way to split it and the split won't recurse forever, then recurse
			return getTriangles(image,triangle1, bestPPList1) + getTriangles(image,triangle2,bestPPList2)
		else:
			return [(triangle,average(pixelList))]

		
def scale(point,factor):
	""" returns the point scaled by the factor """
	return (point[0]*factor,point[1]*factor)

def svgScale(point,factor):
	""" returns the point scaled by the factor """
	return (str(point[0]*factor)+"px",str(point[1]*factor) + "px")	

def rgb(color):
	return "rgb" + str(color)



def makeThumbnail(image):
	""" makes image into a thumbnail and returns 
		that thumbnail's width and height as a tuple """
	bbox = image.getbbox()
	width = bbox[2]-bbox[0]
	height = bbox[3]-bbox[1]

	workingHeight = height * WORKING_WIDTH / width
	size = (WORKING_WIDTH,workingHeight)
	image.thumbnail(size)
	return size

def nameGenerator():
	firstWordList = ["Starry", "Pubescent","Electric","Derelict","Infused","Culture","Vibrating","Dormant","Portland","Seductive","Bourgeoise","Phallic"]
	secondWordList = ["Plight","Hue","Transcendence","Carousel","Conversation","Privilege","Fallacy","Opression","Abortion","Jihad","Exploration","Episode"]
	number = random.randint(134,768)
	return random.choice(firstWordList) + " " + random.choice(secondWordList) + " No. " + str(number)



def main():
	image =  Image.open("img/" + IMAGE_NAME + ".jpg")
	workingSize = makeThumbnail(image)
	print "Image loaded"
	
	points = []
	for x in range(workingSize[0]):
		for y in range(workingSize[1]):
			points.append((x,y))
	
	startTime = time.time()
	
	leftX,topY,rightX,bottomY =  image.getbbox()

	
	topLeft = (leftX,topY)		# find the starting triangle coordinates
	topRight = (rightX,topY)
	bottomLeft = (leftX, bottomY)
	bottomRight = (rightX, bottomY)

	pointPixelList = [(p, image.getpixel(p)) for p in points]

	PPL1,PPL2 = split(pointPixelList,(0,0),workingSize,topRight)
	triangleList = []		#gets a list of all the triangles and their respective colors
	
	print "Getting triangles, part 1"
	triangleList += getTriangles(image, (bottomRight,topLeft, topRight),PPL1)
	print "halfway done getting triangles in,", round(time.time() - startTime,1), "seconds" 

	print "Getting triangles, part 2"
	triangleList += getTriangles(image, (topLeft, bottomRight, bottomLeft),PPL2)

	print "triangles found in,", round(time.time() - startTime,1), "seconds" 

	startTime = time.time()

	if SAVE_TYPE == "svg":
		print "Creating Image"
		svgFile = svgwrite.Drawing(filename = "triangled/" + IMAGE_NAME + ".svg",
                                size = svgScale(workingSize,SCALE_FACTOR))
		for triangle,color in triangleList:
			triangle = [scale(point,SCALE_FACTOR) for point in triangle]
			svgFile.add(svgFile.polygon(points = triangle,
										stroke = rgb(color),
            	                       fill = rgb(color)))
		svgFile.save()
		
		print "Image created in", round(time.time() - startTime,1), "seconds"
	
	elif SAVE_TYPE == "jpg":
		print "Placing pixels"

		image = Image.new('RGB',scale(workingSize,SCALE_FACTOR))	# Makes a new, higher quality image out of the list of triangles
		#imageNumber = 0
		for triangle,color in triangleList:
			triangle = tuple([scale(point,SCALE_FACTOR) for point in triangle])
			for point in pointsIn(triangle):
				image.putpixel(point,color)
			#if imageNumber % 20 == 0:
			#	image.save("sunsetProcess/"+ str(imageNumber) + ".jpg")
			#imageNumber += 1
		
		print "Pixels Placed in", round(time.time() - startTime,1), "seconds"
	
		image.save("triangled/" + IMAGE_NAME + ".jpg")

if __name__ == "__main__":
	main()