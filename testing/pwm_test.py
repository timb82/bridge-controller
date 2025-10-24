from machine import Pin, PWM, mem32
from time import sleep, ticks_ms


class cpwm:
    def __init__(self, pinA, freq):
        # rely on micropython for initial config
        self.pwm_pin = PWM(Pin(pinA))
        self.pwm_pin.freq(freq * 2)  # edge freq = 2 * center-aligned
        self.pwm_pin.duty_u16(0)
        self.pwm_pin2 = PWM(Pin(pinA + 1))
        self.pwm_pin2.freq(freq * 2)  # edge freq = 2 * center-aligned
        self.pwm_pin2.duty_u16(0)

        # slice mapping 4.5.2 in datasheet
        self.slice_no = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)

        # reg addr section 4.5.3 in datasheet
        self.PWM_BASE = 0x40050000 + 20 * self.slice_no
        self.top = mem32[self.PWM_BASE + 16] + 1  # period top

    def duty(self, duty_pc, dt_ticks=0):
        dt_ticks = max(dt_ticks, 0)  # ensure non-zero
        duty = int(duty_pc * self.top)
        dutyH = duty & 0xFFFF
        dutymin = min(duty + dt_ticks, self.top)
        dutyL = (dutymin << 16) & 0xFFFF0000
        mem32[self.PWM_BASE + 0x3000 + 0x08] = 0xFFFF
        mem32[self.PWM_BASE + 0x2000 + 0x08] = (duty + 1) & 0xFFFF
        mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10  # invert output B, center-aligned
        mem32[self.PWM_BASE + 0x3000 + 0x08] = 0xFFFF
        mem32[self.PWM_BASE + 0x2000 + 0x08] = (duty + 1) & 0xFFFF
        mem32[self.PWM_BASE + 12] = dutyL + dutyH
        A, B = (reg := mem32[self.PWM_BASE + 0xC]) & 0xFFFF, reg >> 16
        print(
            f"duty_pc: {duty_pc}\tdutyH: {dutyH}\tdutyL: {dutymin}\tTOP: {self.top}\t CC:{mem32[self.PWM_BASE + 0x08] & 0xFFFF}"
        )


# PWM on GP8, GP9
pwm = cpwm(8, 10_000)

# # 8 ns per tick for deadtime
# # 63 ticks = 504 ns
pwm.duty(0.65, 1000)
# pwm = cpwm(8, 10)
BASE = pwm.PWM_BASE
SET_ALIAS = BASE + 0x2000
CLR_ALIAS = BASE + 0x3000


def reg(offset=0):
    return mem32[BASE + offset]


def split(reg):
    low = reg & 0xFFFF  # bits 15-0
    high = (reg >> 16) & 0xFFFF  # bits 31-16
    return low, high


def set_low_word(offset, value):
    # Clear then set low 16 bits using atomic aliases
    # Clear lower 16 bits
    mem32[CLR_ALIAS + offset] = 0xFFFF
    # Set new value (masked to 16 bits)
    mem32[SET_ALIAS + offset] = value & 0xFFFF


def on():
    mem32[SET_ALIAS] = 1


def off():
    mem32[CLR_ALIAS] = 1


def enabled():
    if reg() & 0x1:
        return True
    else:
        return False


def top(val=False):
    TOP = 0x10
    if val:
        set_low_word(TOP, val)

    else:
        return split(reg(TOP))[0]


def cc(val=False):
    CC = 0x0C
    if val:
        words = (val[1] << 16) | (val[0] & 0xFFFF)
        mem32[BASE + CC] = words
    else:
        return split(reg(CC))


def ctr(val=False):
    CTR = 0x08
    if val:
        set_low_word(CTR, val)
    else:
        return split(reg(CTR))[0]


def check_ctr(iterations=100):
    for i in range(iterations):
        print(ctr())


sleep(3)
pwm.pwm_pin.duty_u16(0)
pwm.pwm_pin2.duty_u16(0)
# try:
#     while True:
#         pass
# except KeyboardInterrupt:
#     pwm.duty(0, 0)
