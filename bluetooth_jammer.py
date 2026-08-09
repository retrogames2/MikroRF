import st7789
from machine import Pin, SPI
import vga1_16x32 as font32
import vga1_8x16 as font8
import machine

spi = SPI(
    1,
    baudrate=20000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    mosi=Pin(19)
)

tft = st7789.ST7789(
    spi,
    240,
    320,
    reset=Pin(20, Pin.OUT),
    dc=Pin(21, Pin.OUT),
    cs=Pin(22, Pin.OUT),
    rotation=1
)

def draw_ble():
    tft.text(font32, "/", 122, 150, st7789.WHITE)
    tft.text(font32, "\\", 122, 120, st7789.WHITE)
    tft.text(font32, "|", 135, 150, st7789.WHITE)
    tft.text(font32, "|", 135, 120, st7789.WHITE)
    tft.text(font32, "|", 135, 100, st7789.WHITE)
    tft.text(font32, "|", 135, 170, st7789.WHITE)
    tft.text(font32, "/", 147, 170, st7789.WHITE)
    tft.text(font32, "\\", 145, 150, st7789.WHITE)
    tft.text(font32, "/", 147, 120, st7789.WHITE)
    tft.text(font32, "\\", 145, 100, st7789.WHITE)

tft.fill(st7789.BLACK)
tft.text(font32, "Jammer BLE:", 80, 20, st7789.WHITE)
tft.text(font32, "Wylaczony", 80, 56, st7789.GREEN)
tft.text(font8, "Kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)
draw_ble()

button = Pin(15, Pin.IN, Pin.PULL_UP)
output = Pin(1, Pin.OUT)
left = Pin(2, Pin.IN, Pin.PULL_UP)

state = 0

while True:
    if button.value() == 0:
        state = not state
        output.value(state)
        if state == 1:
            tft.fill(st7789.BLACK)
            tft.text(font32, "Jammer BLE:", 80, 20, st7789.WHITE)
            tft.text(font32, "Atakowanie", 80, 56, st7789.RED)
            tft.text(font32, "(!)", 165, 135, st7789.RED)
            tft.text(font8, "Kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)
            draw_ble()
        else:
            tft.fill(st7789.BLACK)
            tft.text(font32, "Jammer BLE:", 80, 20, st7789.WHITE)
            tft.text(font32, "Wylaczony", 80, 56, st7789.GREEN)
            tft.text(font8, "Kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)
            draw_ble()

        while button.value() == 0:
            pass
        
    if left.value() == 0:
                machine.reset()
        
                while up.value() == 0:
                    time.sleep_ms(10)