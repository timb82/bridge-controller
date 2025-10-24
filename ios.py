from machine import Pin, PWM, Timer
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
        self.signal_in = Pin(read_pin, Pin.IN, pull=Pin.PULL_DOWN)
        self.signal_in.irq(trigger=Pin.IRQ_RISING, handler=self._read_signal)
        self._last_trigger_time = 0
        self._receiver_timer: None | Timer = None
        self._transmitter_timer: None | Timer = None

    def _btn_callback(self, state, pin):
        if state == 0 and self.comm_free():  # Button pressed
            self._transmitter_timer = Timer(-1)
            self._transmitter_timer.init(mode=Timer.ONE_SHOT, period=2000, callback=self._stop_transmission)
            self.led_snd.on()
            self.signal_out.duty_u16(32768)  # 50% duty cycle
            print("transmitting...")

    def _stop_transmission(self, t):
        self.led_snd.off()
        self.signal_out.duty_u16(0)
        assert self._transmitter_timer is not None
        self._transmitter_timer.deinit()
        self._transmitter_timer = None
        print("transmission complete!")

    def _read_signal(self, pin):
        if self.comm_free():  # Only process if not already transmitting or receiving
            self._receiver_timer = Timer(-1)
            self._receiver_timer.init(mode=Timer.ONE_SHOT, period=3000, callback=self._stop_reception)
            self.led_rcv.on()
            print("transmission received")

    def _stop_reception(self, t):
        self.led_rcv.off()
        assert self._receiver_timer is not None
        self._receiver_timer.deinit()
        self._receiver_timer = None
        print("reception complete!")

    def comm_free(self):
        if self._receiver_timer is None and self._transmitter_timer is None:
            return True
        else:
            return False


class PowerTransfer:
    def __init__(self, gate_A_Pin, power_led_pin, freq=20_000, duty=0.5, dt_ns=500):
        self.active = False
        self.power_led = Pin(power_led_pin, Pin.OUT)
        self.dual_pwm = CompPWM(gate_A_Pin, freq=freq, duty=duty, dt_ns=dt_ns)

    def start(self):
        self.active = True
        # Turn on PWM for gate drive signals
        self.power_led.on()
        print("Power transfer started")

    def stop(self):
        self.active = False
        # Turn off PWM for gate drive signals
        self.power_led.off()
        print("Power transfer stopped")

    def start_btn_callback(self, state, pin):
        if state == 0 and not self.active:  # Button pressed
            self.start()

    def stop_btn_callback(self, state, pin):
        if state == 0 and self.active:  # Button pressed
            self.stop()
