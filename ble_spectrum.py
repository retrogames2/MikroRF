from machine import Pin, SPI
import bluetooth
import machine
import time
import st7789
import vga1_8x8 as font8


# =========================================================
# ST7789
# =========================================================

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


# =========================================================
# EKRAN
# =========================================================

WIDTH = 320
HEIGHT = 240


# =========================================================
# KOLORY
# =========================================================

BLACK = st7789.BLACK
WHITE = st7789.WHITE
GRID = st7789.color565(30, 30, 30)
BAR = st7789.color565(0, 180, 255)


# =========================================================
# WYKRES
# =========================================================

GRAPH_X = 30
GRAPH_Y = 30

GRAPH_W = 280
GRAPH_H = 175

# Maksymalnie pokazujemy 13 urządzeń
# uporządkowanych według RSSI
CHANNELS = 13

BAR_W = GRAPH_W // CHANNELS


# =========================================================
# BLE
# =========================================================

ble = bluetooth.BLE()
ble.active(True)


# =========================================================
# DANE SKANOWANIA
# =========================================================

devices = {}

_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6


def bt_irq(event, data):

    if event == _IRQ_SCAN_RESULT:

        addr_type, addr, adv_type, rssi, adv_data = data

        # Zamieniamy adres na bytes,
        # żeby można było użyć go jako klucza słownika

        addr = bytes(addr)

        devices[addr] = rssi


# Rejestrujemy callback
ble.irq(bt_irq)


# =========================================================
# POPRZEDNIE WYSOKOŚCI
# =========================================================

old_heights = {}

for ch in range(CHANNELS):
    old_heights[ch] = 0


# =========================================================
# RSSI -> WYSOKOŚĆ
# =========================================================

def rssi_to_height(rssi):

    if rssi < -100:
        rssi = -100

    if rssi > -20:
        rssi = -20

    return int(
        ((rssi + 100) / 80) * GRAPH_H
    )


# =========================================================
# RSSI -> Y
# =========================================================

def rssi_to_y(rssi):

    return GRAPH_Y + int(
        ((-rssi - 20) / 80) * GRAPH_H
    )


# =========================================================
# RYSOWANIE EKRANU
# =========================================================

def draw_axes():

    tft.fill(BLACK)

    tft.text(
        font8,
        "Trzymaj lewo aby wyjsc <-",
        5,
        225,
        WHITE
    )

    # -----------------------------------------------------
    # TYTUŁ
    # -----------------------------------------------------

    tft.text(
        font8,
        "Bluetooth BLE Analyzer",
        90,
        5,
        WHITE
    )

    # -----------------------------------------------------
    # OŚ Y
    # -----------------------------------------------------

    tft.line(
        GRAPH_X,
        GRAPH_Y,
        GRAPH_X,
        GRAPH_Y + GRAPH_H,
        WHITE
    )

    # -----------------------------------------------------
    # OŚ X
    # -----------------------------------------------------

    tft.line(
        GRAPH_X,
        GRAPH_Y + GRAPH_H,
        GRAPH_X + GRAPH_W,
        GRAPH_Y + GRAPH_H,
        WHITE
    )

    # -----------------------------------------------------
    # LINIE RSSI
    # -----------------------------------------------------

    for rssi in [-20, -40, -60, -80, -100]:

        y = rssi_to_y(rssi)

        tft.text(
            font8,
            str(rssi),
            0,
            y - 4,
            WHITE
        )

        tft.line(
            GRAPH_X + 1,
            y,
            GRAPH_X + GRAPH_W,
            y,
            GRID
        )

    # -----------------------------------------------------
    # NUMERY URZĄDZEŃ
    # -----------------------------------------------------

    for ch in range(CHANNELS):

        x = GRAPH_X + ch * BAR_W

        tft.text(
            font8,
            str(ch + 1),
            x + 4,
            GRAPH_Y + GRAPH_H + 5,
            WHITE
        )


# =========================================================
# SKAN BLE
# =========================================================

def scan_bluetooth():

    # Czyścimy poprzednie wyniki

    devices.clear()

    # -----------------------------------------------------
    # Skan BLE
    #
    # 100 ms = szybkie odświeżanie
    #
    # interval_us / window_us:
    # im większe, tym więcej czasu radio skanuje
    # -----------------------------------------------------

    ble.gap_scan(
        100,
        30000,
        30000,
        True
    )

    # Czekamy na zakończenie skanu

    time.sleep_ms(120)

    # Zatrzymujemy skan

    ble.gap_scan(None)

    # -----------------------------------------------------
    # Pobieramy RSSI
    # -----------------------------------------------------

    values = []

    for addr in devices:

        try:
            values.append(devices[addr])
        except:
            pass

    # Najsilniejsze urządzenia pierwsze

    values.sort(reverse=True)

    # Maksymalnie 13 słupków

    values = values[:CHANNELS]

    result = {}

    for i in range(CHANNELS):

        if i < len(values):
            result[i] = values[i]
        else:
            result[i] = -100

    return result


# =========================================================
# ODTWORZENIE FRAGMENTU LINII
# =========================================================

def redraw_grid_part(x, y1, y2):

    if y1 > y2:

        temp = y1
        y1 = y2
        y2 = temp

    for rssi in [-20, -40, -60, -80, -100]:

        y = rssi_to_y(rssi)

        if y1 <= y <= y2:

            tft.line(
                x,
                y,
                x + BAR_W - 4,
                y,
                GRID
            )


# =========================================================
# SZYBKIE RYSOWANIE SŁUPKÓW
# =========================================================

def draw_spectrum(data):

    for ch in range(CHANNELS):

        rssi = data[ch]

        new_height = rssi_to_height(rssi)
        old_height = old_heights[ch]

        # -------------------------------------------------
        # Nic się nie zmieniło
        # -------------------------------------------------

        if new_height == old_height:
            continue

        # -------------------------------------------------
        # Pozycja słupka
        # -------------------------------------------------

        x = GRAPH_X + ch * BAR_W + 2

        width = BAR_W - 3

        old_y = GRAPH_Y + GRAPH_H - old_height
        new_y = GRAPH_Y + GRAPH_H - new_height

        # =================================================
        # SŁUPEK URÓSŁ
        # =================================================

        if new_height > old_height:

            tft.fill_rect(
                x,
                new_y,
                width,
                new_height - old_height,
                BAR
            )

        # =================================================
        # SŁUPEK ZMALAŁ
        # =================================================

        else:

            tft.fill_rect(
                x,
                old_y,
                width,
                old_height - new_height,
                BLACK
            )

            redraw_grid_part(
                x,
                old_y,
                old_y + old_height - new_height
            )

        old_heights[ch] = new_height


# =========================================================
# START
# =========================================================

draw_axes()


# =========================================================
# PĘTLA
# =========================================================

while True:

    try:

        start = time.ticks_ms()

        data = scan_bluetooth()

        draw_spectrum(data)

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            start
        )

        print(
            "BLE Scan + draw:",
            elapsed,
            "ms",
            "Devices:",
            len(devices)
        )

        # -------------------------------------------------
        # PRZYCISK
        # -------------------------------------------------

        if left.value() == 0:
            machine.reset()

        time.sleep_ms(20)

    except Exception as e:

        print(
            "BLE SCAN ERROR:",
            e
        )

        time.sleep_ms(500)