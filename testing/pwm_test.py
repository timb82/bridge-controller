from machine import Pin, PWM, mem32
from time import sleep, ticks_ms


class cpwm:
    def __init__(self, pinA, freq):
        # rely on micropython for initial config
        pwm_pin = PWM(Pin(pinA))
        pwm_pin.freq(freq * 2)  # edge freq = 2 * center-aligned
        pwm_pin.duty_u16(0)
        pwm_pin = PWM(Pin(pinA + 1))
        pwm_pin.freq(freq * 2)  # edge freq = 2 * center-aligned
        pwm_pin.duty_u16(0)

        # slice mapping 4.5.2 in datasheet
        self.slice_no = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)

        # reg addr section 4.5.3 in datasheet
        self.PWM_BASE = 0x40050000 + 20 * self.slice_no
        self.top = mem32[self.PWM_BASE + 16] + 1  # period top
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10  # invert output B, center-aligned

    def duty(self, duty_pc, dt_ticks=0):
        dt_ticks = max(dt_ticks, 0)  # ensure non-zero
        duty = int(duty_pc * self.top)
        dutyH = duty & 0xFFFF
        dutymin = min(duty + dt_ticks, self.top)
        dutyL = (dutymin << 16) & 0xFFFF0000
        mem32[self.PWM_BASE + 12] = dutyL + dutyH
        A, B = (reg := mem32[self.slice_no + 0xC]) & 0xFFFF, reg >> 16
        print(
            f"duty_pc: {duty_pc}\tdutyH: {dutyH}\tdutyL: {dutymin}\tTOP: {self.top}\t CC:{mem32[self.slice_no + 0x08] & 0xFFFF}"
        )


# PWM on GP8, GP9
pwm = cpwm(8, 10_000)

# 8 ns per tick for deadtime
# 63 ticks = 504 ns
pwm.duty(0.65, 630)

try:
    while True:
        pass
except KeyboardInterrupt:
    pwm.duty(0, 0)
