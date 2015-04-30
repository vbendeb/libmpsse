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
        self.write_reported = False

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
        if not self.write_reported:
            print 'data is', data
            self.write_reported = True
        self.flash.Write(data)

    def Close(self):
        self.flash.Stop()
        self.flash.Close()

if __name__ == "__main__":

    import sys
    from getopt import getopt as GetOpt, GetoptError

    def pin_mappings():
        print """
           Pin mappings for raw SPI mode
-----------------------------------------
| Description | C232HM Cable Color Code |
-----------------------------------------
| CS          |        Brown            |
| MISO        |        Green            |
| WP          |        Grey             |
| GND         |        Black            |
| MOSI        |       Yellow            |
| CLK         |       Orange            |
| HOLD        |       Purple            |
| Vcc         |         Red             |
-----------------------------------------
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
        print "\t-c, --clock            Just keep clocking the bus with CS asserted"
        print "\t-h, --help             Show help"
        print "\t-p, --pin-mappings     Display a table of SPI flash to FTDI pin mappings"
        print ""

        sys.exit(1)

    def main():
        freq = None
        do_read = False
        do_write = False
        do_clock = False
        verify = False
        address = 0
        size = 0
        data = ""

        try:
            opts, args = GetOpt(sys.argv[1:],
                                "f:s:r:w:chp",
                                ["frequency=", "size=", "read=",
                                 "write=", "clock", "help", "pin-mappings"])
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
            elif opt in ('-c', '--clock'):
                do_clock = True

        if not (do_read or do_write or do_clock):
            print "Please specify an action!"
            usage()

        if (do_read or do_write) and do_clock:
            print "Constant clock can not be combined with read and/or write!"
            usage()

        if do_read:
            if not rname or not size:
                print "Please specify an output file and read size!"
                usage()

        if do_write:
            if not wname:
                print "Please specify an input file!"
                usage()

        spi = SPIRaw(freq)
        print "%s initialized at %d hertz" % (spi.chip, spi.speed)

        if do_clock:
            try:
                data = 'some random string to keep sending'
                while True:
                    spi.Write(data)
            except KeyboardInterrupt:
                pass

        if do_write:
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
