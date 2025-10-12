# https://tahmidmc.blogspot.com/2024/07/generating-complementary-pwm-with.html
from machine import Pin, PWM, mem32
from time import sleep, ticks_ms


class CompPWM:
    def __init__(self, pinA, freq=10_000, duty_pc=0.5, dt=1000):
        self.pwmA = PWM(Pin(pinA))
        self.pwmB = PWM(Pin(pinA + 1))
        self.freq(2 * freq)  # double freq for center-aligned mode
        self.duty_pc = (duty_pc,)
        self.dt = dt  # dead time in ns
        pwmA = PWM(Pin(pinA))
        pwmB = PWM(Pin(pinA + 1))

        # slice mapping 4.5.2 in datasheet
        slice_num = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)
        # reg addr section 4.5.3 in datasheet
        self.PWM_BASE = 0x40050000 + 20 * slice_num

        self.top = mem32[self.PWM_BASE + 16] + 1  # period top
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10  # invert output B, center-aligned


class cpwm:
    def __init__(self, pinA, freq):
        # rely on micropython for initial config
        pwm_pin = PWM(Pin(pinA))
        pwm_pin.freq(freq * 2)  # double freq for center aligned mode (datasheet 4.5.2.1)
        pwm_pin.duty_u16(0)
        pwm_pin = PWM(Pin(pinA + 1))
        pwm_pin.duty_u16(0)
        pwm_pin.freq(freq * 2)  # double freq for center aligned mode
        # slice mapping 4.5.2 in datasheet
        slice_num = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)

        # reg addr section 4.5.3 in datasheet
        self.PWM_BASE = 0x40050000 + 20 * slice_num  # CHx_CSR address
        self.top = mem32[self.PWM_BASE + 16] + 1  # period top
        # Modify CSR: Enable phase-correct (center-aligned) mode, invert B output
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10

    def start(self):
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 1  # enable PWM

    def stop(self):
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] & ~1  # disable PWM

    # TODO add deadtime calculation based on machine frequency and dividers

    # TODO update duty cycle - adapt the original code
    def duty(self, duty_pc, dt_ticks=0):
        dt_ticks = max(dt_ticks, 0)  # ensure non-zero
        duty = int(duty_pc * self.top)
        dutyH = duty & 0xFFFF
        dutymin = min(duty + dt_ticks, self.top)
        dutyL = (dutymin << 16) & 0xFFFF0000
        mem32[self.PWM_BASE + 12] = dutyL + dutyH

    # TODO update pwm frequency


# PWM on GP16, GP17
pwm16 = cpwm(16, 10_000)

# 8 ns per tick for deadtime
# 63 ticks = 504 ns
pwm16.duty(0.25, 63)

while True:
    pass
