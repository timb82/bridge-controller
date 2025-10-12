# Code was written for the Pi Pico, for the Pi Pico W, use an output with an external LED to get visual feedback.

# This example takes a simpler approach to explain PIO and how it integrates with Micropython
# on the Raspberry Pi Pico.

# This is example code on how to have two pairs or state machines, who are working together, run simultaneously.
# Because they can't be called at the same time, but can run independently at the same time,
# we activate the machines one by one, and then use a Pin which they both are waiting for at the same time.
# The onboard LED will turn ON while both programs are running. When each program is completed they will write to REPL.
# Once both programs are done, user will be asked to press enter again to run the programs again.

# Program can run without connecting anything to the Pi Pico, but one suggestion is adding LED's to the outputs
# and use Pins that works for you.

# I used this code as a base for my stepper motor project:
# https://github.com/Vendelator/RP2040_PIO_Steppermotors - MIT license
# The best source for explaining PIO: https://dernulleffekt.de/doku.php?id=raspberrypipico:pico_pio

# To change how many times the pins toggle, change the values in sm_0.put() and sm_4.put().
# To change how fast the program toggles, change frequency and add/remove delay [x]
# which can be done to any isntruction in the PIO routines.
# In the example i use nop() [31], which delays for 1 + 31 cycles.

# At current setting with 20_000 Hz frequency, (1 + 1 + (32 * 65) + 1) instruction in delay(),
# pins will toggle at approximatly 10 hZ.(10 times a second)
# This means PIO block 0 will take 10 seconds to finish and PIO block 1 will take 20 seconds.


# import machine     # To be able to control GPIO Pins
from machine import Pin  # To be able to use Pin objects
import rp2  # To be able to use state machines

trigger_pin = Pin(28, Pin.OUT)  # This pin will trigger our state machines using wait(1, gpio, 25).
pio_block_0 = False  # True/False object used to see if the program is allowed to proceed.
pio_block_1 = False  # - " -


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)  # Tells our program that this is a PIO routine and to set the pin low on activation.
def pin_activator():
    pull(block)  # Wait for FIFO to fill (put), then pull data to OSR.
    mov(x, osr)  # Copy OSR data from to X.
    wait(1, gpio, 25)  # Does nothing until GPIO Pin 25 is set to high, this is how we synchronize activation.

    label("Jump_Point")  # this is a header we jump back to for counting steps.
    set(pins, 1)  # Sets the in_base Pin high.
    jmp(not_x, "end")  # if X is 0(zero), jump to end.
    irq(5)  # Sets IRQ 5 high, signaling.
    irq(block, 4)  # Waiting for IRQ flag 4 to clear before proceeding.
    set(pins, 0)  # Sets the in_base Pin low.
    jmp(x_dec, "Jump_Point")  # if x is NOT 0(zero), remove one (-1) from X and jump back to "Jump_Point", Else, proceed.

    label("end")  # This is a label we can jump to if X is 0.
    irq(block, rel(0))  # Signals IRQ handler of the actual state machine and waits for handler to clear the flag. Once the
    # handler clears the flag, the program restarts and is blocked until new data is available.


@rp2.asm_pio()  # Does not manipulate any hardware, it's just code. empty  ()
def delay():
    wait(1, irq, 5)  # Waiting for IRQ flag 5 from pin_activator and then clears it.
    set(y, 31)  # Sets Y to the value 31.
    label("Delay")  # This is a header we jump back to for adding a delay.
    nop()[31]  # nop() does nothing for [n] instructions.
    nop()[31]  # - " -
    jmp(y_dec, "Delay")  # If Y not 0(zero), remove one (-1) from Y and make jump to
    # delay, Else, proceed.
    irq(clear, 4)  # Clears IRQ flag 4, allowing step_counter() to continue

    # At this point, the program restarts, and begins with waiting for IRQ


def pio_0_handler(sm):  # This is our Interrupt handler for PIO block 0.
    global pio_block_0  # To be able to change our global variable.
    pio_block_0 = True  # Change variable to True to be able to exit loop.
    print(sm, "sending interrupt.", "\nPio-Block 0 done!")
    # sm is the statemachine calling the handler.
    # Here we could trigger other functions or execute code
    # like turning a Pin on or off.


def pio_1_handler(sm):  # This is our Interrupt handler for PIO block 1
    global pio_block_1  # To be able to change our global variable
    pio_block_1 = True  # Change variable to True to be able to exit loop.
    print(sm, "sending interrupt.", "\nPio-Block 1 done!")
    # sm is the statemachine calling the handler.
    # Here we could trigger other functions or execute code
    # like turning a Pin on or off.


#                        --- PIO Block 0 ---
sm_0 = rp2.StateMachine(0, pin_activator, freq=20000, set_base=Pin(16))
# Calls rp2 and Instantiate a statemachine
# (0, ... is the statemachine number. (0-7)
# , pin_activator ... is the PIO routine
# , freq=2000 ... sets the frequency to 2000 Hz
# , in_base=Pin(0) ... sets GPIO 0 as our base pin.

sm_0.irq(pio_0_handler)  # Tells the program that any interrupt from sm_0 should activate the function pio_0_handler(sm):

sm_1 = rp2.StateMachine(1, delay, freq=20000)
# Creates object called sm_1 and binds it to state machine 1 in PIO block 0)

#                        --- PIO Block 1 ---
sm_4 = rp2.StateMachine(4, pin_activator, freq=20000, set_base=Pin(17))
# Calls rp2 and Instantiate a statemachine
# (4, ... is the statemachine number. (0-7)
# , pin_activator ... is the PIO routine
# , freq=2000 ... sets the frequency to 2000 Hz
# , set_base=Pin(0) ... sets GPIO 0 as our base pin.

sm_4.irq(pio_1_handler)  # Tells the program that any interrupt from sm_4 should activate
# the function pio_1_handler(sm):

sm_5 = rp2.StateMachine(5, delay, freq=20000)
# Creates object called sm_1 and binds it to state machine 5 in PIO block 1)

#                        --- Starting the State machines ---
sm_0.active(1), sm_1.active(1), sm_4.active(1), sm_5.active(1)
# All 4 state machines are now running
# State machine 0 in PIO 0 and state machine 4 in PIO 1 are both waiting to be fed data.

sm_0.put(100)  # We can "put" data into state machine 0 using an integer.
# This number will tell pin_activator() how many times to turn on/off.
any_number = 200
sm_4.put(any_number)  # We can also use a variable.

# Both state machines are now fed, have copied this value into X
# and are waiting for GPIO 25 to turn high.


#                        --- Running the program ---
while True:
    input("Press enter to execute both programs synchronous...")
    trigger_pin.value(1)
    while True:
        if pio_block_0 and pio_block_1:  # Check if they are both True
            trigger_pin.value(0)
            pio_block_0 = False
            pio_block_1 = False
            break
#                        --- Explaining the program ---
# while is an endless loop unless exited.
# input will pause the while loop until user inputs something (Presses enter in REPL).
# trigger_pin.value(1) sets GPIO 25 high and the onboard LED turns on,
# this will activate our state machines and they will start toggeling the pins.
# their pins and wait for out pre determined period of time before swithcing them of
# again.
# The second while loop will lock us into a loop where we check if
# both handlers have changed pio_block_0 and pio_block_1 to True.
