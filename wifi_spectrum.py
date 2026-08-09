from machine import Pin, SPI
import network
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

CHANNELS = 13

BAR_W = GRAPH_W // CHANNELS


# =========================================================
# WIFI
# =========================================================

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.disconnect()


# =========================================================
# POPRZEDNIE WYSOKOŚCI
# =========================================================

old_heights = {}

for ch in range(1, CHANNELS + 1):
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
# POZYCJA LINII RSSI
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
    tft.text(font8, "Trzymaj lewo aby wyjsc <-", 5, 225, st7789.WHITE)

    # -----------------------------------------------------
    # Tytuł
    # -----------------------------------------------------

    tft.text(
        font8,
        "WiFi Spectrum 2.4GHz",
        100,
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

        # liczba RSSI
        tft.text(
            font8,
            str(rssi),
            0,
            y - 4,
            WHITE
        )

        # linia pomocnicza
        tft.line(
            GRAPH_X + 1,
            y,
            GRAPH_X + GRAPH_W,
            y,
            GRID
        )

    # -----------------------------------------------------
    # NUMERY KANAŁÓW
    # -----------------------------------------------------

    for ch in range(1, CHANNELS + 1):

        x = GRAPH_X + (ch - 1) * BAR_W

        tft.text(
            font8,
            str(ch),
            x + 4,
            GRAPH_Y + GRAPH_H + 5,
            WHITE
        )


# =========================================================
# SKANOWANIE WIFI
# =========================================================

def scan_wifi():

    networks = wlan.scan()

    channel_rssi = {}

    for ch in range(1, CHANNELS + 1):
        channel_rssi[ch] = []

    for net in networks:

        try:

            # scan():
            # 0 = SSID
            # 1 = BSSID
            # 2 = channel
            # 3 = RSSI

            channel = net[2]
            rssi = net[3]

            if 1 <= channel <= 13:

                channel_rssi[channel].append(rssi)

        except:
            pass

    result = {}

    for ch in range(1, CHANNELS + 1):

        values = channel_rssi[ch]

        if values:
            result[ch] = max(values)
        else:
            result[ch] = -100

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

    for ch in range(1, CHANNELS + 1):

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

        x = GRAPH_X + (ch - 1) * BAR_W + 2

        width = BAR_W - 3

        old_y = GRAPH_Y + GRAPH_H - old_height
        new_y = GRAPH_Y + GRAPH_H - new_height

        # =================================================
        # SŁUPEK URÓSŁ
        # =================================================

        if new_height > old_height:

            # Dorysowujemy tylko brakującą część

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

            # Czyścimy tylko część, która została usunięta

            tft.fill_rect(
                x,
                old_y,
                width,
                old_height - new_height,
                BLACK
            )

            # Odtwarzamy linie pomocnicze,
            # które zostały wymazane

            redraw_grid_part(
                x,
                old_y,
                old_y + old_height - new_height
            )

        # -------------------------------------------------
        # Zapamiętujemy wysokość
        # -------------------------------------------------

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

        data = scan_wifi()

        draw_spectrum(data)

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            start
        )

        print(
            "Scan + draw:",
            elapsed,
            "ms"
        )
        
        if left.value() == 0:
            machine.reset()
        
        # Małe opóźnienie
        time.sleep_ms(50)

    except Exception as e:

        print(
            "SCAN ERROR:",
            e
        )

        time.sleep_ms(500)