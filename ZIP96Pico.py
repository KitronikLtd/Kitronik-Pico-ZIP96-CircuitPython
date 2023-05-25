from time import sleep
from board import GP1, GP2, GP4, GP5, GP7, GP12, GP13, GP14, GP15
from digitalio import DigitalInOut, Direction, Pull
from pwmio import PWMOut
from rp2pio import StateMachine
from adafruit_pioasm import Program
from adafruit_pixelbuf import PixelBuf
from struct import pack

p = Program("""
.program ws2812
.side_set 1

.wrap_target
    pull block          side 0
    out y, 32           side 0      ; get count of ws2812 bits

bitloop:
    pull ifempty        side 0      ; drive low
    out x 1             side 0 [5]
    jmp !x do_zero      side 1 [3]  ; drive high and branch depending on bit val
    jmp y--, bitloop    side 1 [4]  ; drive high for a one (long pulse)
    jmp end_sequence    side 0      ; sequence is over

do_zero:
    jmp y--, bitloop    side 0 [4]  ; drive low for a zero (short pulse)

end_sequence:
    pull block          side 0      ; get fresh delay value
    out y, 32           side 0      ; get delay count

wait_reset:
    jmp y--, wait_reset side 0      ; wait until delay elapses
.wrap
""")

class KitronikZIPLEDsPIO(PixelBuf):
    def __init__(self, pin, num_leds, brightness=0.1, auto_write=True):
        byte_count = 3 * num_leds
        bit_count = byte_count * 8
        padding_count = -byte_count % 4
        # backwards, so that dma byteswap corrects it!
        header = pack(">L", bit_count - 1)
        trailer = b"\0" * padding_count + pack(">L", 3840)

        self.sm = StateMachine(p.assembled,
                               frequency=12_800_000,
                               first_sideset_pin=pin,
                               out_shift_right=False,
                               auto_pull=False,
                               pull_threshold=32,
                               **p.pio_kwargs)

        super().__init__(num_leds,
                         byteorder="GRB",
                         brightness=brightness,
                         auto_write=auto_write,
                         header=header,
                         trailer=trailer)

    def _transmit(self, buf):
        self.sm.background_write(memoryview(buf).cast("L"), swap=True)

'''
Class for the Pico 96 LED retro gamer.    
'''

# The KitronikButton class enable the use of the 2 user input buttons on the board
class KitronikButton:
    def __init__(self, WhichPin):
        self.theButton = DigitalInOut(WhichPin)
        self.theButton.direction = Direction.INPUT
        self.theButton.pull = Pull.DOWN
        
    def pressed(self):
        return self.theButton.value
        
        
# The KitronikVibrate class enable the use of the vibration motor on the board
class KitronikVibrate:
    def __init__(self, WhichPin):
        self.theMotor = DigitalInOut(WhichPin)
        self.theMotor.direction = Direction.OUTPUT
        
    def vibrate(self):
        self.theMotor.value = True
    
    def stop(self):
        self.theMotor.value = False
    

# The KitronikBuzzer class enables control of the piezo buzzer on the board
class KitronikBuzzer:
    # Function is called when the class is initialised and sets the buzzer pin to GP2
    def __init__(self, WhichPin):
        self.buzzer = PWMOut(WhichPin, variable_frequency=True)

    # Play a continous tone at a specified frequency
    def playTone(self, freq):
        if freq < 30:
            freq = 30
        if freq > 3000:
            freq = 3000
        self.buzzer.frequency = freq
        self.buzzer.duty_cycle = 32767

    # Play a tone at a speciied frequency for a specified length of time in ms
    def playTone_Length(self, freq, length):
        self.playTone(freq)
        sleep(length / 1000)
        self.stopTone()

    # Stop the buzzer producing a tone
    def stopTone(self):
        self.buzzer.duty_cycle = 0

# The KitronikZIPLEDs class enables control of the ZIP LEDs on the board
class KitronikZIPLEDs:
    # Define some colour tuples for people to use.    
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)
    WHITE = (255, 255, 255)
    COLOURS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

    # We drive the ZIP LEDs using one of the PIO statemachines.
    def __init__(self, num_zip_leds=96, brightness=0.2, ZIPPin=GP7):
        self.num_zip_leds = num_zip_leds
        # Create and start the StateMachine for the ZIPLeds
        self.ZIPLEDs = KitronikZIPLEDsPIO(ZIPPin, num_zip_leds, brightness=brightness, auto_write=False)

    # Show pushes the current setup of the LEDS to the physical LEDS - it makes them visible.
    def show(self):
        self.ZIPLEDs.show()

    # Turn the LED off by setting the colour to black
    def clear(self, whichLED):
        self.setLED(whichLED, self.BLACK)
        
    # Sets the colour of an individual LED. Use show to make change visible
    def setLED(self, whichLED, whichColour):
        if whichLED < 0:
            raise Exception("INVALID LED:", whichLED, " specified")
        elif whichLED > self.num_zip_leds - 1:
            raise Exception("INVALID LED:", whichLED, " specified")
        else:
            self.ZIPLEDs[whichLED] = whichColour

    def setLEDMatrix(self, X, Y, whichColour):
        #unpack X and Y into the single strip LED position
        whichLED = X + (Y * 12)
        self.setLED(whichLED, whichColour)
        
    # Gets the stored colour of an individual LED, which isnt nessecerily the colour on show if it has been changed, but not 'show'n
    def getLED(self, whichLED):
        if whichLED < 0:
            raise Exception("INVALID LED:", whichLED, " specified")
        elif whichLED > self.num_zip_leds - 1:
            raise Exception("INVALID LED:", whichLED, " specified")
        else:
            return self.ZIPLEDs[whichLED]
    
    # Sets the colour of all LEDs to be the same.
    def fill(self, colour):
        for LED in range(self.num_zip_leds):
            self.setLED(LED, colour)
    
    # Takes 0-100 as a brightness value, brighness is applies in the'show' function
    def setBrightness(self, value):
        # Cap to 0 - 100%
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        
        self.ZIPLEDs.brightness = value / 100

class KitronikZIP96:
    def __init__(self):
        self.Up = KitronikButton(GP14)
        self.Down = KitronikButton(GP12)
        self.Left = KitronikButton(GP13)
        self.Right= KitronikButton(GP15)
        self.A = KitronikButton(GP1)
        self.B = KitronikButton(GP2)
        
        self.Screen = KitronikZIPLEDs()
        self.Buzzer = KitronikBuzzer(GP5)
        self.Vibrate = KitronikVibrate(GP4)