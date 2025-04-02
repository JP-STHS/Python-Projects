import viz

#Start of code taken from Vizard tutorial "Setting the scene"

#enable full screen anti-aliasing (FSAA) to smooth edges
viz.setMultiSample(4)

viz.go()

#increase Field of View
viz.MainWindow.fov(70)

#create the gallery
gallery = viz.addChild("gallery.osgb")
#turn collisions on
viz.collision(viz.ON)
