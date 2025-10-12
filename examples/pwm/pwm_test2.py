from machine import
from rp2 import PIO, StateMachine, asm_pio


class GatePWM:
    """
    Class for generating PWM signals for gate control.
    """

    @asm_pio(set_init=PIO.OUT_LOW, out_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_RIGHT)
    def q1_pwm_asm():
        # Setup
        pull(noblock)  # Get duty value
        mov(y, osr)  # Store duty in y

        wrap_target()
        # High period
        mov(x, y)  # Load duty value
        set(pins, 1)  # Set pin high
        label("high")
        jmp(x_dec, "high")  # Stay high for duty period

        # Low period
        mov(x, invert(y))  # Load inverse of duty for low period
        set(pins, 0)  # Set pin low
        label("low")
        jmp(x_dec, "low")  # Stay low for remaining period

        wrap()  # Loop back

    def __init__(self, pin, sm_freq=2_000_000, pwm_freq):
        self.q1 = Pin(pin, Pin.OUT)
        self.freq = sm_freq
        self.sm = StateMachine(0, GatePWM.q1_pwm_asm, freq=self.freq, set_base=self.q1)

    