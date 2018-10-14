# import pygame
# from pygame.locals import *
import trianglemosaic
import freeform
from Tkinter import Tk, Label, Button, IntVar, StringVar, Radiobutton, Scale
import tkFileDialog


class FilterSelector:
    def __init__(self, master):
        self.master = master
        master.title("Choose your settings")

        self.imageButton = Button(master, text="Select Image",
                                  command=self.selectImage)
        self.imageButton.grid(row=0)

        self.imagePath = ""
        self.imageName = StringVar()
        self.imageName.set("No Image Selected")
        self.imageLabel = Label(master, textvariable=self.imageName)
        self.imageLabel.grid(row=0, column=1)

        self.alg = IntVar()
        self.selectTriangle = Radiobutton(master, text="Freeform",
                                          variable=self.alg, value=0)
        self.selectFreeform = Radiobutton(master, text="Triangle",
                                          variable=self.alg, value=1)
        self.selectTriangle.grid(row=1, column=0)
        self.selectFreeform.grid(row=1, column=1)

        self.workingWidth = IntVar()
        widthScale = Scale(master, variable=self.workingWidth, from_=100,
                           to=2000, orient="horizontal")
        widthScale.grid(row=2, column=0)

        self.doItButton = Button(master, text="Make it Happen",
                                 command=self.processImage)
        self.doItButton.grid(row=3, column=0)

    def selectImage(self):
        self.imagePath = tkFileDialog.askopenfilename(initialdir="img/",
                                                      title="Select file")
        self.imageName.set(self.imagePath.split("/")[-1])

    def processImage(self):
        if self.alg.get() == 0:
            freeform.createImage(self.imageName.get(),
                                       workingWidth=self.workingWidth.get())
        elif self.alg.get() == 1:
            trianglemosaic.createImage(self.imageName.get(),
                                 workingWidth=self.workingWidth.get())


root = Tk()
my_gui = FilterSelector(root)
root.mainloop()
