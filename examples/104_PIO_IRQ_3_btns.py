from rp2 import PIO, asm_pio, StateMachine
from machine import Pin
from time import sleep_ms as sleep


BTN_PINS = [11, 12, 13]
LED_PINS = [18, 19, 20]
PIN_BTN_G = 11
PIN_BTN_Y = 12
PIN_BTN_R = 13
PIN_LED_G = 18
PIN_LED_Y = 19
PIN_LED_R = 20

buttons = []
leds = []
sm_list = []


@asm_pio()
def btn_irq():
    wrap_target()
    wait(1, pin, 0)
    nop()[31]
    nop()[31]
    nop()[31]
    nop()[31]
    irq(block, 0)
    wait(0, pin, 0)
    nop()[31]
    nop()[31]
    nop()[31]
    nop()[31]
    wrap()


@asm_pio(out_init=PIO.OUT_LOW)
def led_control():
    set(x, 0b00000)
    wrap_target()
    wait(1, irq, 0)
    mov(x, invert(x))
    mov(pins, x)
    irq(clear, 0)
    wrap()


def btn_handler(sm):
    led0.value(not led0.value())
    print(sm)


btn0 = Pin(BTN_PINS[0], Pin.IN, Pin.PULL_DOWN)
led0 = Pin(LED_PINS[0], Pin.OUT)
sm0 = StateMachine(6, btn_irq, freq=2000, in_base=btn0)
sm0.irq(btn_handler)
sm0.active(1)

# for i in range(3):
#     buttons.append(Pin(BTN_PINS[i], Pin.IN, Pin.PULL_DOWN))
#     leds.append(Pin(LED_PINS[i], Pin.OUT))
#     # sm_list.append(StateMachine(i, btn_irq, freq=2000, in_base=buttons[i]))
#     # sm_list[i].irq(button_handler)
#     # sm_list[i].active(1)

# sm_btn = StateMachine(0, btn_irq, freq=2000, in_base=buttons[0])
# sm_led = StateMachine(1, led_control, freq=2000, out_base=leds[0])

# sm_btn.active(1)
# sm_led.active(1)


# btn_grn = Pin(PIN_BTN_G, Pin.IN, Pin.PULL_DOWN)
# led_grn = Pin(PIN_LED_G, Pin.OUT)
# sm_btn_gr = StateMachine(0, btn_irq, freq=2000, in_base=btn_grn)
# sm_btn_gr.irq(button_handler)
# sm_btn_gr.active(1)


while True:
    pass
