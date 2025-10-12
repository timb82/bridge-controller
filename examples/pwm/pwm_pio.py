from machine import Pin
import rp2
import array


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def pwm_prog():
    wrap_target()
    pull(noblock)  # Get new period/duty cycle if available
    mov(x, osr)  # Transfer period value to x
    mov(y, isr)  # Transfer duty cycle value to y
    label("loop")
    jmp(y_dec, "high")  # Stay high for duty cycle count
    set(pins, 0)  # Set output low
    jmp("cont")
    label("high")
    set(pins, 1)  # Set output high
    label("cont")
    jmp(x_dec, "loop")  # Continue for period count
    wrap()


@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH)
def pwm_prog_inv():
    wrap_target()
    pull(noblock)  # Get new period/duty cycle if available
    mov(x, osr)  # Transfer period value to x
    mov(y, isr)  # Transfer duty cycle value to y
    label("loop")
    jmp(y_dec, "low")  # Stay low for duty cycle count
    set(pins, 1)  # Set output high
    jmp("cont")
    label("low")
    set(pins, 0)  # Set output low
    label("cont")
    jmp(x_dec, "loop")  # Continue for period count
    wrap()


@rp2.asm_pio()
def sync_prog():
    wrap_target()
    irq(0)  # Generate sync IRQ
    set(x, 31)  # Delay counter
    label("delay")
    jmp(x_dec, "delay")  # Simple delay
    wrap()


class PWMController:
    def __init__(self, pin1=16, pin2=17, freq=20000, duty=75):
        self.sm_pwm1 = rp2.StateMachine(0, pwm_prog, freq=125_000_000, set_base=Pin(pin1))
        self.sm_pwm2 = rp2.StateMachine(1, pwm_prog_inv, freq=125_000_000, set_base=Pin(pin2))
        self.sm_sync = rp2.StateMachine(2, sync_prog, freq=125_000_000)

        self.period = int(125_000_000 / freq)
        self.duty = int(self.period * duty / 100)

        # Configure PWM state machines
        self.sm_pwm1.put(self.period)
        self.sm_pwm1.exec("pull()")
        self.sm_pwm1.put(self.duty)
        self.sm_pwm1.exec("pull()")

        self.sm_pwm2.put(self.period)
        self.sm_pwm2.exec("pull()")
        self.sm_pwm2.put(self.duty)
        self.sm_pwm2.exec("pull()")

        # Set up IRQ handler
        self.sm_pwm1.irq(self.sync_handler)
        self.sm_pwm2.irq(self.sync_handler)

    def sync_handler(self, sm):
        # Restart PWM state machines on sync signal
        if not sm.rx_fifo():
            self.sm_pwm1.restart()
            self.sm_pwm2.restart()

    def start(self):
        self.sm_pwm1.active(1)
        self.sm_pwm2.active(1)
        self.sm_sync.active(1)

    def stop(self):
        self.sm_pwm1.active(0)
        self.sm_pwm2.active(0)
        self.sm_sync.active(0)

    def set_frequency(self, freq):
        self.period = int(125_000_000 / freq)
        self.duty = int(self.period * self.get_duty_cycle() / 100)
        self._update_pwm()

    def set_duty_cycle(self, duty):
        if 0 <= duty <= 100:
            self.duty = int(self.period * duty / 100)
            self._update_pwm()

    def get_frequency(self):
        return 125_000_000 / self.period

    def get_duty_cycle(self):
        return (self.duty * 100) / self.period

    def _update_pwm(self):
        self.stop()
        self.sm_pwm1.put(self.period)
        self.sm_pwm1.put(self.duty)
        self.sm_pwm2.put(self.period)
        self.sm_pwm2.put(self.duty)
        self.start()
