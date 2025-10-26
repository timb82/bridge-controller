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
        self.a = Pin(0, Pin.IN, Pin.PULL_UP)
        self.b = Pin(1, Pin.IN, Pin.PULL_UP)

        # slice mapping 4.5.2 in datasheet
        self.slice_no = (pinA >> 1) if pinA < 16 else ((pinA - 16) >> 1)

        # reg addr section 4.5.3 in datasheet
        self.PWM_BASE = 0x40050000 + 20 * self.slice_no
        self.top = mem32[self.PWM_BASE + 16] + 1  # period top

    def duty(self, duty_pc, dt_ticks=0):
        self.CC = 0x0C  # Counter compare register offset
        self.CTR = 0x8  # Counter value register offset
        self.TOP = 0x10  # Counter TOP refister offset
        self.SET_ALIAS = self.PWM_BASE + 0x2000
        self.CLR_ALIAS = self.PWM_BASE + 0x3000

        dt_ticks = max(dt_ticks, 0)  # ensure non-zero
        duty = int(duty_pc * self.top)
        dutyH = duty & 0xFFFF
        dutymin = min(duty + dt_ticks, self.top)
        dutyL = (dutymin << 16) & 0xFFFF0000

        self.status("init           ")
        self.off()
        self.status("counter off    ")

        # mem32[self.PWM_BASE + 0x2000 + self.CC] = 0xFFFFFF << 16
        # mem32[self.PWM_BASE + 0x3000 + self.CC] = 0xFFFFFF
        # self.status("CC pre-set     ")

        # mem32[self.PWM_BASE] = mem32[self.PWM_BASE] | 10  # invert output B, center-aligned
        # self.status("Center mode set")

        self.set_low_word(self.CTR, duty + 1)  # move counter to dead time
        self.status("CTR value set  ")

        mem32[self.PWM_BASE + self.CC] = dutyL + dutyH
        self.status("CC values  set")

        self.on()
        self.status("Counter on    ")

    def get_reg(self, offset=0):
        register = mem32[self.PWM_BASE + offset]
        return (register & 0xFFFF, (register >> 16) & 0xFFFF)

    def set_low_word(self, offset, value):
        # Clear then set low 16 bits using atomic aliases
        # Clear lower 16 bits
        mem32[self.CLR_ALIAS + offset] = 0xFFFF
        # Set new value (masked to 16 bits)
        mem32[self.SET_ALIAS + offset] = value & 0xFFFF

    def is_enabled(self):
        if self.get_reg()[0] & 0x1:
            return True
        else:
            return False

    def on(self):
        mem32[self.SET_ALIAS] = 0b1011

    def off(self):
        mem32[self.CLR_ALIAS] = 0b1011

    def status(self, str=""):
        print(
            f"{str}\t\tPWM enabled? - {self.is_enabled()}\tChan A, B: {self.a.value(), self.b.value()}\tCTR: {self.get_reg(self.CTR)[0]}\tTOP: {self.get_reg(self.TOP)[0]}\tCC: {self.get_reg(self.CC)}"
        )


# PWM on GP8, GP9
pwm = cpwm(8, 10_000)
# # 8 ns per tick for deadtime
# # 63 ticks = 504 ns
pwm.duty(0.5, 800)
pwm.status("PWM running...")


sleep(3)
pwm.status("PWM running...")
pwm.off()
pwm.pwm_pin.duty_u16(0)
pwm.pwm_pin2.duty_u16(0)
print("PWM off")
