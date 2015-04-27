#!/usr/bin/env python

import os
import sys

MPSSE_MODULE = 'mpsse.py'

for d in sys.path:
    if os.path.exists(os.path.join(d, MPSSE_MODULE)):
        break;
else:
    sys.path.append(os.path.realpath(
        os.path.join(os.path.dirname(sys.argv[0]), '..')))

from mpsse import *
from time import sleep

class SPIRaw(object):

    BLOCK_SIZE = 256    # SPI block size, writes must be done in multiples of this size

    def __init__(self, speed=FIFTEEN_MHZ):

        # Sanity check on the specified clock speed
        if not speed:
            speed = FIFTEEN_MHZ

        self.flash = MPSSE(SPI0, speed, MSB)
        self.chip = self.flash.GetDescription()
        self.speed = self.flash.GetClock()
        self._init_gpio()
        self.flash.Start()

    def _init_gpio(self):
        # Set the GPIOL0 and GPIOL1 pins high for connection to SPI flash WP and HOLD pins.
        self.flash.PinHigh(GPIOL0)
        self.flash.PinHigh(GPIOL1)

    def _addr2str(self, address):
            addr_str = ""

            for i in range(0, self.ADDRESS_LENGTH):
                    addr_str += chr((address >> (i*8)) & 0xFF)

            return addr_str[::-1]

    def Read(self, count):
        data = self.flash.Read(count)
        return data

    def Write(self, data):
        print 'data is', data
        self.flash.Write(data)

    def Close(self):
        self.flash.Stop()
        self.flash.Close()


if __name__ == "__main__":

    import sys
    from getopt import getopt as GetOpt, GetoptError

    def pin_mappings():
        print """
           Common Pin Mappings for 8-pin SPI Flash Chips
--------------------------------------------------------------------
| Description | SPI Flash Pin | FTDI Pin | C232HM Cable Color Code |
--------------------------------------------------------------------
| CS          | 1             | ADBUS3   | Brown                   |
| MISO        | 2             | ADBUS2   | Green                   |
| WP          | 3             | ADBUS4   | Grey                    |
| GND         | 4             | N/A      | Black                   |
| MOSI        | 5             | ADBUS1   | Yellow                  |
| CLK         | 6             | ADBUS0   | Orange                  |
| HOLD        | 7             | ADBUS5   | Purple                  |
| Vcc         | 8             | N/A      | Red                     |
--------------------------------------------------------------------
"""
        sys.exit(0)

    def usage():
        print ""
        print "Usage: %s [OPTIONS]" % sys.argv[0]
        print ""
        print "\t-r, --read=<file>      Read raw data from the bus to file"
        print "\t-w, --write=<file>     Write raw data from file to the bus"
        print "\t-s, --size=<int>       Set the size of raw data to read"
        print "\t-f, --frequency=<int>  Set the SPI clock frequency, in hertz [15,000,000]"
        print "\t-p, --pin-mappings     Display a table of SPI flash to FTDI pin mappings"
        print "\t-h, --help             Show help"
        print ""

        sys.exit(1)

    def main():
        freq = None
        do_read = False
        do_write = False
        verify = False
        address = 0
        size = 0
        data = ""

        try:
            opts, args = GetOpt(sys.argv[1:],
                                "f:s:r:w:ph",
                                ["frequency=", "size=", "read=",
                                 "write=", "pin-mappings", "help"])
        except GetoptError, e:
            print e
            usage()

        for opt, arg in opts:
            if opt in ('-f', '--frequency'):
                freq = int(arg)
            elif opt in ('-s', '--size'):
                size = int(arg)
            elif opt in ('-r', '--read'):
                do_read = True
                rname = arg
            elif opt in ('-w', '--write'):
                do_write = True
                wname = arg
            elif opt in ('-h', '--help'):
                usage()
            elif opt in ('-p', '--pin-mappings'):
                pin_mappings()

        if not (do_read or do_write):
            print "Please specify an action!"
            usage()

        if do_read:
            if rname is None or not size:
                print "Please specify an output file and read size!"
                usage()

        spi = SPIRaw(freq)
        print "%s initialized at %d hertz" % (spi.chip, spi.speed)

        if do_write:
            if wname is None:
                print "Please specify an input file!"
                usage()

            data = open(wname, 'rb').read()
            sys.stdout.write("Writing %d bytes from %s to the chip..." %
                             (len(data), wname))
            sys.stdout.flush()
            spi.Write(data)
            print "done."

        if do_read:
            sys.stdout.write("Reading %d bytes..." % size)
            sys.stdout.flush()
            data = spi.Read(size)
            open(rname, 'wb').write(data)
            print "saved to %s." % rname

        spi.Close()

    main()
