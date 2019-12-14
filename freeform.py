from PIL import Image
import numpy as np
import time
import random
import svgwrite



# general algorithm strategy in comment form
# initial steps
#   create a hash table mapping points to their pixel's color 
#   generate (random?) points around the image for blobs to center
# main loop
#   go through every blob
#       go through each pixel in the blob
#           go through all neighboring pixels and check inclusion
#               if the pixel hasn't been used in a blob yet, calculate score
#               score is based on several metrics
#                   1. how close the pixel is to the average color
#                   2. how close the pixel is to the center
#                   3. what timestep it currently is
#                       the timestep thing is to make it so after a while unclaimed pixels can just be taken.


# optimization ideas for later:
#   remove points from clump when they are surrounded

IMAGE_NAME = "wallpaper4"
THRESHOLD = 4               # threshold score for adding a point
WORKING_WIDTH = 1600        #width of the image while getting triangles
CLUMP_DENSITY = .01        # number of clumps per pixel - must be much, much less than 1


# dictionary matching points to pixel colors
pixelMap = {}
clumpMap = {}


class Clump:
    def __init__(self,point):
        self.center = point
        self.color = pixelMap[point]
        self.points = set([point])
        self.borderPoints = set([point])
        self.numPoints = 1
        self.timesExpanding = 0

        # mark point as used
        del pixelMap[point]
        clumpMap[point] = self

    def expand(self):
        self.timesExpanding += 1

        # go through points and check their neighbors
        expansionCandidates = set()
        surroundedPoints = set()

        for point in self.borderPoints:
            surrounded = True
            for neighbor in getNeighbors(point):
                if pixelMap.has_key(neighbor):
                    if neighbor not in expansionCandidates:
                        expansionCandidates.add(neighbor)
                    surrounded = False
            if surrounded:
                surroundedPoints.add(point)

        for point in expansionCandidates:
            if self.score(point) < THRESHOLD:
                self.addPoint(point)

        for point in surroundedPoints:
            self.borderPoints.remove(point)

    def addPoint(self, point):

        # Update the average color and clump center
        n = self.numPoints
        self.color = tuple([(n*self.color[i] + pixelMap[point][i]) / (n+1)
                             for i in range(3)])
        # update the center
        self.center = tuple([(n*self.center[i] + point[i]) / (n+1)
                             for i in range(2)])

        self.points.add(point)
        self.borderPoints.add(point)
        self.numPoints += 1

        # mark the point as used
        del pixelMap[point]
        clumpMap[point] = self

    def score(self, point):
        return (difference(pixelMap[point], self.color)
                + difference(point, self.center)) / self.timesExpanding


def getNeighbors(point):
    pointList = []
    for i in [-1,0,1]:
        for j in [-1,0,1]:
            if i != j and j != 0:
                pointList.append( (point[0]+i, point[1] + j) )
    return pointList


def difference(p1,p2):
    return np.sqrt(sum([(p1[i] - p2[i])**2 for i in range(len(p1))]))

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


def createImage(imageName, saveName="freeform", clumpDensity=.005, workingWidth=0):

    image =  Image.open("img/" + imageName)
    workingSize = makeThumbnail(image, workingWidth)
    print "Image loaded"
    

    # populate point to pixel dictionary
    points = []
    for x in range(workingSize[0]):
        for y in range(workingSize[1]):
            pixelMap[(x,y)] = image.getpixel((x, y))
    
    print "pixels analyzed"

    clumpList = []
    numPoints = workingSize[0]*workingSize[1]

    for i in range(int(clumpDensity*numPoints)):
        clumpCenter = (random.randint(0,workingSize[0]-1), random.randint(0,workingSize[1]-1))
        if pixelMap.has_key(clumpCenter):
            clumpList.append(Clump(clumpCenter))

    print "clumps initialized"

    for i in range(400):
        startTime = time.time()
        for clump in clumpList:
            clump.expand()

        print "step", str(i+1), "took", round(time.time() - startTime,1), "seconds" 

    print "Placing pixels"

    pointCount = 0
    image = Image.new('RGB', workingSize, 0x000000)
    for clump in clumpList:
        for point in clump.points:
            pointCount += 1
            image.putpixel(point,tuple(clump.color))
    print(pointCount, numPoints)

    print "Pixels Placed in", round(time.time() - startTime,1), "seconds"

    image.save("freeform/" + saveName + ".png")


def main():
    createImage('connor.jpg', saveName='connor', workingWidth=600)

if __name__ == "__main__":
    main()