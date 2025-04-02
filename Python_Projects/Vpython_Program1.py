# Date:  October 31, 2023
import vpython
#Import vpython and time
from vpython import *
from time import *
#Create boxes
torso = box(pos=vector(0,-10,0),color=color.blue, length=9,height=10,width=7)
legs = box(pos=vector(0,-20,0),color=color.green, length=9,height=10,width=7)
arm1 = box(pos=vector(7.6,-8,5),color=color.yellow, length=6,height=6,width=13)
arm2 = box(pos=vector(-7.6,-8,5),color=color.yellow, length=6,height=6,width=13)
#Create spheres
head = sphere(pos=vector(0,0,0),color=color.yellow, radius=5)
ball = sphere(pos=vector(0,15,3), color=color.red, radius =7)
#Disco ball method
disco = 1
while disco < 10:
    sleep(0.1)
    ball.color = color.blue
    sleep(0.1)
    ball.color = color.purple
    sleep(0.1)
    ball.color = color.green
    sleep(0.1)
    ball.color = color.orange
    sleep(0.1)
    ball.color = color.magenta
    sleep(0.1)
    ball.color = color.cyan
while True:
    pass
