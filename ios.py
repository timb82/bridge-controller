from machine import Pin, PWM
from time import ticks_ms, ticks_diff
from cpwm import CompPWM


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


class Comm:
    def __init__(self, btn_pin, led_send_pin, led_rcv_pin, signal_pin, read_pin, freq=31000):
        self.btn = Button(btn_pin, callback=self._btn_callback)
        self.led_snd = Pin(led_send_pin, Pin.OUT)
        self.led_rcv = Pin(led_rcv_pin, Pin.OUT)
        self.freq = freq
        self.signal_out = PWM(Pin(signal_pin, Pin.OUT), freq=self.freq, duty_u16=0)
        self.signal_in = Pin(read_pin, Pin.IN)
        self.signal_in.irq(trigger=Pin.IRQ_RISING, handler=self._read_signal)
        self.transmitting = False

    def _btn_callback(self, state, pin):
        if state == 0:  # Button pressed
            self.transmitting = True
            print("sending transmission")
            self.led_snd.toggle()

            # add one-shot timer to control duration

            # self.led_send.on()
            # TODO: Set signal_out to PWM, 31kHz 50%
            # self.led_send.off()
            self.transmitting = False

    def _read_signal(self, pin):
        if not self.transmitting:
            print("transmission received")
            # blink led_rcv for 3s

        # add periodic timer to blink LED


class PowerTransfer:
    def __init__(self, gate_A_Pin, power_led_pin, freq=20_000, duty=0.5, dt_ns=500):
        self.active = False
        self.power_led = Pin(power_led_pin, Pin.OUT)
        self.pwm = CompPWM(gate_A_Pin, freq=freq, duty=duty, dt_ns=dt_ns)

    def start(self):
        self.active = True
        print("Power transfer started")
        led_main_conv.on()
        # Turn on PWM for gate drive signals

    def stop(self):
        self.active = False
        print("Power transfer stopped")
        led_main_conv.off()
        # Turn off PWM for gate drive signals

    def start_btn_callback(self, state, pin):
        if state == 0 and not self.active:  # Button pressed
            self.power_led.on()
            self.active = True
            print("Power transfer started")
            # Turn on PWM for gate drive signals

    def stop_btn_callback(self, state, pin):
        if state == 0 and self.active:  # Button pressed
            self.power_led.off()
            self.active = False
            print("Power transfer stopped")
            # Turn off PWM for gate drive signals
