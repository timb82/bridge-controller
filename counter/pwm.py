from machine import Pin, PWM
import time

# Set up PWM on Pin 16 (change as needed)
pwm_pin = PWM(Pin(16))
pwm_pin.freq(5_000_000)  # 20kHz


def set_duty_cycle(percent):
    # percent: 0 to 100
    duty = int(65535 * percent / 100)
    pwm_pin.duty_u16(duty)


# Example: Sweep duty cycle from 0% to 100%
set_duty_cycle(75)
while True:
    pass
    # for dc in range(0, 101, 5):
    #     set_duty_cycle(dc)
    #     time.sleep(2)
    # for dc in range(100, -1, -5):
    #     set_duty_cycle(dc)
    #     time.sleep(2)
