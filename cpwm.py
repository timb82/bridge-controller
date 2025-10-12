# https://tahmidmc.blogspot.com/2024/07/generating-complementary-pwm-with.html
from machine import Pin, PWM, mem32, freq
from time import sleep, ticks_ms
from math import ceil

# slice mapping 4.5.2 in datasheet
PWM_BASE = 0x40050000  # Base address of PWM peripheral
PWM_CHAN_OFFSET = 0x14  # Offset between slices (each slice = 20 bytes = 0x14)
PIN_A = 16


class CompPWM:
    """Complementary PWM on Pin A and Pin A+1 with dead time
    Args:
        PinA (int): GPIO for channel A PWM, must be even and between 0 and 28; channel B is always PinA+1
        freq (int): Frequency in Hz, default 10_000
        duty (float): Duty cycle as a fraction (0.0 to 1.0), default 0.5
        dt_ns (int): Dead time in nanoseconds, default 500ns
    """

    # TODO test pwm.deinint
    # TODO test changing freq on the fly
    # TODO test changing duty on the fly
    # TODO test changing deadtime on the fly
    # TODO add error checks for pin, freq, duty, dt
    # TODO implement pin change
    def __init__(self, pinA, freq=10_000, duty=0.5, dt_ns=500):
        self._slice_num = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)
        self._slice_base = PWM_BASE + self._slice_num * PWM_CHAN_OFFSET
        # PREINIT for setters
        self._running = False
        self._pin = None
        self._freq = None
        self._duty = None
        self._dt_ticks = 63  # dead time in ticks
        self._dt_ns = 504  # for default f_sys=125MHz and clkdiv=1.0
        # STORE ARGS
        self.pin = pinA
        self.freq = freq
        self.dt_ns = dt_ns  # dead time in ns
        self.duty = duty

        # INIT PWM

        self.top = mem32[self._slice_base + 16] + 1  # period top
        mem32[self._slice_base] = mem32[self._slice_base] | 10  # invert output B, center-aligned
        # self.start()

    def start(self):
        mem32[self._slice_base] = mem32[self._slice_base] | 1  # enable PWM
        self._running = True

    def stop(self):
        mem32[self._slice_base] = mem32[self._slice_base] & ~1  # disable PWM
        self._running = False

    @property
    def running(self):
        """Determines if the PWM is running or not"""
        return self._running

    @running.setter
    def running(self, value):
        if value and not self._running:
            self.start()
        elif not value and self._running:
            self.stop()

    @property
    def pin(self):
        """set up Pin A and Pin A+1 for complementary PWM

        Pin number must be even and between 0 and 28
        Pin change is not implemented"""
        return self._pin

    @pin.setter
    def pin(self, value):
        if self._pin is None:
            if value < 0 or value > 28 or (value % 2) != 0:
                raise ValueError("Pin_A number must be even and between 0 and 28")
            self._pin = value
            self.pwmA = PWM(Pin(self._pin))
            self.pwmB = PWM(Pin(self._pin + 1))
        else:
            raise NotImplementedError("Pin change not implemented")

    @property
    def freq(self):
        """Frequency in Hz
        Note: freq is doubled internally for center-aligned mode
        after setting freq, reapply duty and dead time to update registers in case clkdiv or top changed"""
        return int(self._freq / 2)

    @freq.setter
    def freq(self, freq_hz):
        running = self._running  # save state
        if running:
            self.stop()

        self._freq = int(2 * freq_hz)
        self.pwmA.freq(self._freq)
        self.pwmB.freq(self._freq)
        self._top = mem32[self._slice_base + 0x10] + 1
        self.dt_ns = self.dt_ns  # reapply dead time (updates ticks for new clkdiv)
        # TODO check if i need to reapply duty here
        if self.duty is not None:
            self.duty = self.duty  # reapply duty (updates compare regs for new top)

        if running:
            self.start()

    @property
    def dt_ns(self):
        """Dead time in nanoseconds
        Number of PWM clock ticks is evaluated and actual dead time is set based on clock divider and system fre"""
        return self._dt_ns

    @dt_ns.setter
    def dt_ns(self, dt_ns):
        # reg addr section 4.5.3 in datasheet
        DIV_REG = 0x04  # Clock divider register
        div_raw = mem32[self._slice_base + DIV_REG]
        clkdiv = float((div_raw >> 4) & 0xFF) + (div_raw & 0x0F) / 16.0
        clktick_ns = clkdiv / (freq() / 1e9)  # ns per tick

        self._dt_ticks = ceil(dt_ns / clktick_ns)  # number of dead time ticks
        self._dt_ns = clktick_ns * self._dt_ticks  # actual dead time in ns

    @property
    def duty(self):
        """Duty cycle as a fraction (0.0 to 1.0)
        Duty cycle is applied to output A, output B is complementary with dead time.
        PWM runs in center-aligned mode, therefore deadtime is added to both edges of the B pulse."""
        return self._duty

    @duty.setter
    def duty(self, duty):
        self._duty = min(max(duty, 0.0), 1.0)  # clamp to 0.0-1.0
        # top = mem32[self._slice_base + 0x10] + 1
        dt_ticks = max(self._dt_ticks, 0)  # ensure non-zero
        duty_ticks = int(self._duty * self._top)
        dutyH = duty_ticks & 0xFFFF
        dutymin = min(duty_ticks + dt_ticks, self._top)
        dutyL = (dutymin << 16) & 0xFFFF0000
        mem32[self._slice_base + 0x0C] = dutyL + dutyH

    def __str__(self):
        """Returns current configuration"""
        return f"Pin A: {self.pin}, Pin B: {self.pin+1}, Freq: {self.freq}Hz, Duty: {self.duty:.4f}, Dead time: {self.dt_ns:.1f}ns ({self._dt_ticks} ticks), Running: {self.running}"


# class cpwm:
#     def __init__(self, pinA, freq):
#         # rely on micropython for initial config
#         pwm_pin = PWM(Pin(pinA))
#         pwm_pin.freq(freq * 2)  # double freq for center aligned mode (datasheet 4.5.2.1)
#         pwm_pin.duty_u16(0)
#         pwm_pin = PWM(Pin(pinA + 1))
#         pwm_pin.duty_u16(0)
#         pwm_pin.freq(freq * 2)  # double freq for center aligned mode
#         # slice mapping 4.5.2 in datasheet
#         slice_num = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)

#         # reg addr section 4.5.3 in datasheet
#         self.PWM_BASE = 0x40050000 + 20 * slice_num  # CHx_CSR address
#         self.top = mem32[self.PWM_BASE + 16] + 1  # period top
#         # Modify CSR: Enable phase-correct (center-aligned) mode, invert B output
#         mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10

#     def duty(self, duty_pc, dt_ticks=0):
#         dt_ticks = max(dt_ticks, 0)  # ensure non-zero
#         duty = int(duty_pc * self.top)
#         dutyH = duty & 0xFFFF
#         dutymin = min(duty + dt_ticks, self.top)
#         dutyL = (dutymin << 16) & 0xFFFF0000
#         mem32[self.PWM_BASE + 12] = dutyL + dutyH


pwm = CompPWM(PIN_A, 10_000)
print(pwm)
