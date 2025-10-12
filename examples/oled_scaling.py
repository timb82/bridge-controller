from machine import SoftI2C, Pin
import time
import ssd1306

OLED_SCL_PIN = 15  # clock
OLED_SDA_PIN = 14  # data
OLED_WIDTH = 128  # pixels
OLED_HEIGHT = 64  # pixels


def oled_text_scaled(oled, text, x, y, scale, character_width=8, character_height=8):
    # temporary buffer for the text
    width = character_width * len(text)
    height = character_height
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
                oled.fill_rect(x + i * scale, y + j * scale, scale, scale, 1)


def main():
    i2c = SoftI2C(scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

    # no scaling
    oled.fill(0)
    oled.text("ABCDEFGHIJKLMNOP", 0, 0)
    oled.text("abcdefghijklmnop", 0, 8)
    oled.text("0123456789012345", 0, 16)
    oled.text('=!"#$%&/()?-+*:;', 0, 24)
    oled.show()
    time.sleep(3)

    # 2x
    oled.fill(0)
    oled_text_scaled(oled, "ABCDEFGH", 0, 0, 2)
    oled_text_scaled(oled, "abcdefgh", 0, 16, 2)
    oled.show()
    time.sleep(3)

    # 4x
    oled.fill(0)
    oled_text_scaled(oled, "ABCD", 0, 0, 4)
    oled.show()
    time.sleep(3)


if __name__ == "__main__":
    main()
