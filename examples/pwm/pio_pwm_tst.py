# pio_pwm.py
# Generates two 10kHz PWM signals using PIO with adjustable duty cycle and dead time
# Signal 2 is the inverted version of signal 1, with dead time between transitions

import time
from machine import Pin
import rp2

PWM_PINS = (16, 17)  # Define the pins for PWM output


# PIO program for a single PWM output
@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32)
def pwm():
    wrap_target()
    pull()
    mov(x, osr)
    pull()
    mov(y, osr)
    set(pins, 1)
    mov(isr, y)
    label("high")
    jmp(isr--, high)
    set(pins, 0)
    mov(isr, x)
    sub(isr, y)
    label("low")
    jmp(isr--, low)
    wrap()


# PIO program for inverted PWM with dead time
@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32)
def pwm_inv_dead():
    """
        pull()
        mov(x, osr)
        pull()
        mov(y, osr)
        pull()
        mov(z, osr)
        set(pins, 0)
        mov(isr, y)
    wait_high:
        jmp(isr--, wait_high)
        mov(isr, z)
    dead:
        jmp(isr--, dead)
        set(pins, 1)
        mov(isr, x)
        sub(isr, y)
        sub(isr, z)
    wait_low:
        jmp(isr--, wait_low)
        set(pins, 0)
        jmp(pwm_inv_dead)
    """


# Helper to calculate cycles for PIO
def calc_cycles(freq, duty, dead_time_us, sm_freq=125_000_000):
    period = int(sm_freq // freq)
    high_time = int(period * duty)
    dead_time = int((dead_time_us * sm_freq) // 1_000_000)
    if high_time + dead_time > period:
        dead_time = period - high_time
    return period, high_time, dead_time


class DualPWM:
    def __init__(self, pin1, pin2, freq=10_000, duty=0.5, dead_time_us=1):
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin2 = Pin(pin2, Pin.OUT)
        self.freq = freq
        self.duty = duty
        self.dead_time_us = dead_time_us
        self.sm_freq = 125_000_000  # PIO clock (default)
        # Use default frequency (system clock) for PIO, set freq after creation if needed
        self.sm1 = rp2.StateMachine(0, pwm, out_base=self.pin1)
        self.sm2 = rp2.StateMachine(1, pwm_inv_dead, out_base=self.pin2)
        # Set frequency if supported
        try:
            self.sm1.freq(self.sm_freq)
            self.sm2.freq(self.sm_freq)
        except AttributeError:
            pass  # Some MicroPython builds set freq at creation
        self.update(self.freq, self.duty, self.dead_time_us)
        self.sm1.active(1)
        self.sm2.active(1)

    def update(self, freq=None, duty=None, dead_time_us=None):
        if freq is not None:
            self.freq = freq
        if duty is not None:
            self.duty = duty
        if dead_time_us is not None:
            self.dead_time_us = dead_time_us
        period, high_time, dead_time = calc_cycles(
            self.freq, self.duty, self.dead_time_us, self.sm_freq
        )
        # Update both state machines
        self.sm1.put(period)
        self.sm1.put(high_time)
        self.sm2.put(period)
        self.sm2.put(high_time)
        self.sm2.put(dead_time)

    def deinit(self):
        self.sm1.active(0)
        self.sm2.active(0)


# Example usage
if __name__ == "__main__":
    pwm = DualPWM(
        pin1=PWM_PINS[0], pin2=PWM_PINS[1], freq=10_000, duty=0.5, dead_time_us=2
    )
    try:
        duty_values = [0.25, 0.5, 0.75]
        idx = 0
        while True:
            pwm.update(duty=duty_values[idx])
            idx = (idx + 1) % len(duty_values)
            time.sleep(3)
    except KeyboardInterrupt:
        pwm.deinit()
