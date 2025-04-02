# Date:  November 7, 2023

from vpython import *



#mainline
scene = canvas(background=color.gray(0.7))
#creating the planets
#Start of code borrowed from sample code Moving Planets
earth = sphere(pos=vector(30,0,30),radius=2, color=color.blue)
mars = sphere (pos=vector(45, 0, 30), radius=1.7, color=color.red)
mercury = sphere (pos=vector(10, 0, 30), radius=1.5, color = vector(0.6,0.6,0.6))
venus = sphere (pos=vector(20, 0, 30), radius=2, color = vector(0.6,0.1,0.6))
#Creating the sun
sun = box(length=30, width=2, height=30, color=color.orange)
sun2=box(pos=vector(0,0,2),length=20, width=2, height=20, color=color.yellow)

earth_dist = 1.0
mars_dist = 1.5
mercury_dist = 0.31
venus_dist = 0.72
k = 0.05
while True:
    #animation loop
    rate(45)
    earth.rotate(angle=k / (earth_dist ** 2), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
    mars.rotate(angle=k / (mars_dist ** 2), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
    venus.rotate(angle=k / (venus_dist ** 2), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
    mercury.rotate(angle=k / (mercury_dist ** 2), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
    #methods for angles
    angle1 = pi / 3
    angle2 = -0.7
    axis1 = vector(0, 0, 1)
    sun.rotate(angle=angle1, axis=axis1)
    axis2 = vector(0, 0, 1)
    sun2.rotate(angle=angle2,axis=axis2)
