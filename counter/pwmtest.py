from machine import Pin
import rp2
from time import sleep_us


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def pwm_pio():
    wrap_target()
    mov(x, osr)
    mov(y, isr)
    set(pins, 0)
    label("low")
    jmp(x_not_y, "high")
    set(pins, 1)
    label("high")
    jmp(y_dec, "low")
    wrap()


class PinPWM:
    def __init__(self, sm_id, pin, period, pw, freq=20_000_000):
        self._sm = rp2.StateMachine(sm_id, pwm_pio, freq=freq, set_base=Pin(pin))
        self._sm.active(1)
        self._period = period
        self._pw = pw
        self.setup()

    def setup(self):
        self._sm.put(self._period)
        self._sm.exec("pull()")
        self._sm.exec("mov(isr, osr)")
        self._sm.put(self._pw)
        self._sm.exec("pull()")

    def set_period(self, period):
        self._period = period
        self.setup()

    def set_pw(self, pw):
        self._pw = pw
        self._sm.put(self._pw)


# sm0 = rp2.StateMachine(0, pwm_pio, freq=2_000_000, set_base=Pin(16))

try:
    sm0.active(1)
    sm0.put(20000)  # Set period to 20ms
    sm0.exec("pull()")
    sm0.exec("mov(isr, osr)")
    sm0.put(1500)  # Set pulse width to 1.5ms
    sm0.exec("pull()")
    sleep_us(5_000)  # Wait for 1 second

    while True:
        for i in range(0, 10000, 100):
            sm0.put(i)
            sm0.exec("pull()")
            sleep_us(10000)
except KeyboardInterrupt:
    sm0.active(0)
