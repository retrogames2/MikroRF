from machine import Pin, SPI
import st7789
import vga1_16x32 as font32
import vga1_8x8 as font8
import vga1_16x16 as font16
import vga1_8x16 as font816
import time

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

tft.fill(st7789.BLACK)

tft.text(font32, "MikroRF", 110, 120, st7789.GREEN)
tft.text(font16, "o", 140, 90, st7789.WHITE)
tft.text(font8, ")", 160, 96, st7789.WHITE)
tft.text(font16, ")", 165, 90, st7789.WHITE)
tft.text(font32, ")", 175, 83, st7789.WHITE)
tft.text(font816, "Micro Hacking Device", 80, 160, st7789.WHITE)
tft.text(font8, "by @MikroTechnika", 0, 230, st7789.WHITE)
time.sleep(1.5)

tft.fill(st7789.BLACK)

up = Pin(3, Pin.IN, Pin.PULL_UP)
down = Pin(23, Pin.IN, Pin.PULL_UP)
sel = Pin(15, Pin.IN, Pin.PULL_UP)

menu = ["rf433", "ir", "bluetooth_tools", "wifi_tools", "nfc"]
selected = 0
old_selected = -1

def drawmenu(menu, selected):
    tft.fill(st7789.BLACK)
    tft.text(font32, "Wybierz Narzedzie:", 20, 10, st7789.GREEN)
    for index, item in enumerate(menu):
        y = 60 + index * 36
        if index == selected:
            tft.text(font32, item, 60, y, st7789.WHITE)
            tft.rect(50, y - 4, 260, 40, st7789.BLUE)
        else:
            tft.text(font32, item, 60, y, st7789.WHITE)
    
while True:
    if up.value() == 0:
        selected -= 1
        
        while up.value() == 0:
            time.sleep_ms(10)
    
    if down.value() == 0:
        selected += 1
        
        while down.value() == 0:
            time.sleep_ms(10)
    
    if sel.value() == 0:
        while sel.value() == 0:
            time.sleep_ms(10)
            
        tft.fill(st7789.BLACK)
        exec(open(menu[selected] + ".py").read())
        break
            
    if selected > len(menu) - 1:
        selected = 0
        
    if selected < 0:
        selected = len(menu) - 1
        
    if selected != old_selected:    
        drawmenu(menu, selected)
        old_selected = selected
         
    time.sleep_ms(10)