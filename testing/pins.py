from machine import Pin, PWM
from time import sleep

pin = Pin(8, Pin.OUT)
pwm = PWM(pin)
sleep(1)
pwm.freq(10000)
sleep(1)
pwm.duty_u16(32768)
sleep(3)
pwm.duty_u16(0)
