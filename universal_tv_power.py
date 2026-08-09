from machine import Pin, SPI
import machine
import st7789
import esp32
import time
import vga1_8x16 as font16

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

IR_PIN = 11

# ==========================
# Single RMT instance - 38 kHz works for most protocols
# ==========================

rmt = esp32.RMT(
    pin=Pin(IR_PIN, Pin.OUT),
    resolution_hz=1_000_000,
    tx_carrier=(38000, 33, 1)
)

# ==========================
# SIRC (Sony IR) - 40 kHz (using 38kHz RMT)
# ==========================

# SIRC 12-bit
ADDRESS1_SIRC = 0x01
COMMAND1_SIRC = 0x15

ADDRESS2_SIRC = 0x00
COMMAND2_SIRC = 0x15

ADDRESS3_SIRC = 0x08
COMMAND3_SIRC = 0x15

ADDRESS4_SIRC = 0x1F
COMMAND4_SIRC = 0x15

# SIRC 15-bit
ADDRESS1_SIRC15 = 0x01
COMMAND1_SIRC15 = 0x65

ADDRESS2_SIRC15 = 0x11
COMMAND2_SIRC15 = 0x15

ADDRESS3_SIRC15 = 0x01
COMMAND3_SIRC15 = 0x0B

# SIRC 20-bit
ADDRESS1_SIRC20 = 0x10
COMMAND1_SIRC20 = 0x15
EXTENDED1_SIRC20 = 0x00

ADDRESS2_SIRC20 = 0x1A
COMMAND2_SIRC20 = 0x15
EXTENDED2_SIRC20 = 0x00

ADDRESS3_SIRC20 = 0x0C
COMMAND3_SIRC20 = 0x15
EXTENDED3_SIRC20 = 0x00


def send_sirc(command, address):
    durations = []
    levels = []

    # Start: 2400 us ON, 600 us OFF
    levels.extend([1, 0])
    durations.extend([2400, 600])

    # 7 bitów komendy (LSB first)
    for i in range(7):
        if (command >> i) & 1:
            levels.extend([1, 0])
            durations.extend([1200, 600])
        else:
            levels.extend([1, 0])
            durations.extend([600, 600])

    # 5 bitów adresu (LSB first)
    for i in range(5):
        if (address >> i) & 1:
            levels.extend([1, 0])
            durations.extend([1200, 600])
        else:
            levels.extend([1, 0])
            durations.extend([600, 600])

    rmt.write_pulses(tuple(durations), tuple(levels))


def send_sirc15(command, address):
    durations = []
    levels = []

    # Start
    levels.extend([1, 0])
    durations.extend([2400, 600])

    # 7 bitów komendy (LSB first)
    for i in range(7):
        if (command >> i) & 1:
            durations.extend([1200, 600])
        else:
            durations.extend([600, 600])
        levels.extend([1, 0])

    # 8 bitów adresu (LSB first)
    for i in range(8):
        if (address >> i) & 1:
            durations.extend([1200, 600])
        else:
            durations.extend([600, 600])
        levels.extend([1, 0])

    rmt.write_pulses(tuple(durations), tuple(levels))


def send_sirc20(command, address, extended):
    durations = []
    levels = []

    # Start
    levels.extend([1, 0])
    durations.extend([2400, 600])

    # 7 bitów komendy
    for i in range(7):
        if (command >> i) & 1:
            durations.extend([1200, 600])
        else:
            durations.extend([600, 600])
        levels.extend([1, 0])

    # 5 bitów adresu
    for i in range(5):
        if (address >> i) & 1:
            durations.extend([1200, 600])
        else:
            durations.extend([600, 600])
        levels.extend([1, 0])

    # 8 bitów Extended
    for i in range(8):
        if (extended >> i) & 1:
            durations.extend([1200, 600])
        else:
            durations.extend([600, 600])
        levels.extend([1, 0])

    rmt.write_pulses(tuple(durations), tuple(levels))


# ==========================
# Samsung - 38 kHz
# ==========================

def samsung32(a, c):
    d = []
    l = []

    l += [1,0]
    d += [4500,4500]

    for i in range(8):
        l.append(1)
        l.append(0)
        if (a >> i) & 1:
            d.extend([560, 1690])
        else:
            d.extend([560, 560])

    for i in range(8):
        l.append(1)
        l.append(0)
        if (a >> i) & 1:
            d.extend([560, 1690])
        else:
            d.extend([560, 560])

    for i in range(8):
        l.append(1)
        l.append(0)
        if (c >> i) & 1:
            d.extend([560, 1690])
        else:
            d.extend([560, 560])

    for i in range(8):
        l.append(1)
        l.append(0)
        if ((~c) >> i) & 1:
            d.extend([560, 1690])
        else:
            d.extend([560, 560])

    l.append(1)
    d.append(560)

    rmt.write_pulses(tuple(d), tuple(l))


def send_samsung16(address, command):
    durations = []
    levels = []

    # Start
    levels.extend([1, 0])
    durations.extend([9000, 4500])

    # 16-bit Address (LSB first)
    for i in range(16):
        levels.extend([1, 0])
        if (address >> i) & 1:
            durations.extend([560, 1690])
        else:
            durations.extend([560, 560])

    # 16-bit Command (LSB first)
    for i in range(16):
        levels.extend([1, 0])
        if (command >> i) & 1:
            durations.extend([560, 1690])
        else:
            durations.extend([560, 560])

    # Stop
    levels.append(1)
    durations.append(560)

    rmt.write_pulses(tuple(durations), tuple(levels))


# ==========================
# RC5 - 36 kHz
# ==========================

ADDRESS1_RC5 = 0x00
COMMAND1_RC5 = 0x0C
TOGGLE1_RC5 = 0

ADDRESS2_RC5 = 0x01
COMMAND2_RC5 = 0x0C
TOGGLE2_RC5 = 0

ADDRESS3_RC5 = 0x05
COMMAND3_RC5 = 0x0C
TOGGLE3_RC5 = 0

ADDRESS4_RC5 = 0x07
COMMAND4_RC5 = 0x0C
TOGGLE4_RC5 = 0

ADDRESS5_RC5 = 0x10
COMMAND5_RC5 = 0x0C
TOGGLE5_RC5 = 0

HALF_BIT_RC5 = 889  # RC5 półbit


def manchester_bit_rc5(durations, levels, bit):
    # RC5:
    # 1 = LOW->HIGH
    # 0 = HIGH->LOW
    if bit:
        levels.extend([0, 1])
        durations.extend([HALF_BIT_RC5, HALF_BIT_RC5])
    else:
        levels.extend([1, 0])
        durations.extend([HALF_BIT_RC5, HALF_BIT_RC5])


def send_rc5(address, command, toggle):
    levels = []
    durations = []

    # 14 bitów MSB first:
    frame = (
        (1 << 13) |        # start bit 1
        (1 << 12) |        # start bit 2
        (toggle << 11) |
        (address << 6) |
        command
    )

    for i in range(13, -1, -1):
        manchester_bit_rc5(
            durations,
            levels,
            (frame >> i) & 1
        )

    rmt.write_pulses(tuple(durations), tuple(levels))


# ==========================
# Panasonic - 36 kHz (PWM)
# ==========================

from machine import PWM

# Panasonic timings
HEADER_MARK_PANASONIC = 3500
HEADER_SPACE_PANASONIC = 1750

BIT_MARK_PANASONIC = 432
ZERO_SPACE_PANASONIC = 432
ONE_SPACE_PANASONIC = 1296


def mark_panasonic(us, carrier):
    carrier.duty(512)
    time.sleep_us(us)
    carrier.duty(0)


def space_panasonic(us, carrier):
    carrier.duty(0)
    time.sleep_us(us)


def send_bit_panasonic(bit, carrier):
    mark_panasonic(BIT_MARK_PANASONIC, carrier)
    if bit:
        space_panasonic(ONE_SPACE_PANASONIC, carrier)
    else:
        space_panasonic(ZERO_SPACE_PANASONIC, carrier)


def send_byte_panasonic(value, carrier):
    for i in range(8):
        send_bit_panasonic((value >> i) & 1, carrier)


def send_panasonic(addr, cmd, carrier):
    # start
    mark_panasonic(HEADER_MARK_PANASONIC, carrier)
    space_panasonic(HEADER_SPACE_PANASONIC, carrier)

    # próba ramki Panasonic 48 bit
    data = [
        addr & 0xFF,
        (addr >> 8) & 0xFF,
        cmd & 0xFF,
        (cmd >> 8) & 0xFF,
        0x00,
        0x00
    ]

    for b in data:
        send_byte_panasonic(b, carrier)

    mark_panasonic(BIT_MARK_PANASONIC, carrier)
    carrier.duty(0)


panasonic_codes = [
    (0x4004, 0x100C),
    (0x4004, 0x1001),
    (0x4004, 0x0001),
    (0x4004, 0x000C),
    (0x4004, 0x40BF)
]


# ==========================
# NEC - 38 kHz
# ==========================

nec_codes = [
    (0x07,0x02),
    (0xE0E0,0x40BF),
    (0x00,0x02),
    (0x40,0x0C),
    (0x20,0xDF),
    (0x04,0x08),
    (0x18,0xE7),
    (0x20DF,0x10EF),
    (0x20DF,0x40BF),
    (0x20DF,0xD02F),
    (0x20DF,0x08F7),
    (0x20DF,0xF00F),
    (0x20DF,0xC03F),
    (0x20DF,0x8877),
    (0x20DF,0x18E7),
    (0x20DF,0x30CF),
    (0x20DF,0x48B7),
    (0x00FF,0xF00F),
    (0x00FF,0x10EF),
    (0x807F,0x02FD),
    (0x807F,0x40BF),
    (0x20DF,0x10EF),
    (0xF00F,0x0AF5),
    (0xD827,0x20DF),
    (0x00FF,0x40BF),
    (0xA25D,0x629D),
    (0x00FF,0x08F7),
    (0x00FF,0xF00F),
    (0x00FF,0x10EF),
    (0x807F,0x02FD),
    (0x807F,0x40BF),
    (0x20DF,0x10EF),
    (0xF00F,0x0AF5),
    (0xD827,0x20DF),
    (0x00FF,0x40BF),
    (0xA25D,0x629D),
    (0x00FF,0x08F7),
    (0xFF00,0x12ED),
    (0xFF00,0x02FD),
    (0xFD02,0x10EF),
    (0xFD02,0x00FF),
    (0x20DF,0x10EF),
    (0x00FF,0x40BF),
    (0xFF00,0xF00F),
    (0xA25D,0x629D),
    (0xFD02,0x20DF),
    (0xFF00,0x08F7),
    (0x806F,0x12ED),
    (0x4004,0x02FD),
    (0x806F,0x10EF),
    (0x806F,0x08F7),
    (0x806F,0x20DF),
    (0x00FF,0x12ED),
    (0x00FF,0x02FD),
    (0x807F,0x48B7),
    (0x20DF,0x10EF),
    (0x00FF,0x40BF),
    (0xA25D,0x629D),
    (0xF00F,0x10EF),
    (0xC03F,0x08F7),
    (0x10EF,0x00FF),
    (0x00FF,0xF00F),
    (0x00FF,0x12ED),
    (0x00FF,0x02FD),
    (0x807F,0x48B7),
    (0x20DF,0x10EF),
    (0x00FF,0x40BF),
    (0xA25D,0x629D),
    (0xF00F,0x10EF),
    (0xC03F,0x08F7),
    (0x10EF,0x00FF),
    (0x00FF,0xF00F),
]


def send_nec(a, c):
    d = []
    l = []
    l += [1, 0]
    d += [9000, 4500]
    for i in range(8):
        l.extend([1, 0])
        d.extend([560, 1690] if ((a >> i) & 1) else [560, 560])
    ia = (~a) & 0xFF
    for i in range(8):
        l.extend([1, 0])
        d.extend([560, 1690] if ((ia >> i) & 1) else [560, 560])
    for i in range(8):
        l.extend([1, 0])
        d.extend([560, 1690] if ((c >> i) & 1) else [560, 560])
    ic = (~c) & 0xFF
    for i in range(8):
        l.extend([1, 0])
        d.extend([560, 1690] if ((ic >> i) & 1) else [560, 560])
    l.append(1)
    d.append(560)
    rmt.write_pulses(tuple(d), tuple(l))


def send_nec16(a, c):
    d = []
    l = []
    l += [1, 0]
    d += [9000, 4500]
    for i in range(16):
        l.extend([1, 0])
        d.extend([560, 1690] if ((a >> i) & 1) else [560, 560])
    for i in range(16):
        l.extend([1, 0])
        d.extend([560, 1690] if ((c >> i) & 1) else [560, 560])
    l.append(1)
    d.append(560)
    rmt.write_pulses(tuple(d), tuple(l))


# ==========================
# Main execution - sending all signals
# ==========================
# SIRC signals
tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow SIRC 12bit...", 30, 80, st7789.WHITE)
for _ in range(3):
    send_sirc(COMMAND1_SIRC, ADDRESS1_SIRC)
    time.sleep(0.5)

for _ in range(3):
    send_sirc(COMMAND2_SIRC, ADDRESS2_SIRC)
    time.sleep(0.5)

for _ in range(3):
    send_sirc(COMMAND3_SIRC, ADDRESS3_SIRC)
    time.sleep(0.5)

for _ in range(3):
    send_sirc(COMMAND4_SIRC, ADDRESS4_SIRC)
    time.sleep(0.5)

tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow SIRC 15bit...", 30, 80, st7789.WHITE)
for _ in range(3):
    send_sirc15(COMMAND1_SIRC15, ADDRESS1_SIRC15)
    time.sleep(0.5)

for _ in range(3):
    send_sirc15(COMMAND2_SIRC15, ADDRESS2_SIRC15)
    time.sleep(0.5)

for _ in range(3):
    send_sirc15(COMMAND3_SIRC15, ADDRESS3_SIRC15)
    time.sleep(0.5)

tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow SIRC 20bit...", 30, 80, st7789.WHITE)
for _ in range(3):
    send_sirc20(COMMAND1_SIRC20, ADDRESS1_SIRC20, EXTENDED1_SIRC20)
    time.sleep(0.5)

for _ in range(3):
    send_sirc20(COMMAND2_SIRC20, ADDRESS2_SIRC20, EXTENDED2_SIRC20)
    time.sleep(0.5)

for _ in range(3):
    send_sirc20(COMMAND3_SIRC20, ADDRESS3_SIRC20, EXTENDED3_SIRC20)
    time.sleep(0.5)

# Samsung signals
tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow Samsung 32bit...", 10, 80, st7789.WHITE)
samsung32(0x07, 0x02)
time.sleep(0.5)

tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow Samsung 16bit...", 10, 80, st7789.WHITE)
send_samsung16(0xE0E0, 0x40BF)
time.sleep(0.5)

# RC5 signals
tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow RC5 16bit", 30, 80, st7789.WHITE)
send_rc5(ADDRESS1_RC5, COMMAND1_RC5, TOGGLE1_RC5)
time.sleep(0.5)
send_rc5(ADDRESS2_RC5, COMMAND2_RC5, TOGGLE2_RC5)
time.sleep(0.5)
send_rc5(ADDRESS3_RC5, COMMAND3_RC5, TOGGLE3_RC5)
time.sleep(0.5)
send_rc5(ADDRESS4_RC5, COMMAND4_RC5, TOGGLE4_RC5)
time.sleep(0.5)
send_rc5(ADDRESS5_RC5, COMMAND5_RC5, TOGGLE5_RC5)
time.sleep(0.5)

# NEC signals
tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow NEC..", 50, 80, st7789.WHITE)
for a, c in nec_codes:
    if a <= 0xFF and c <= 0xFF:
        send_nec(a, c)
    else:
        send_nec16(a, c)
    time.sleep(0.5)

# Panasonic signals - 36 kHz (PWM)
tft.fill(st7789.BLACK)
tft.text(font16, "Wysylanie sygnalow Panasonic", 30, 80, st7789.WHITE)
# Release RMT before using PWM on the same pin
del rmt
carrier_panasonic = PWM(Pin(IR_PIN), freq=36000, duty=0)
for addr, cmd in panasonic_codes:
    send_panasonic(addr, cmd, carrier_panasonic)
    time.sleep(0.5)
    
carrier_panasonic.deinit()
# Reinitialize RMT for NEC signals
rmt = esp32.RMT(
    pin=Pin(IR_PIN, Pin.OUT),
    resolution_hz=1_000_000,
    tx_carrier=(38000, 33, 1)
)

tft.fill(st7789.BLACK)
tft.text(font16, "Wszystkie sygnaly zostaly wyslane!", 10, 80, st7789.WHITE)
tft.text(font16, "Kliknij lewo aby wyjsc <-", 10, 220, st7789.WHITE)

while True:
    if left.value() == 0:
        machine.reset()
        
        while up.value() == 0:
            time.sleep_ms(10)
    

