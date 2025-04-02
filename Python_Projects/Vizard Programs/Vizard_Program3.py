#start of code inspired from YouTube tutorial "How to create a VR experiment in 15 minutes using Python 3.8 with Vizard"
import viz
import vizfx
import vizact
import random

#Start of code taken from Vizard tutorials "Setting the scene"
#Start of code inspired from Sample Code VR Animation
def recenter():
	shortWalk = vizact.walkTo([0,0,5])
	coolMan.setEuler([0,0,0])
	coolMan.addAction(shortWalk)
	fpos = 0
#Start of code taken from VR program Smash Sisters
fpos = 7.0
leftie = 7.0
def forward():
	global fpos
	fpos += 0.3
	coolMan.setEuler([0,0,0])
	typical_move = vizact.moveTo([4.5,0.2,fpos], time = 0.1)
	coolMan.addAction(typical_move,coolMan.state(2))
def backward():
	global fpos
	fpos -= 0.3
	coolMan.setEuler([200,0,0])
	typical_move = vizact.moveTo([4.5,0.2,fpos], time = 0.1)
	coolMan.addAction(typical_move,coolMan.state(2))
def randomfeelings():
	randstate = random.randint(1,15)
	coolMan.state(randstate)
#enable full screen anti-aliasing (FSAA) to smooth edges
viz.setMultiSample(4)

viz.go()

#increase Field of View
viz.MainWindow.fov(70)

#create the scene
scene = vizfx.addChild('Vizard vr program thing anger bord/theNewScene.osgb')

#turn collisions on
viz.collision(viz.ON)

#create the avatar
coolMan = viz.addAvatar('vcc_male2.cfg')
coolMan.setPosition([4.5, 0, 7])
coolMan.setEuler([0,0,0])
#keyboard commands
vizact.onkeydown('q',recenter)
vizact.onkeydown('w',forward)
vizact.onkeydown('s',backward)
vizact.onkeydown('e',randomfeelings)
