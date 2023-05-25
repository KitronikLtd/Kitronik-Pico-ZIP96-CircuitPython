from ZIP96Pico import *

screenLength = 96
gamer = KitronikZIP96()
screen = gamer.Screen
screen.setBrightness(10)

while True:
    if gamer.Up.pressed():
        for i in range(screenLength):
            screen.setLED(i, (255, 255, 255))
            screen.show()
    
    if gamer.Left.pressed():
        screen.fill((255, 0, 0))
        screen.show()
    
    if gamer.Down.pressed():
        screen.fill((0, 255, 0))
        screen.show()
    
    if gamer.Right.pressed():
        screen.fill((0, 0, 255))
        screen.show()
    
    if gamer.A.pressed():
        gamer.Buzzer.playTone(500)
    else:
        gamer.Buzzer.stopTone()
    
    if gamer.B.pressed():
        gamer.Vibrate.vibrate()
    else:
        gamer.Vibrate.stop()
