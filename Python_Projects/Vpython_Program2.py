# Date:  November 2, 2023
import vpython
#Start of code borrowed from Sample Code Objects
#Start of code borrowed from Sample Code Bicycle
from vpython import *

# Create the objects
class Larry:
    def __init__(self, pos=vector(0, 0, 0)):
        #body
        self.torso= ellipsoid(pos=pos + vector(0, 5, 0.45), axis=vector(0, 0, 2),
                                    color=color.green, length=5,width=5, height=11)
        #face
        self.nose= ellipsoid(pos=pos + vector(0, 6.7, 3), axis=vector(0, 0, 2),
                             color=color.green, width=1, height=1, length=0.3)
        self.eye1=ellipsoid(pos=pos + vector(0.5, 7.5, 3), axis=vector(0, 0, 2),
                             color=color.green, width=1, height=1.5, length=0.1)
        self.eye2 = ellipsoid(pos=pos + vector(-0.5, 7.5, 3), axis=vector(0, 0, 2),
                              color=color.green, width=1, height=1.5, length=0.1)
        self.white1 = ellipsoid(pos=pos + vector(0.5, 7.5, 3), axis=vector(0, 0, 2),
                              color=color.white, width=1, height=1.3, length=0.2)
        self.white2 = ellipsoid(pos=pos + vector(-0.5, 7.5, 3), axis=vector(0, 0, 2),
                              color=color.white, width=1, height=1.3, length=0.2)
        self.pupil1 = ellipsoid(pos=pos + vector(0.5, 7.5, 3), axis=vector(0, 0, 2),
                              color=color.black, width=0.6, height=0.6, length=0.3)
        self.pupil2 = ellipsoid(pos=pos + vector(-0.5, 7.5, 3), axis=vector(0, 0, 2),
                                color=color.black, width=0.6, height=0.6, length=0.3)
        class larryMouth:
            def __init__(self, pos=vector(0, 0, 0)):
                #Code borrowed from ChatGPT output
                #Modify the mouth to create a half-circle shape
                angle = 1 * pi  # Half of pi radians (180 degrees)
                radius = 1
                num_points = 100
                self.mouth = curve(pos=[pos + vector(radius * cos(angle * i / num_points),
                                                     5 - radius * sin(angle * i / num_points),
                                                     3) for i in range(num_points)],
                                   color=color.black)
        larryMouth = larryMouth(pos=pos + vector(0, 1, 0.2))
class Bob:
    def __init__(self, pos=vector(0, 0, 0)):
        #body
        self.torso = ellipsoid(pos=pos + vector(0, 2.5, 0.45), axis=vector(0, 0, 2),
                               color=color.red, height=6, length=6, width=6.6)
        #face
        self.nose = ellipsoid(pos=pos + vector(0, 3.2, 3.6), axis=vector(0, 0, 2),
                              color=color.red, width=1, height=1, length=0.3)
        self.eye1 = ellipsoid(pos=pos + vector(0.5, 4, 3.6), axis=vector(0, 0, 2),
                              color=color.red, width=1, height=1.5, length=0.1)
        self.eye2 = ellipsoid(pos=pos + vector(-0.5, 4, 3.6), axis=vector(0, 0, 2),
                              color=color.red, width=1, height=1.5, length=0.1)
        self.white1 = ellipsoid(pos=pos + vector(0.5, 4, 3.6), axis=vector(0, 0, 2),
                                color=color.white, width=1, height=1.3, length=0.2)
        self.white2 = ellipsoid(pos=pos + vector(-0.5, 4, 3.6), axis=vector(0, 0, 2),
                                color=color.white, width=1, height=1.3, length=0.2)
        self.pupil1 = ellipsoid(pos=pos + vector(0.5, 4, 3.6), axis=vector(0, 0, 2),
                                color=color.black, width=0.6, height=0.6, length=0.3)
        self.pupil2 = ellipsoid(pos=pos + vector(-0.5, 4, 3.6), axis=vector(0, 0, 2),
                                color=color.black, width=0.6, height=0.6, length=0.3)

        class BobMouth:
            def __init__(self, pos=vector(0, 0, 0)):
                # Code borrowed from ChatGPT output
                # Modify the mouth to create a half-circle shape
                angle = 1 * pi  # Half of pi radians (180 degrees)
                radius = 1
                num_points = 100
                self.mouth = curve(pos=[pos + vector(radius * cos(angle * i / num_points),
                                                     5 - radius * sin(angle * i / num_points),
                                                     3) for i in range(num_points)],
                                   color=color.black)

        BobMouth = BobMouth(pos=pos + vector(0, -2, 0.5))
        class bobHair:
            def __init__(self, pos=vector(0, 0, 0)):
                #hair
                hair_pos = pos + vector(0, 4.3, 4.2)
                hair_height = 1
                hair_radius = 1
                num_sides = 10

                for i in range(num_sides):
                    angle = 2 * pi * i / num_sides
                    base_pos = hair_pos + vector(hair_radius * cos(angle), hair_radius * sin(angle), 0)
                    tip_pos = hair_pos + vector(0, 0, hair_height)
                    pyramid(pos=base_pos, axis=tip_pos - base_pos, size=vector(hair_radius * 2, hair_radius * 2, 0),
                            color=color.green)
        bobHair = bobHair(pos=pos + vector(0,1,-3.7))
class Sink:
    def __init__(self, pos=vector(0, 0, 0)):
        self.bottom = box(pos=vector(-30,1,20),length=40, width=30, height=2, color=color.gray(0.8))
        self.inner = box(pos=vector(-30,1.3,20),length=35, width=25, height=2, color=color.black)
        self.midpart = box(pos=vector(-30,15,10),length=8, width=8, height=30, color=color.gray(0.8))
        self.top = box(pos=vector(-30,30,15.6),length=8, width=20, height=5, color=color.gray(0.8))

#mainline
scene = canvas(background=color.gray(0.2))
floor = box(pos=vector(0,0,0),length=100, width=100, height=2, color=color.white)
backWall = box(pos=vector(0,50,-50),length=100, width=2, height=100, color=color.white)
window = box(pos=vector(-30,30,-47),length=30, width=2, height=30, color=color.blue)
Sink = Sink(vector(0,0,0))
Larry = Larry(vector(5, 1, 5))
Bob = Bob(vector(15,1,5))

while True:
    pass

