from machine import Pin, SPI
import machine
import st7789
import vga1_16x32 as font32
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

up = Pin(3, Pin.IN, Pin.PULL_UP)
down = Pin(23, Pin.IN, Pin.PULL_UP)
left = Pin(2, Pin.IN, Pin.PULL_UP)
sel = Pin(15, Pin.IN, Pin.PULL_UP)

menu = ["bluetooth_jammer", "ble_spectrum"]
selected = 0
old_selected = -1

def drawmenu(menu, selected):
    tft.fill(st7789.BLACK)
    tft.text(font32, "BLE TOOLS:", 80, 10, st7789.GREEN)
    tft.text(font816, "kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)
    for index, item in enumerate(menu):
        y = 60 + index * 36
        if index == selected:
            tft.text(font32, item, 20, y, st7789.WHITE)
            tft.rect(10, y - 4, 270, 40, st7789.BLUE)
        else:
            tft.text(font32, item, 20, y, st7789.WHITE)
    
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
        
    if left.value() == 0:
        machine.reset()
        
        while up.value() == 0:
            time.sleep_ms(10)
         
    time.sleep_ms(10)


