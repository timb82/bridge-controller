from machine import Pin, I2C
import ssd1306
from utime import sleep, ticks_ms

SDA_PIN = 18
SCL_PIN = 19
BTN_PIN = 28
SENSOR_PIN = 20
LED_PIN = "LED"
DEBOUNCE_TIME = 250  # milliseconds


class Counter:
    def __init__(self):
        self.count = 0
        self.running = False

    def inc(self):
        if self.running:
            self.count += 1

    def reset(self):
        self.count = 0

    def get_count(self):
        return self.count

    def start(self):
        self.running = True

    def stop(self):
        self.running = False


class Display:
    def __init__(self, oled):
        self.oled = oled
        self.character_width = 8
        self.character_height = 8
        self.scale = 2

    def show_count(self, count):
        count = str(count)
        self.oled.fill(0)  # Clear the display
        self.oled_text_scaled("Count:", 20, 0)
        self.oled_text_scaled(count, 64 - len(count) * 5 * self.scale, 30)
        self.oled.text("<on>", 0, 54) if counter.running else self.oled.text(
            "<off>", 0, 54
        )
        self.oled.show()

    def oled_text_scaled(self, text, x, y):
        # temporary buffer for the text
        width = self.character_width * len(text)
        height = self.character_height
        temp_buf = bytearray(width * height)
        temp_fb = ssd1306.framebuf.FrameBuffer(
            temp_buf, width, height, ssd1306.framebuf.MONO_VLSB
        )

        # write text to the temporary framebuffer
        temp_fb.text(text, 0, 0, 1)

        # scale and write to the display
        for i in range(width):
            for j in range(height):
                pixel = temp_fb.pixel(i, j)
                if pixel:  # If the pixel is set, draw a larger rectangle
                    self.oled.fill_rect(
                        x + i * self.scale,
                        y + j * self.scale,
                        self.scale,
                        self.scale,
                        1,
                    )

    def fill_rect(self, x, y, width, height, color):
        self.oled.fill_rect(x, y, width, height, color)
        self.oled.show()


class Sensor:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.last_press_time = 0

        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_press)

    def handle_press(self, pin):
        current_time = ticks_ms()
        if current_time - self.last_press_time > DEBOUNCE_TIME:
            self.trigger()
            self.last_press_time = current_time

    def trigger(self):
        counter.inc()
        disp.show_count(counter.get_count())


class Button:
    def __init__(
        self,
        pin,
        short_click,
        long_press_dn=None,
        long_release_up=None,
        long_time_dn=3000,
        long_time_up=5000,
    ):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.short_click_callback = short_click
        self.long_press_dn_callback = long_press_dn
        self.long_release_up_callback = long_release_up
        self.long_time_dn = long_time_dn
        self.long_time_up = long_time_up
        self.last_press_time = 0
        self.pressed = False
        self.press_start_time = 0
        self.long_press_dn_fired = False

        self.pin.irq(
            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.handle_event
        )

    def handle_event(self, pin):
        current_time = ticks_ms()
        if pin.value() == 0:  # Button pressed (falling edge)
            # Debounce press
            if not self.pressed and (
                current_time - self.last_press_time > DEBOUNCE_TIME
            ):
                self.pressed = True
                self.last_press_time = current_time
                self.press_start_time = current_time
                self.long_press_dn_fired = False
        else:  # Button released (rising edge)
            if self.pressed:
                press_duration = current_time - self.press_start_time
                if press_duration >= self.long_time_up:
                    if self.long_release_up_callback:
                        self.long_release_up_callback()
                elif press_duration < self.long_time_dn:
                    if self.short_click_callback:
                        self.short_click_callback()
                # If between 3s and 5s, do nothing on release
                self.pressed = False
                self.last_press_time = current_time

    def poll(self):
        # Call this in the main loop to check for 3s long press
        if self.pressed and not self.long_press_dn_fired:
            current_time = ticks_ms()
            if current_time - self.press_start_time >= self.long_time_dn:
                self.long_press_dn_fired = True
                if self.long_press_dn_callback:
                    self.long_press_dn_callback()


def short_click():
    led.toggle()
    if led.value() == 1:
        counter.start()
    else:
        counter.stop()
    print(f"Running: {counter.running}")
    disp.show_count(counter.get_count())


def long_press_dn():
    print("RESET?")
    disp.fill_rect(0, 53, 128, 64, 0)  # Clear display's status line
    disp.oled.text("Hold to reset...", 0, 54, 1)
    disp.oled.show()
    led.off()
    counter.stop()
    for _ in range(9):
        led.toggle()
        sleep(0.25)
    led.off()
    disp.fill_rect(0, 53, 128, 64, 0)  # Clear display's status line
    disp.oled.text("Release button.", 0, 54, 1)
    disp.oled.show()

    # You can add any action here for 3s long press


def long_release_5s():
    counter.reset()
    led.off()
    disp.show_count(counter.get_count())


# Init interfaces
oled = ssd1306.SSD1306_I2C(128, 64, I2C(id=1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN)))
led = Pin(LED_PIN, Pin.OUT)
disp = Display(oled)
counter = Counter()
sensor = Sensor(SENSOR_PIN)
button = Button(BTN_PIN, short_click, long_press_dn, long_release_5s)

disp.show_count(counter.get_count())

while True:
    button.poll()
