import viz
import vizfx
import vizact

#Start of code taken from Vizard tutorials "Setting the scene"
#Start of code inspired from Sample Code VR Animation
#functions with timers
def spinRed(redAngryBird):
	typical_spin = vizact.spin(0,1,0,15)
	redAngryBird.addAction(typical_spin)
	vizact.ontimer(2,spinRed,redAngryBird)
def biggerRed(redAngryBird):
	newSize = redAngryBird.setScale(20,20,20)
	redAngryBird.addAction(newSize)
	vizact.ontimer(2,biggerRed,redAngryBird)
def flightRed(redAngryBird):
	newLocation = redAngryBird.setPosition(3,5,3)
	redAngryBird.addAction(newLocation)
	vizact.ontimer(2,flightRed,redAngryBird)

#enable full screen anti-aliasing (FSAA) to smooth edges
viz.setMultiSample(4)

viz.go()

#increase Field of View
viz.MainWindow.fov(70)

#create the scene
scene = vizfx.addChild('Vizard vr program thing anger bord/theNewScene.osgb')

#turn collisions on
viz.collision(viz.ON)


redAngryBird = scene.getChild('redbird.gltf')

#timers
vizact.ontimer(10,flightRed,redAngryBird)
vizact.ontimer(20,biggerRed,redAngryBird)
vizact.ontimer(30,spinRed,redAngryBird)
