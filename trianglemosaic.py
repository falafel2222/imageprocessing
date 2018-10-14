from math import sqrt
from PIL import Image
import time
import random
import svgwrite

MAX_WIDTH_TO_HEIGHT = 2   # maximum width to height ratio

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
        algorithm used from http://www.blackpawn.com/texts/pointinpoly/,
        all credit goes there"""

    # create vectors from A to P, A to B, and A to C
    AP = (P[0]-A[0], P[1]-A[1])
    AB = (B[0]-A[0], B[1]-A[1])
    AC = (C[0]-A[0], C[1]-A[1])

    # compute dot products of those vectors
    dotCC = dotProduct(AC, AC)
    dotCB = dotProduct(AC, AB)
    dotBB = dotProduct(AB, AB)
    dotCP = dotProduct(AC, AP)
    dotBP = dotProduct(AB, AP)
    if (dotBB * dotCC - dotCB * dotCB) == 0:
        return False
    # math to find barymetric coordinates
    invDenom = 1.0 / (dotBB * dotCC - dotCB * dotCB)
    u = (dotBB * dotCP - dotCB * dotBP) * invDenom
    v = (dotCC * dotBP - dotCB * dotCP) * invDenom

    # checks if P's barymetric coordinates are in the triangle
    return u >= 0 and v >= 0 and u + v <= 1


def pointsIn(points):
    """takes in a tuple of 3 points represented by tuples
        returns a list of the points contained inside the triangle
        bounded by those points"""

    xList = [points[0][0], points[1][0], points[2][0]]
    yList = [points[0][1], points[1][1], points[2][1]]

    pointList = []
    for x in range(int(min(xList)), int(max(xList)+.99)):
        for y in range(int(min(yList)),int(max(yList)+.99)):
            if inTriangle((x,y),points[0],points[1],points[2]):
                pointList.append((x,y))
    return pointList


def midpoint(point1, point2):
    return ((point2[0] + point1[0])/2.0,(point2[1]+point1[1])/2.0)


def distance(point1,point2):
    return sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)


def split(pointPixelList,midpoint,tipPoint,referencePoint):
    half1 = []
    half2 = []
    line = (tipPoint[0]-midpoint[0],tipPoint[1] - midpoint[1])  # vector from midpoint to tipPoint

    for point,pixel in pointPixelList:
        v = (point[0]-midpoint[0],point[1] - midpoint[1])   # vector from midpoint to each point
        
        if line[0]*v[1]-line[1]*v[0] > 0:   # if the cross-product of line and v is positive
            half1.append((point,pixel))
        else:
            half2.append((point,pixel))
    #print len(half1),len(half2)
    
    v = (referencePoint[0]-midpoint[0],referencePoint[1] - midpoint[1]) # vector from midpoint to referencePoint
    
    if line[0]*v[1]-line[1]*v[0] > 0:   #make sure the half that has referencePoint is returned first
        return half1,half2
    else:
        return half2,half1


def getTriangles(image,triangle, pointPixelList, threshold):
    """ takes in an image and 3 points that represent a triangle
        and returns a list of smaller triangles that make up 
        the big triangle and their respective average colors"""
    
    pixelList = [pixel for p, pixel in pointPixelList]
    
    # if the colors in the box are similar or the box is too small, return
    if variance(pixelList) < threshold: 
        color = average(pixelList)
        return [(triangle,color)]
    
    # else, find the way to split the triangle with the least total variance
    else:
        bestVariance = float('inf')
        triangle1 = None
        triangle2 = None
        bestPPList1 = None
        bestPPList2 = None

        for point in triangle:

            otherpoints = [p for p in triangle if p != point]

            mid = midpoint(otherpoints[0],otherpoints[1])

            pointPixelList1,pointPixelList2 = split(pointPixelList, point, mid,
                                                    otherpoints[0])

            pixelList1 = [pixel for p,pixel in pointPixelList1]
            pixelList2 = [pixel for p,pixel in pointPixelList2]

            # only consider splits if they leave some pixels in each side            
            if pixelList1 and pixelList2:
                variance1 = variance(pixelList1)
                variance2 = variance(pixelList2)

                # split the triangle if it's too wide
                baseLength = distance(otherpoints[0], otherpoints[1])
                if (baseLength**2)/(2.0*len(pointPixelList)) > MAX_WIDTH_TO_HEIGHT:
                    bestVariance = 0
                    triangle1 = (mid,point,otherpoints[0])
                    triangle2 = (mid,point,otherpoints[1])
                    bestPPList1 = pointPixelList1
                    bestPPList2 = pointPixelList2

                # if the combined variances are the smallest, 
                # this is the best way to split it
                if variance1 + variance2 <= bestVariance:     
                    bestVariance = variance1 + variance2
                    triangle1 = (mid,point,otherpoints[0])
                    triangle2 = (mid,point,otherpoints[1])
                    bestPPList1 = pointPixelList1
                    bestPPList2 = pointPixelList2

        # split if we found a viable one, otherwise don't
        if triangle1:
            firstHalf = getTriangles(image,triangle1, bestPPList1, threshold)
            secondHalf = getTriangles(image,triangle2,bestPPList2, threshold)
            return firstHalf + secondHalf
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


def makeThumbnail(image, workingWidth):
    """ makes image into a thumbnail and returns 
        that thumbnail's width and height as a tuple """
    bbox = image.getbbox()
    width = bbox[2]-bbox[0]
    height = bbox[3]-bbox[1]

    if workingWidth:
        workingHeight = height * workingWidth / width
        size = (workingWidth, workingHeight)
        image.thumbnail(size)
        return size
    else:
        return (width, height)


def createImage(imageName, saveType="svg", saveName="triangled", 
                scaleFactor=3, workingWidth=0, threshold=500):
    
    image =  Image.open("img/" + imageName)

    workingSize = makeThumbnail(image, workingWidth)
    
    print "Image loaded"
    
    points = []
    for x in range(workingSize[0]):
        for y in range(workingSize[1]):
            points.append((x,y))
    
    startTime = time.time()
    
    leftX,topY,rightX,bottomY =  image.getbbox()

    # find the starting triangle coordinates    
    topLeft = (leftX,topY)
    topRight = (rightX,topY)
    bottomLeft = (leftX, bottomY)
    bottomRight = (rightX, bottomY)

    pointPixelList = [(p, image.getpixel(p)) for p in points]

    PPL1,PPL2 = split(pointPixelList,(0,0),workingSize,topRight)

    triangleList = [] 
    print "Getting triangles, part 1"
    triangleList += getTriangles(image, (bottomRight,topLeft, topRight),
                                 PPL1, threshold)
    print "halfway done getting triangles in,",
    print round(time.time() - startTime,1), "seconds" 

    print "Getting triangles, part 2"
    triangleList += getTriangles(image, (topLeft, bottomRight, bottomLeft),
                                 PPL2, threshold)

    print "triangles found in,", round(time.time() - startTime,1), "seconds" 

    startTime = time.time()

    if saveType == "svg":
        print "Creating Image"
        svgFile = svgwrite.Drawing(filename = "triangled/" + saveName + ".svg",
                                   size = svgScale(workingSize,scaleFactor))
        for triangle,color in triangleList:
            triangle = [scale(point,scaleFactor) for point in triangle]
            svgFile.add(svgFile.polygon(points = triangle,
                                        stroke = rgb(color),
                                        fill = rgb(color)))
        svgFile.save()
        
        print "Image created in", round(time.time() - startTime,1), "seconds"
    
    elif saveType == "jpg":
        print "Placing pixels"
        # Makes a new, higher quality image out of the list of triangles
        image = Image.new('RGB',scale(workingSize,scaleFactor))
        #imageNumber = 0
        for triangle,color in triangleList:
            triangle = tuple([scale(point,scaleFactor) for point in triangle])
            for point in pointsIn(triangle):
                image.putpixel(point,color)
            #if imageNumber % 20 == 0:
            #   image.save("sunsetProcess/"+ str(imageNumber) + ".jpg")
            #imageNumber += 1
        
        print "Pixels Placed in", round(time.time() - startTime,1), "seconds"
    
        image.save("triangled/" + saveName + ".jpg")
