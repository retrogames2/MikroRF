from machine import Pin, I2C, SPI
from pn532 import PN532_I2C
import time
import st7789
import machine
import vga1_16x16 as font8
import vga1_8x16 as font16

# =========================
# ESP32-C6 -> PN532
# =========================
# SDA = GPIO 7
# SCL = GPIO 0

i2c = I2C(
    0,
    scl=Pin(0),
    sda=Pin(7),
    freq=100000
)

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
left = Pin(2, Pin.IN, Pin.PULL_UP)

print("Skanowanie magistrali I2C...")

devices = i2c.scan()

print("Znalezione urządzenia:", [hex(x) for x in devices])

if 0x24 not in devices:
    tft.text(font8, "Blad 404", 0, 0, st7789.WHITE)
    print("BLAD: nie znaleziono PN532!")
    print("Sprawdz:")
    print("- SDA -> GPIO7")
    print("- SCL -> GPIO0")
    print("- GND -> GND")
    print("- VCC -> zasilanie PN532")
else:
    print("PN532 znaleziony pod adresem 0x24!")
    tft.text(font16, "Zbliz karte do czytnika...", 20, 80, st7789.WHITE)

    # Utworzenie obiektu PN532
    pn532 = PN532_I2C(i2c, debug=False)

    # =========================
    # Odczyt firmware
    # =========================

    print("Sprawdzanie firmware PN532...")

    try:
        firmware = pn532.firmware_version()

        print(
            "Firmware:",
            firmware[0],
            firmware[1],
            firmware[2],
            firmware[3]
        )

    except Exception as e:
        print("Blad firmware:", e)

    # =========================
    # Ustawienie trybu czytnika
    # =========================

    print("Konfiguracja PN532...")

    try:
        pn532.set_mode()
        print("PN532 gotowy.")
    except Exception as e:
        print("Blad konfiguracji:", e)

    print()
    print("==============================")
    print("   PRZYLOZ KARTE DO PN532")
    print("==============================")
    print()

    # =========================
    # Odczyt kart
    # =========================

    while True:

        try:
            card = pn532.list_passive_target(timeout=500)

            if card:
                # card:
                # [target, SENS_RES, SEL_RES, UID]

                target = card[0]
                sens_res = card[1]
                sel_res = card[2]
                uid = card[3]

                print()
                print("==============================")
                print("KARTA ZNALEZIONA!")
                print("==============================")
                tft.fill(st7789.BLACK)

                tft.text(font8, "Karta znaleziona:", 10, 10, st7789.WHITE)
                tft.text(font8, "SENS_RES:" + hex(sens_res), 10, 30, st7789.WHITE)
                tft.text(font8, "SEL_RES:" + hex(sel_res), 10, 50, st7789.WHITE)
                tft.text(font8, "UID:" + " ".join("{:02X}".format(x) for x in uid), 10, 70, st7789.WHITE)
                tft.text(font8, "UID HEX:" + bytes(uid).hex(), 10, 90, st7789.WHITE)
                tft.text(font16, "Przyloz kolejna karte aby zeskanowac", 10, 180, st7789.WHITE)
                tft.text(font16, "Kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)
                print("Target:", target)
                print("SENS_RES:", hex(sens_res))
                print("SEL_RES:", hex(sel_res))

                print(
                    "UID:",
                    " ".join("{:02X}".format(x) for x in uid)
                )

                print("UID HEX:", bytes(uid).hex())

                print("UID DEC:", uid)

                print("==============================")
                print()

                # Nie drukuj tej samej karty cały czas
                time.sleep_ms(10)

            else:
                if left.value() == 0:
                    machine.reset()
        
                    while up.value() == 0:
                        time.sleep_ms(10)

        except Exception as e:
            print()
            print("Blad odczytu:", e)
            time.sleep(1)

        time.sleep(0.1)