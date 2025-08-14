# enc.py
# Rotary encoder class with half-step support for MicroPython

from machine import Pin
import time

# Encoder pin definitions
SW_PIN = 15
DT_PIN = 13
CLK_PIN = 12


class RotaryEncoder:
    # State table for half-step decoding (Gray code)
    _halfstep_table = [0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0]

    def __init__(
        self,
        pin_a,
        pin_b,
        button_pin=None,
        callback=None,
        button_callback=None,
        pull=None,
        debounce_ms=50,
        step_scale=1,
    ):
        self.pin_a = Pin(pin_a, Pin.IN, pull or Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, pull or Pin.PULL_UP)
        self.state = (self.pin_a.value() << 1) | self.pin_b.value()
        self.position = 0
        self.callback = callback
        self.button_callback = button_callback
        self.button_pin = None
        self.button_state = 1  # Assume not pressed (pull-up)
        self.debounce_ms = debounce_ms
        self._last_button_time = 0
        self.step_scale = step_scale
        if button_pin is not None:
            self.button_pin = Pin(button_pin, Pin.IN, pull or Pin.PULL_UP)
            self.button_pin.irq(
                trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._button_update
            )
        # Set up interrupts
        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update)

    def _update(self, pin):
        prev_state = self.state
        self.state = (self.pin_a.value() << 1) | self.pin_b.value()
        idx = (prev_state << 2) | self.state
        movement = self._halfstep_table[idx]
        if movement:
            self.position += movement * self.step_scale
            if self.callback:
                self.callback(self.position)

    def _button_update(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_button_time) < self.debounce_ms:
            return  # debounce
        self._last_button_time = now
        new_state = self.button_pin.value()
        if new_state != self.button_state:
            self.button_state = new_state
            if self.button_callback:
                self.button_callback(self.button_state == 0)  # True if pressed

    def get(self):
        return self.position

    def reset(self, value=0):
        self.position = value

    def button_pressed(self):
        if self.button_pin:
            return self.button_pin.value() == 0
        return False


if __name__ == "__main__":
    def rotary_callback(pos):
        print("Encoder position:", pos)

    def button_callback(pressed):
        if pressed:
            print("Button pressed!")
        else:
            print("Button released!")

    enc = RotaryEncoder(
        pin_a=CLK_PIN,
        pin_b=DT_PIN,
        button_pin=SW_PIN,
        callback=rotary_callback,
        button_callback=button_callback,
    )

    print("Rotate the encoder or press the button (Ctrl+C to exit)...")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting.")
