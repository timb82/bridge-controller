# https://tahmidmc.blogspot.com/2024/07/generating-complementary-pwm-with.html
from machine import Pin, PWM, mem32, freq
from math import ceil

# slice mapping 4.5.2 in datasheet
PWM_BASE = 0x40050000  # Base address of PWM peripheral
PWM_CHAN_OFFSET = 0x14  # Offset between slices (each slice = 20 bytes = 0x14)


class CompPWM:
    """Complementary PWM on Pin A and Pin A+1 with dead time
    Args:
        PinA (int): GPIO for channel A PWM, must be even and between 0 and 28; channel B is always PinA+1
        freq (int): Frequency in Hz, default 10_000
        duty (float): Duty cycle as a fraction (0.0 to 1.0), default 0.5
        dt_ns (int): Dead time in nanoseconds, default 500ns
    """

    # TODO test pwm.deinint
    # TODO add changing freq on the fly
    # TODO test changing duty on the fly
    # TODO test changing dead time on the fly
    # TODO add error checks for pin, freq, duty, dt
    # TODO implement pin change
    def __init__(self, pin_base, freq=10_000, duty=0.5, dt_ns=500):
        self._running = False
        self._pin_base = pin_base
        self._duty = min(max(duty, 0.0), 1.0)
        self._freq = 2 * freq
        self._dt_ns = dt_ns

        if type(self._pin_base) is int or 0 < self._pin_base < 29 or (self._pin_base % 2) == 0:
            self._slice_num = (pin_base >> 1) if pin_base < 16 else ((pin_base - 16) >> 1)
            self._slice_base = PWM_BASE + self._slice_num * PWM_CHAN_OFFSET
            self._pinA = Pin(pin_base, Pin.OUT)
            self._pinB = Pin(pin_base + 1, Pin.OUT)
            self.pwmA = PWM(self._pinA)
            # self.pwmA.duty_u16(0)
            self.pwmB = PWM(self._pinB)
            # self.pwmB.duty_u16(0)
            # self.top = mem32[self._slice_base + 16] + 1  # period top register
            # self.pwm_setup()
        else:
            raise ValueError(f"pin_base:{self._pin_base} number must be even number between 0 and 28")

    def pwm_setup(self):
        mem32[self._slice_base] = mem32[self._slice_base] | 10  # invert output B, center-aligned
        self.dt_ns = self._dt_ns  # dead time in ns
        self.freq = self._freq  # PWM frequency
        mem32[self._slice_base] = mem32[self._slice_base] | 10  # invert output B, center-aligned
        self.duty = self._duty  # duty cycle as fraction (0.0-1.0)

    def start(self):
        self.pwm_setup()
        mem32[self._slice_base] = mem32[self._slice_base] | 1  # enable PWM
        self._running = True

    def stop(self):
        mem32[self._slice_base] = mem32[self._slice_base] & ~1  # disable PWM
        # All PWM pins off!!!
        self.pwmA.duty_u16(0)
        self.pwmB.duty_u16(0)
        self._running = False

    def id(self, pin):
        """retun GPIO number of pin"""
        return int(str(pin)[4:-1].split(",")[0][4:])  # extract GPIO number from Pin

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
    def freq(self):
        """Frequency in Hz
        Note: freq is doubled internally for center-aligned mode
        after setting freq, reapply duty and dead time to update registers in case clkdiv or top changed"""
        if self._freq is None:
            return None
        else:
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
            self.duty = self.duty  # reapply duty (updates compare registers for new top)

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
        PWM runs in center-aligned mode, therefore dead time is added to both edges of the B pulse."""
        return self._duty

    @duty.setter
    def duty(self, duty):
        self._duty = min(max(duty, 0.0), 1.0)  # clamp to 0.0-1.0
        dt_ticks = max(self._dt_ticks, 1)  # ensure non-zero dead time
        duty_ticks = int(self._duty * self._top)
        dutyH = duty_ticks & 0xFFFF
        dutymin = min(duty_ticks + dt_ticks, self._top)
        dutyL = (dutymin << 16) & 0xFFFF0000
        mem32[self._slice_base + 0x0C] = dutyL + dutyH
        reg_CTR = mem32[self._slice_base + 0x08]

    def __str__(self):
        """Returns current configuration"""
        return f"Pin A: {self.id(self._pinA)}, Pin B: {self.id(self._pinB)}, Freq: {self.freq}Hz, Duty: {self.duty:.4f}, Dead time: {self.dt_ns:.1f}ns ({self._dt_ticks} ticks), Running: {self.running}"


if __name__ == "__main__":
    from time import sleep

    PIN_A = 8  # Example pin for testing, PIN_B = PIN_A + 1
    try:
        # print("Initialize PWM...")
        pwm = CompPWM(PIN_A, 10_000, duty=0.66, dt_ns=5000)
        # print(pwm)
        # print("PWM on standby...")
        # sleep_us(30)
        pwm.start()
        print("PWM running")
        while True:
            pass
            sleep(2)
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pwm.stop()
        print("Stopped by user")
