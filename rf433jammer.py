"""
433MHz Jammer for ESP32-C6 with CC1101
Continuous jamming - starts immediately on boot
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
import vga1_8x16 as font8

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

left = Pin(2, Pin.IN, Pin.PULL_UP)

tft.fill(st7789.BLACK)
tft.text(font32, "Jammer 433MHz", 50, 50, st7789.RED)
tft.text(font32, "Aktywny(!)", 70, 120, st7789.GREEN)
tft.text(font8, "Kliknij lewo aby wrocic <-", 10, 220, st7789.WHITE)

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
        self.gdo0 = Pin(gdo0_pin, Pin.IN)
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
        """Initialize CC1101 for maximum power jamming"""
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

        # Frequency 433.92 MHz
        self._write_reg(CC1101_FREQ2, 0x10)
        self._write_reg(CC1101_FREQ1, 0xB0)
        self._write_reg(CC1101_FREQ0, 0x71)
        self._write_reg(CC1101_FSCTRL1, 0x0F)
        self._write_reg(CC1101_FSCTRL0, 0x00)

        # AM650 (ASK/OOK) modulation
        self._write_reg(CC1101_MDMCFG4, 0xF6)
        self._write_reg(CC1101_MDMCFG3, 0x83)
        self._write_reg(CC1101_MDMCFG2, 0x13)  # ASK/OOK
        self._write_reg(CC1101_MDMCFG1, 0x22)
        self._write_reg(CC1101_MDMCFG0, 0xF8)
        self._write_reg(CC1101_DEVIATN, 0x15)

        # Control
        self._write_reg(CC1101_MCSM2, 0x07)
        self._write_reg(CC1101_MCSM1, 0x30)
        self._write_reg(CC1101_MCSM0, 0x18)

        # AGC
        self._write_reg(CC1101_FOCCFG, 0x16)
        self._write_reg(CC1101_BSCFG, 0x6C)
        self._write_reg(CC1101_AGCCTRL2, 0x43)
        self._write_reg(CC1101_AGCCTRL1, 0x40)
        self._write_reg(CC1101_AGCCTRL0, 0x91)

        # Front-end
        self._write_reg(CC1101_FREND1, 0xB6)
        self._write_reg(CC1101_FREND0, 0x10)

        # Calibration
        self._write_reg(CC1101_FSCAL3, 0xE9)
        self._write_reg(CC1101_FSCAL2, 0x2A)
        self._write_reg(CC1101_FSCAL1, 0x00)
        self._write_reg(CC1101_FSCAL0, 0x1F)

        # PA Table - max power
        self._write_burst(CC1101_PATABLE, [0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0, 0xC0])

        # Calibration
        self._strobe(CC1101_SCAL)
        time.sleep_ms(10)
        self._strobe(CC1101_SIDLE)
        time.sleep_ms(1)

    def start_jamming(self):
        """Start continuous jamming - never returns"""
        print("JAMMER 433MHz STARTED - Continuous jamming")
        
        # Set for ASK/OOK modulation
        self._write_reg(CC1101_MDMCFG2, 0x13)
        
        # Create jamming pattern - alternating bits for maximum interference
        jam_pattern = bytearray(64)
        for i in range(64):
            jam_pattern[i] = 0xAA if i % 2 == 0 else 0x55
        
        # Start infinite jamming loop
        while True:
            # Clear TX FIFO
            self._strobe(CC1101_SFTX)
            time.sleep_us(100)
            
            # Fill FIFO with jamming pattern
            self._write_burst(CC1101_TXFIFO, jam_pattern)
            
            # Start transmission
            self._strobe(CC1101_STX)
            time.sleep_us(50)
            
            if left.value() == 0:
                machine.reset()
        
                while up.value() == 0:
                    time.sleep_ms(10)
            
            # Keep transmitting and refill FIFO as needed
            while True:
                # Check if FIFO needs refilling
                tx_bytes = self._read_reg(CC1101_TXBYTES, burst=False) & 0x7F
                if tx_bytes < 32:
                    # Refill FIFO with fresh jamming pattern
                    for i in range(64):
                        jam_pattern[i] = 0xAA if i % 2 == 0 else 0x55
                    self._write_burst(CC1101_TXFIFO, jam_pattern)
                
                # Small delay to prevent CPU overload
                time.sleep_us(50)
                
                # Check if still in TX mode
                marcstate = self._read_reg(CC1101_MARCSTATE) & 0x1F
                if marcstate != 0x11:  # 0x11 = TX state
                    # Re-enter TX mode if dropped out
                    self._strobe(CC1101_STX)
                    time.sleep_us(50)
                    break

def main():
    """Initialize CC1101 and start continuous jamming"""
    print("="*60)
    print("433MHz Jammer for ESP32-C6 with CC1101")
    print("Continuous jamming mode - MAX POWER")
    print("="*60)
    
    # Initialize CC1101
    cc1101 = CC1101(
        spi_id=1,
        sck_pin=6,
        miso_pin=5,
        mosi_pin=4,
        cs_pin=10,
        gdo0_pin=9
    )
    
    print("\nCC1101 initialized")
    print("Starting continuous jamming on 433.92MHz...")
    
    # Start infinite jamming
    cc1101.start_jamming()

if __name__ == "__main__":
    main()