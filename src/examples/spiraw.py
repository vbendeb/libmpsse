#!/usr/bin/env python

import os
import random
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

    def __init__(self, speed=FIFTEEN_MHZ, mode=0):

        modes = [SPI0, SPI1, SPI2, SPI3]

        # Sanity check on the specified clock speed
        if not speed:
            speed = FIFTEEN_MHZ

        self.flash = MPSSE(modes[mode], speed, MSB)
        self.chip = self.flash.GetDescription()
        self.speed = self.flash.GetClock()
        self._init_gpio()
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

    def Start(self):
        self.flash.Start()

    def Stop(self):
        self.flash.Stop()

    def Read(self, count):
        data = self.flash.Read(count)
        return data

    def Write(self, data):
        self.flash.Write(data)

    def Close(self):
        self.flash.Stop()
        self.flash.Close()

if __name__ == "__main__":

    import sys
    from getopt import getopt as GetOpt, GetoptError

    def do_n_loops(num_loops, spi):
        deviation = 0
        for _ in range(num_loops):
            size = 10 + int(random.random() * 1000)
            text = [size / 256, size % 256]
            check = 255
            for i in range(size - 1):
                check ^= i
                text.append(i)
            text.append(check % 256)
            spi.Start()
            text = ''.join('%c' % (x % 256) for x in text)
            spi.Write(text)
            readback = spi.Read(size + 60)
            spi.Stop()
            read_index = readback.find(text[0:2])
            readtext = readback[read_index:read_index + len(text)]
            if readtext != text:
                print 'Mismatch!', read_index
                for s in (text, readtext, readback):
                    print ' '.join(' %2.2x' % ord(x) for x in s)
                    print

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
        print "\t-f, --frequency=<int>  Set the SPI clock frequency, in hertz [15,000,000]"
        print "\t-m, --loop=<int>       Send N random size packets and verify they are sent back"
        print "\t-m, --mode=<int>       Set the SPI bus mode {[0], 1, 2, 3}"
        print "\t-r, --read=<file>      Read raw data from the bus to file"
        print "\t-s, --size=<int>       Set the size of raw data to read"
        print "\t-w, --write=<file>     Write raw data from file to the bus"
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
        num_loops = 0
        verify = False
        address = 0
        size = 0
        data = ""
        mode = 0 # Default SPI operation mode

        try:
            opts, args = GetOpt(sys.argv[1:], "f:l:m:r:s:w:chp",
                ["frequency=", "loop=", "mode=", "read=", "size=", "write=",
                "clock", "help", "pin-mappings"])
        except GetoptError, e:
            print e
            usage()

        try:
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
                elif opt in ('-l', '--loop'):
                    num_loops = int(arg)
                elif opt in ('-m', '--mode'):
                    mode = int(arg)
        except ValueError:
            usage()

        if mode < 0 or mode > 3:
            usage()

        if not (do_read or do_write or do_clock or num_loops):
            print "Please specify an action!"
            usage()

        if (do_read or do_write or num_loops) and do_clock:
            print "Constant clock can not be combined with read and/or write!"
            usage()

        if ((do_read or do_write) and num_loops):
            print "Loops can not be combined with read or write"
            usage()

        if do_read:
            if not rname or not size:
                print "Please specify an output file and read size!"
                usage()

        if do_write:
            if not wname:
                print "Please specify an input file!"
                usage()

        spi = SPIRaw(freq, mode)
        print "%s initialized at %d hertz" % (spi.chip, spi.speed)

        if (num_loops):
            do_n_loops(num_loops, spi)

        spi.Start()
        if do_clock:
            if size:
                spi.Write('U' * size)
            else:
                try:
                    data = 'some random string to keep sending'
                    while True:
                        spi.Write(data)
                except KeyboardInterrupt:
                    pass
            sys.exit(0)

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
