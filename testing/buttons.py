from micropython import const
from machine import Pin
from time import ticks_ms, ticks_diff

_LED_MAIN_CONV = 2
_LED_COMM_TRANS = 3
_LED_COMM_RCVR = 4
_SIG_TRANS = 6  # 31 kHz 50% PWM for 3 seconds on button pressed

_G_Q1Q4 = 8  # Gate drive signal for Q2 and Q5
# G_Q2Q3 = 9  # Gate drive signal for Q3 and Q4, by default G_Q1Q4 +1

_START_BTN = 22  # Power transmission start button
_STOP_BTN = 21  # Power transmission stop button
_COMM_BTN = 26  # Comm send button
_COMM_READ = 27  # Input from comm receiver # FIXME requires voltage divider


class Button:
    def __init__(self, pin_num, callback=None, pull=Pin.PULL_UP):
        self.pin = Pin(pin_num, Pin.IN, pull)
        self.callback = callback
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_irq)
        self._last_state = self.pin.value()
        self._debounce_time = 30  # milliseconds
        self._last_time = 0
        # self.timer = Timer(-1)

    def _handle_irq(self, pin):
        current_time = ticks_ms()
        if ticks_diff(current_time, self._last_time) > self._debounce_time:
            new_state = self.pin.value()
            if new_state != self._last_state:
                self._last_state = new_state
                if self.callback:
                    self.callback(new_state, pin)
            self._last_time = current_time


def start_callback(state, pin):
    if state == 0:  # Button pressed
        green_led.toggle()
        print("Button state:", state, "\tButton pin:", pin)


def stop_callback(state, pin):
    if state == 0:  # Button pressed
        red_led.toggle()
        print("Button state:", state, "\tButton pin:", pin)


start_btn = Button(_START_BTN, callback=start_callback)
stop_btn = Button(_STOP_BTN, callback=stop_callback)

red_led = Pin(_LED_MAIN_CONV, Pin.OUT)
green_led = Pin(_LED_COMM_RCVR, Pin.OUT)

while True:
    pass
