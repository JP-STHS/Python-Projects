# Date:  November 13, 2023

from vpython import *
import random

#Puzzle box game - find the secret number

scene = canvas(background=color.gray(0.7))
floor = box(pos=vector(0,-5,0), length=100, width=100,height=4)

susWall = box(pos=vector(0,20,0),length=50, width=50,height=50,color=color.gray(0.5))
secretWall = box(pos=vector(0,20,3),length=45, width=50,height=45,color=color.gray(0.4))
normalwall = box(pos=vector(0,20,6),length=49, width=50,height=49,color=color.gray(0.3))
barrier = box(pos=vector(0,20,0),length=110, width=110,height=110,color=color.black)
#Start of code inspired from Python 3D Graphics Tutorial 21 by Paul McWhorter:
#https://www.youtube.com/watch?v=PJKBrPkcoMo&t=2388s
run=0
secretnum = random.randint(1, 100)
#make fake wall
def wallOpacity(x):
    op=x.value
    susWall.opacity=op
    if susWall.opacity>0:
        #show secret message
        #Start of code inspired from ChatGPT output
        secretmessage.visible = False
    else:
        secretmessage.visible = True

def wallBarrier(x):
    global run
    if x.checked == True:
        run = 1
        barrier.pos=vector(0,40,0)
        sleep(0.2)
        barrier.pos = vector(0, 60, 0)
        sleep(0.2)
        barrier.pos = vector(0, 80, 0)
        sleep(0.2)
        barrier.pos = vector(0, 100, 0)
        sleep(0.2)
    if x.checked == False:
        run = 0
        barrier.pos=vector(0,20,0)
secretmessage = text(pos=vector(0, 20, -40), text= str(secretnum) + ' !oY 😏', height=3,color=color.orange)
secretmessage.visible=False

#mainline
radio(bind=wallBarrier, text='Remove barrier')
scene.append_to_caption('\n\n')
wtext(text='???')
slider(bind=wallOpacity, vertical=False,min=0,max=1,value=1,)

print("Welcome to the random number puzzle")
print("Find the secret number by solving the vpython box puzzle.")
answer = int(input('\nWhat is the secret number? (displayed backwards) '))
if answer == secretnum:
    print("Congrats! You win!")
elif answer != secretnum:
    print("Wrong! Better luck next time.")

while True:
    rate(30)
    pass


