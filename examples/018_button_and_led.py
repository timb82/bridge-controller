from machine import Pin
from utime import sleep_ms

LED_PIN = 10
BTN_PIN = 22

b_old = 1
b_new = 1

btn = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)
led.off()

while True:
    try:
        b_new = btn.value()
        if b_new is 0 and b_old is 1:
            print("Button down!")
            led.toggle()
        if b_new is 1 and b_old is 0:
            print("Button up!")
        b_old = btn.value()
        sleep_ms(50)
    except KeyboardInterrupt:
        print("bye")
        led.off()
        break
