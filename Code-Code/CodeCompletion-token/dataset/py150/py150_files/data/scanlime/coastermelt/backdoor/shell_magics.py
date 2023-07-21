#
# Implementation of IPython "magics", the cute shell-like
# functions you can use in the debugger shell.
#

__all__ = [ 'ShellMagics' ]

from IPython.core import magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
from IPython.core.display import display
from IPython.core.error import UsageError

import struct, sys, json, argparse, time
from hilbert import hilbert
import target_memory
import remote

from shell_functions import *
from code import *
from dump import *
from mem import *
from watch import *
from console import *
from hook import *
from bitfuzz import *
from bitbang import *
from sim_arm import *
from cpu8051 import *


@magic.magics_class
class ShellMagics(magic.Magics):

    def __init__(self, shell, *kw):
        magic.Magics.__init__(self, shell, *kw)

        # Hex output mode
        self.hex_mode = True
        formatter = self.shell.display_formatter.formatters['text/plain']
        formatter.for_type(int, self.int_formatter)
        formatter.for_type(long, self.int_formatter)

    def int_formatter(self, n, p, cycle):
        if not self.hex_mode:
            return p.text(str(n))
        elif n < 0:
            return p.text("-0x%x" % -n)
        else:
            return p.text("0x%x" % n)

    def _d8(self):
        d8 = self.shell.user_ns.get('d8')
        if not d8:
            raise UsageError('Not connected to the 8051 backdoor. Try %bitbang -8')
        return d8

    @magic.line_magic
    @magic_arguments()
    @argument('enabled', type=int, help='(0 | 1)')
    def hex(self, line):
        """Enable or disable hexadecimal number output mode."""
        args = parse_argstring(self.hex, line)
        self.hex_mode = args.enabled

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Address to read from')
    @argument('size', type=hexint, nargs='?', default=0x100, help='Number of bytes to read')
    @argument('-f', '--fast', action='store_true', help='Go much faster, using somewhat less trustworthy methods')
    @argument('-s', '--space', type=str, default='arm', help='What address space to read from. See dump.py')
    @argument('--check-fast', action='store_true', help='Try fast and slow mode, make sure they match')
    def rd(self, line):
        """Read memory block"""
        args = parse_argstring(self.rd, line)
        d = self.shell.user_ns['d']
        dump(d, args.address, args.size, fast=args.fast, check_fast=args.check_fast, addr_space=args.space)

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Address to read from')
    @argument('size', type=hexint, nargs='?', default=0x100, help='Number of bytes to read')
    def rx8(self, line):
        """Read block of XDATA memory from the 8051"""
        args = parse_argstring(self.rx8, line)
        d8 = self._d8()
        block = d8.xpeek_block(args.address, args.size)
        self.shell.write(hexdump(block, address=args.address & 0xffff))

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Address to read from')
    @argument('wordcount', type=hexint, nargs='?', default=0x100, help='Number of words to read')
    @argument('-f', '--fast', action='store_true', help='Go much faster, using somewhat less trustworthy methods')
    @argument('-s', '--space', type=str, default='arm', help='What address space to read from. See dump.py')
    def rdw(self, line):
        """Read ARM memory block, displaying the result as words"""
        args = parse_argstring(self.rdw, line)
        d = self.shell.user_ns['d']
        dump_words(d, args.address, args.wordcount, fast=args.fast, addr_space=args.space)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address')
    @argument('word', type=hexint, nargs='*', help='Hex words')
    def wrf(self, line, cell='', va=0x500000):
        """Write hex words into the RAM overlay region, then instantly move the overlay into place.
           It's a sneaky trick that looks like a temporary way to write to Flash.

           For example, this patches the signature as it appears in the
           current version of the Backdoor patch itself. Normally this can't
           be modified, since it's in flash:

            : rd c9720 50
            000c9720  ac 42 4c 58 ac 6c 6f 63 ac 65 65 42 ac 6f 6b 42   .BLX.loc.eeB.okB
            000c9730  e6 0c 00 02 a8 00 04 04 c0 46 c0 46 c0 46 c0 46   .........F.F.F.F
            000c9740  7e 4d 65 53 60 31 34 20 76 2e 30 32 20 20 20 20   ~MeS`14 v.02
            000c9750  53 1c 0b 60 16 70 0a 68 53 1c 0b 60 16 70 0a 68   S..`.p.hS..`.p.h
            000c9760  53 1c 0b 60 16 70 0a 68 53 1c 0b 60 16 70 29 88   S..`.p.hS..`.p).

            : wrf c9740 55555555

            : rd c9720 50
            000c9720  ac 42 4c 58 ac 6c 6f 63 ac 65 65 42 ac 6f 6b 42   .BLX.loc.eeB.okB
            000c9730  e6 0c 00 02 a8 00 04 04 c0 46 c0 46 c0 46 c0 46   .........F.F.F.F
            000c9740  55 55 55 55 60 31 34 20 76 2e 30 32 20 20 20 20   UUUU`14 v.02
            000c9750  53 1c 0b 60 16 70 0a 68 53 1c 0b 60 16 70 0a 68   S..`.p.hS..`.p.h
            000c9760  53 1c 0b 60 16 70 0a 68 53 1c 0b 60 16 70 29 88   S..`.p.hS..`.p).

            : sc c ac
            00000000  55 55 55 55 60 31 34 20 76 2e 30 32               UUUU`14 v.02

           """
        args = parse_argstring(self.wr, line)
        d = self.shell.user_ns['d']
        args.word.extend(map(hexint, cell.split()))
        overlay_set(d, va, len(args.word))
        poke_words(d, va, args.word)
        overlay_set(d, args.address, len(args.word))

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address')
    @argument('word', type=hexint, nargs='*', help='Hex words')
    def wr(self, line, cell=''):
        """Write hex words into ARM memory"""
        args = parse_argstring(self.wr, line)
        d = self.shell.user_ns['d']
        args.word.extend(map(hexint, cell.split()))
        poke_words(d, args.address, args.word)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Hex address')
    @argument('byte', type=hexint, nargs='*', help='Hex bytes')
    def wrb(self, line, cell=''):
        """Write hex bytes into ARM memory"""
        args = parse_argstring(self.wrb, line)
        d = self.shell.user_ns['d']
        args.byte.extend(map(hexint, cell.split()))
        poke_bytes(d, args.address, args.byte)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Hex address')
    @argument('byte', type=hexint, nargs='*', help='Hex bytes')
    def wx8(self, line, cell=''):
        """Write hex bytes into 8051 XDATA memory"""
        args = parse_argstring(self.wx8, line)
        d8 = self._d8()
        args.byte.extend(map(hexint, cell.split()))
        d8.xpoke_bytes(args.address, args.byte)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address')
    @argument('word', type=hexint, nargs='*', help='Hex words')
    def orr(self, line, cell=''):
        """Read/modify/write hex words into ARM memory, [mem] |= arg"""
        args = parse_argstring(self.orr, line)
        d = self.shell.user_ns['d']
        args.word.extend(map(hexint, cell.split()))
        for i, w in enumerate(args.word):
            poke_orr(d, args.address + i*4, w)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address')
    @argument('word', type=hexint, nargs='*', help='Hex words')
    def bic(self, line, cell=''):
        """Read/modify/write hex words into ARM memory, [mem] &= ~arg"""
        args = parse_argstring(self.bic, line)
        d = self.shell.user_ns['d']
        args.word.extend(map(hexint, cell.split()))
        for i, w in enumerate(args.word):
            poke_bic(d, args.address + i*4, w)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address')
    @argument('mask', type=hexint, help='Mask of bit(s) to set')
    @argument('bit', type=int, nargs='?', default=1, help='Set or clear the bit?')
    def bitset(self, line, cell=''):
        """Either orr/bic depending on the the value of 'bit'"""
        args = parse_argstring(self.bitset, line)
        d = self.shell.user_ns['d']
        return poke_bit(d, args.address, args.mask, args.bit)

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, help='Hex address, word aligned')
    @argument('word', type=hexint, help='Hex word')
    @argument('count', type=hexint, help='Hex wordcount')
    def fill(self, line):
        """Fill contiguous words in ARM memory with the same value.

        The current impementation uses many poke()s for a general case,
        but values which can be made of a repeating one-byte pattern
        can be filled orders of magnitude faster by using a Backdoor
        command.
        """
        args = parse_argstring(self.fill, line)
        d = self.shell.user_ns['d']
        d.fill(args.address, args.word, args.count)

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint_tuple, nargs='+', help='Single hex address, or a range start:end including both endpoints')
    def watch(self, line):
        """Watch memory for changes, shows the results in an ASCII data table.

        To use the results programmatically, see the watch_scanner() and
        watch_tabulator() functions.

        Keeps running until you kill it with a KeyboardInterrupt.
        """
        args = parse_argstring(self.watch, line)
        d = self.shell.user_ns['d']
        changes = watch_scanner(d, args.address)
        try:
            for line in watch_tabulator(changes):
                self.shell.write(line + '\n')
        except KeyboardInterrupt:
            pass

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint, help='First address to search')
    @argument('size', type=hexint, help='Size of region to search')
    @argument('byte', type=hexint, nargs='+', help='List of bytes to search for, at any alignment')
    @argument('-f', '--fast', action='store_true', help='Go much faster, using somewhat less trustworthy methods')
    @argument('-s', '--space', type=str, default='arm', help='What address space to read from. See dump.py')
    def find(self, line):
        """Read ARM memory block, and look for all occurrences of a byte sequence"""
        args = parse_argstring(self.find, line)
        d = self.shell.user_ns['d']
        substr = ''.join(map(chr, args.byte))

        results = search_block(d, args.address, args.size, substr, fast=args.fast, addr_space=args.space)

        for address, before, after in results:
            self.shell.write("%08x %52s [ %s ] %s\n" %
                (address, hexstr(before), hexstr(substr), hexstr(after)))

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, nargs='?')
    @argument('wordcount', type=hexint, nargs='?', default=1, help='Number of words to remap')
    @argument('-d', '--delay', type=float, default=0.05, metavar='SEC', help='Add a delay between rounds')
    @argument('-p', '--period', type=int, default=8, metavar='N', help='Number of rounds per cycle repeat')
    def bitfuzz(self, line):
        """Scan a small number of words in binary while writing 00000000/ffffffff patterns.
        This can help determine the implementation of bits in an MMIO register.
        """
        args = parse_argstring(self.bitfuzz, line)
        d = self.shell.user_ns['d']
        try:
            for line in bitfuzz_rounds(d, args.address, args.wordcount, args.period, args.delay):
                print line
        except KeyboardInterrupt:
            return

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned, nargs='?')
    @argument('wordcount', type=hexint, nargs='?', default=1, help='Number of words to remap')
    def ovl(self, line):
        """Position a movable RAM overlay at the indicated virtual address range.
        With no parameters, shows the current location of the RAM.

        It can go anywhere in the first 8MB. So, put it between 20_ and 80_, fill it with
        tasty data, then move it overtop of flash. Or see the wrf / asmf commands to do this
        quickly in one step.
        """
        args = parse_argstring(self.ovl, line)
        d = self.shell.user_ns['d']
        if args.address is None:
            self.shell.write("base = %x, wordcount = %x\n" % overlay_get(d))
        else:
            overlay_set(d, args.address, args.wordcount)

    @magic.line_magic
    @magic_arguments()
    @argument('address', type=hexint, help='Hex address')
    @argument('size', type=hexint, nargs='?', default=0x40, help='Hex byte count')
    @argument('-a', '--arm', action='store_true', help='Use 32-bit ARM mode instead of the default Thumb')
    def dis(self, line):
        """Disassemble ARM instructions"""
        args = parse_argstring(self.dis, line)
        d = self.shell.user_ns['d']
        self.shell.write(disassemble(d, args.address, args.size, thumb = not args.arm) + '\n')

    @magic.line_cell_magic
    @magic_arguments()
    @argument('-b', '--base', type=int, default=0, help='First address in map')
    @argument('-s', '--scale', type=int, default=256, help='Scale in bytes per pixel')
    @argument('-w', '--width', type=int, default=4096, help='Size of square hilbert map, in pixels')
    @argument('x', type=int)
    @argument('y', type=int)
    def msl(self, line, cell=''):
        """Memsquare lookup"""
        args = parse_argstring(self.msl, line)
        return int(args.base + args.scale * hilbert(args.x, args.y, args.width))

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned)
    @argument('code', nargs='*')
    def asm(self, line, cell=''):
        """Assemble one or more ARM instructions"""
        args = parse_argstring(self.asm, line)
        d = self.shell.user_ns['d']
        code = ' '.join(args.code) + '\n' + cell
        try:
            assemble(d, args.address, code, defines=all_defines())
        except CodeError, e:
            raise UsageError(str(e))

    @magic.line_cell_magic
    @magic_arguments()
    @argument('address', type=hexint_aligned)
    @argument('code', nargs='*')
    def asmf(self, line, cell='', va=0x500000):
        """Assemble ARM instructions into a patch we instantly overlay onto Flash.
        Combines the 'asm' and 'wrf' commands.
        """
        args = parse_argstring(self.asmf, line)
        d = self.shell.user_ns['d']
        code = ' '.join(args.code) + '\n' + cell
        overlay_assemble(d, args.address, code, defines=all_defines(), va=va)

    @magic.line_magic
    @magic_arguments()
    @argument('vector', type=hexint, nargs='?', help='Vector address to read or set')
    @argument('new_address', type=hexint, nargs='?', help='New address for the indicated vector')
    @argument('--limit', type=hexint, default=0x80, help='Highest address to search for vectors when displaying the full table')
    def ivt(self, line):
        """Read or modify the Interrupt Vector Table"""
        args = parse_argstring(self.ivt, line)
        d = self.shell.user_ns['d']

        if args.vector is None:
            # Show vector table. This only shows vectors with jumps, not
            # vectors that go directly to code.
            for addr in range(0, args.limit, 4):
                value = ivt_get(d, addr)
                if value is not None:
                    self.shell.write("vector %08x = %08x\n" % (addr, value))

        elif args.new_address is None:
            return ivt_get(d, args.vector)

        else:
            ivt_set(d, args.vector, args.new_address)

    @magic.line_cell_magic
    def ec(self, line, cell='', address=target_memory.shell_code):
        """Evaluate a 32-bit C++ expression on the target"""
        d = self.shell.user_ns['d']
        try:
            return evalc(d, line + cell, defines=all_defines(), includes=all_includes(), address=address, verbose=True)
        except CodeError, e:
            raise UsageError(str(e))

    @magic.line_cell_magic
    def ecc(self, line, cell='', address=target_memory.shell_code):
        """Evaluate a 32-bit C++ expression on the target, and immediately start a console
        To ensure we only display output that was generated during the command execution,
        the console is sync'ed and unread output is discarded prior to running the command.
        """
        d = self.shell.user_ns['d']

        ConsoleBuffer(d).discard()

        try:
            return_value = evalc(d, line + cell, defines=all_defines(), includes=all_includes(), address=address, verbose=True)
        except CodeError, e:
            raise UsageError(str(e))

        if return_value is not None:
            display(return_value)
        console_mainloop(d)

    @magic.line_magic
    def ea(self, line, address=target_memory.shell_code, thumb=False):
        """Evaluate an assembly one-liner

        This is an even more reduced and simplified counterpart to %asm,
        like the %ec for assembly.

        - We default to ARM instead of Thumb, since code density is
          not important and we want access to all instructions.
          For thumb, see the %tea variant.

        - Automatically adds a function preamble that saves all registers
          except r0 and r1, which are available for returns.

        - Bridges shell variable r0 on input, and r0-r1 on output.

        - Calls the routine.
        """
        d = self.shell.user_ns['d']
        r0 = int(self.shell.user_ns.get('r0') or 0)

        try:
            r0, r1 = evalasm(d, line, r0, defines=all_defines(), address=address, thumb=thumb)
        except CodeError, e:
            raise UsageError(str(e))

        self.shell.user_ns['r0'] = r0
        self.shell.user_ns['r1'] = r1
        self.shell.write("r0 = 0x%08x, r1 = 0x%08x\n" % (r0, r1))

    @magic.line_magic
    def tea(self, line, address=target_memory.shell_code):
        """Evaluate an assembly one-liner in Thumb mode
        This is a Thumb-mode variant of %ea
        """
        return self.ea(line, address, thumb=True)

    @magic.line_cell_magic
    @magic_arguments()
    @argument('hook_address', type=hexint)
    @argument('handler_address', nargs='?', type=hexint_aligned, default=target_memory.hook_code)
    @argument('-q', '--quiet', action='store_true', help="Just install the hook, don't talk about it")
    @argument('-R', '--reset', action='store_true', help="Reset the ARM before starting")
    @argument('-c', '--console', action='store_true', help='Immediately launch into a %%console after installing')
    @argument('-b', '--bitbang',action='store_true', help='Use bitbang_console() to send output to the bitbang serial port')
    @argument('-f', '--console-file', type=str, default=None, metavar='FILE', help='Append console output to a text file')
    @argument('-d', '--delay', type=float, default=None, metavar='SEC', help='Add a delay loop to the default hook')
    @argument('-m', '--message', type=str, default=None, help='Message to log in the default hook')
    @argument('-r', '--replace', action='store_true', help='Replace the hooked instruction instead of relocating it')
    @argument('-s', '--sram', action='store_true', help='The target already has an SRAM mapping, use that instead of moving the overlay')
    @argument('--console-buffer', type=hexint_aligned, metavar='HEX', default=console_address, help='Specify a different address for the console_buffer_t data structure')
    def hook(self, line, cell=None):
        """Inject a C++ hook into Thumb code executing from Flash memory.

        In line mode, this uses the "default hook" which logs to the console.

        In cell mode, you can write C++ statements that interact with the
        machine state at just prior to executing the hooked instruction. All
        ARM registers are available to read and write, both as named C++
        variables and as a regs[] array.

        The hook and a corresponding interrupt handler are installed at
        handler_address, defaulting to _100.  This command uses the %overlay
        to position an "svc" instruction at the hook location, and the
        generated svc interrupt handler includes a relocated copy of the
        hooked instruction and the necessary glue to get in and out of C++ code.
        """
        args = parse_argstring(self.hook, line)
        d = self.shell.user_ns['d']

        # Hook body is either the cell provided or a trivial default_hook()

        if not cell:
            # Default hook, including our command line as a trace message
            message = args.message or ('%%hook %x' % args.hook_address)
            cell = 'default_hook(regs, %s)' % json.dumps(message)
        elif args.message:
            raise UsageError('--message only applies when using the default hook')

        # Add-ons for any hook body

        if args.delay:
            cell = '%s;\n wait_ms(%d)' % (cell, args.delay * 1000)

        if args.bitbang:
            cell = '%s;\n bitbang_console();' % cell

        try:
            overlay_hook(d, args.hook_address, cell,
                defines = all_defines(),
                includes = all_includes(),
                handler_address = args.handler_address,
                replace_one_instruction = args.replace,
                reset = args.reset,
                verbose = not args.quiet,
                target_already_mapped = args.sram)
        except CodeError, e:
            raise UsageError(str(e))

        if args.console:
            console_mainloop(d, buffer=args.console_buffer, log_filename=args.console_file)

    @magic.line_magic
    @magic_arguments()
    @argument('buffer_address', type=hexint_aligned, nargs='?', default=console_address, help='Specify a different address for the console_buffer_t data structure')
    @argument('-f', type=str, default=None, metavar='FILE', help='Append output to a text file')
    @argument('--slow', action='store_true', help='Use slower but possibly more reliable memory reads')
    def console(self, line):
        """Read console output until KeyboardInterrupt.
        Optionally append the output to a file also.
        To write to this console from C++, use the functions in console.h
        """
        args = parse_argstring(self.console, line)
        d = self.shell.user_ns['d']
        console_mainloop(d, buffer=args.buffer_address, log_filename=args.f,
            use_fast_read = not args.slow)

    @magic.line_cell_magic
    def fc(self, line, cell=None):
        """Define or replace a C++ include definition

        - Without any argument, lists all existing definitions
        - In line mode, stores a one-line function, variable, or structure definition
        - In block mode, stores a multiline function, struct, or class definition

        The key for the includes ditcionary is automatically chosen. In cell mode,
        it's a whitespace-normalized version of the header line. In line mode, it
        extends until the first '{' or '=' character.

        The underlying dictionary is 'includes'. You can remove all includes with:

            includes.clear()

        Example:

            fill _100 1 100
            wr _100 abcdef
            rd _100

            fc uint32_t* words = (uint32_t*) buffer
            buffer = pad + 0x100
            ec words[0]

            %%fc uint32_t sum(uint32_t* values, int count)
            uint32_t result = 0;
            while (count--) {
                result += *(values++);
            }
            return result;

            ec sum(words, 10)

        It's also worth noting that include files are re-read every time you evaluate
        a C++ expression, so a command like this will allow you to edit code in one
        window and interactively run expressions in another:

            fc #include "my_functions.h"

        """
        if cell:
            dict_key = ' '.join(line.split())
            body = "%s {\n%s;\n};\n" % (line, cell)
            includes[dict_key] = body

        elif not line.strip():
            for key, value in includes.items():
                self.shell.write('%s %s %s\n%s\n\n' % (
                    '=' * 10,
                    key,
                    '=' * max(0, 70 - len(key)),
                    value
                ))
        else:
            dict_key = ' '.join(line.split()).split('{')[0].split('=')[0]
            includes[dict_key] = line + ';'

    @magic.line_magic
    @magic_arguments()
    @argument('len', type=hexint, help='Length of input transfer')
    @argument('cdb', type=hexint, nargs='*', help='Up to 12 SCSI CDB bytes')
    def sc(self, line, cell=''):
        """Send a low-level SCSI command with a 12-byte CDB"""
        args = parse_argstring(self.sc, line)
        d = self.shell.user_ns['d']
        cdb = ''.join(map(chr, args.cdb))
        data = scsi_in(d, cdb, args.len)
        self.shell.write(hexdump(data))

    @magic.line_magic
    @magic_arguments()
    @argument('-a', '--arm', action='store_true', help='Try to reset the ARM CPU as well')
    def reset(self, line=''):
        """Reset and reopen the USB interface."""
        args = parse_argstring(self.reset, line)
        d = self.shell.user_ns.get('d_remote')

        if not d:
            # Recover from starting up without a device
            d = remote.Device()
            self.shell.user_ns['d_remote'] = d
            self.shell.user_ns['d'] = d

        d.reset()
        if args.arm:
            reset_arm(d)

    @magic.line_magic
    def eject(self, line=''):
        """Ask the drive to eject its disc."""
        self.sc('0 1b 0 0 0 2')

    @magic.line_magic
    def sc_sense(self, line=''):
        """Send a Request Sense command."""
        self.sc('20 3 0 0 0 20')

    @magic.line_magic
    @magic_arguments()
    @argument('lba', type=hexint, nargs='?', help='Logical Block Address')
    @argument('blockcount', type=hexint, nargs='?', help='Transfer length, in 2kb blocks')
    @argument('-f', type=argparse.FileType('wb'), metavar='FILE', help='Log binary data to a file also')
    def sc_read(self, line, cell=''):
        """Read blocks from the SCSI device.

        You can specify the LBA and address. With no arguments, goes into
        record-player mode and starts reading in order from the beginning.
        This is good if you just want the drive to read anything for testing.
        """
        args = parse_argstring(self.sc_read, line)
        d = self.shell.user_ns['d']
        lba = args.lba or 0

        while True:
            data = scsi_read(d, lba, args.blockcount or 1)
            if args.f:
                args.f.write(data)
                args.f.flush()

            self.shell.write(hexdump(data, address=lba*2048))
            if args.lba is None:
                # sequential mode
                lba += 1
            else:
                # Just one read
                break

    @magic.line_magic
    @magic_arguments()
    @argument('serial_port', type=str, nargs='?', help='Serial port filename to use for reaching the bitbang port')
    @argument('-q', '--quiet', action='store_true', help="Just install the hook, don't talk about it")
    @argument('-e', '--exit', action='store_true', help='Exit an existing bitbang debug session')
    @argument('-a', '--attach', action='store_true', help='Assume bitbang_backdoor() is already running, attach to it')
    @argument('-R', '--reset', action='store_true', help="Reset the ARM before starting")
    @argument('-8', '--cpu8051',action='store_true', help='Install the 8051 backdoor interface ("d8" in the shell)')
    @argument('--address', type=hexint_aligned, default=target_memory.bitbang_backdoor, help='Where to load the bitbang backdoor code. By default this goes just below the console buffer.')
    def bitbang(self, line):
        """Switch to a new debug channel based on a bitbang serial port

        This command switches from the default debug channel (SCSI commands to
        our backdoored firmware) to a new debug channel based on a simple
        hardware modification that adds a serial port to the IO pins used for
        the LED and Eject button.

        This command will run the bitbang_backdoor() C++ function (bitbang.h)
        via the current debug channel. This will put the ARM core into our own
        event loop, with interrupts disabled. It is now waiting for commands
        sent to it over the bitbang serial port, and no other ARM firmware
        runs.

        This will reqiure any common 3.3v USB-serial adapter, soldered to a
        few key points on the drive's main PCB:

            GND                 Many places to get this. I chose a 0-ohm
                                resistor near the motor controller chips.

            RX (from device)    This taps into the signal for the tray LED,
                                but prior to the LED's drive transistor.
                                Here it's a very sharp square wave. The
                                easiest place to grab the signal is the via
                                at pin 10 of the TPIC1391 chip.

            TX (to device)      This drives the eject button signal, which
                                normally has a weak pull-up on it. This signal
                                is on pin 50 of the main PCB's flat cable, but
                                there's a via connected to this pin near the
                                top-left corner of the SoC, and it's much
                                easier to solder there.

        See also:  doc/bitbang-serial-port.jpg
                   doc/hardware-notes.txt

        After %bitbang runs successfully, the default debug device 'd' will be
        the new serial connection. Both devices are available as d_remote and
        d_bitbang, but the bitbang interface is now in the driver's seat.
        """
        args = parse_argstring(self.bitbang, line)
        d = self.shell.user_ns['d']
        d_remote = self.shell.user_ns.get('d_remote')
        d_bitbang = self.shell.user_ns.get('d_bitbang')

        if args.exit:
            if not d_bitbang:
                raise UsageError("No bitbang shell to exit")

            self.shell.write('* Asking bitbang backdoor to exit\n')
            d_bitbang.exit()
            self.shell.user_ns['d_bitbang'] = None
            self.shell.user_ns['d'] = d_remote
            d_remote.reset()

        else:
            if not args.attach and not d_remote:
                raise UsageError("No way in; if the target is already in bitbang mode, try -a")
            if not args.serial_port:
                raise UsageError("Need a hardware serial port; see 'bitbang?' for more info")

            if args.reset:
                print '* Trying to reset... (cycle power if target does not respond)'
                reset_arm(d_remote)

            if not args.attach:
                bitbang_backdoor(d_remote, args.address, verbose=not args.quiet)

            self.shell.write('* Connecting to bitbang backdoor via %s\n' % args.serial_port)
            d_bitbang = BitbangDevice(args.serial_port)

            self.shell.user_ns['d_bitbang'] = d_bitbang
            self.shell.user_ns['d'] = d_bitbang

        d = self.shell.user_ns['d']
        self.shell.write('* Debug interface switched to %r\n' % d)

        if args.cpu8051:
            self.shell.user_ns['d8'] = cpu8051_backdoor(d)

    @magic.line_magic
    @magic_arguments()
    @argument('-l', '--log', type=argparse.FileType('a'), default='trace.log', metavar='FILE', help='Append logs to a file')
    @argument('-r', '--reset', type=hexint, help='Reset the processor, sending it to the indicated vector')
    @argument('-c', '--continuous', action='store_true', help='Keep taking steps until interrupted')
    @argument('-b', '--breakpoint', type=hexint, help='Run until the program counter matches')
    @argument('-S', '--save', type=str, metavar='FILE', help='Save local simulation state to files')
    @argument('-L', '--load', type=str, metavar='FILE', help='Load local simulation state from files')
    @argument('steps', nargs='?', type=int, help='Number of steps to take (decimal int)')
    def sim(self, line):
        """Take a step in a simulated ARM processor.

        The first time you call %sim, it creates a simulation state object as
        'arm' in the shell. Afterwards, %sim by default takes a single step,
        and bridges simulated registers to and from shell variables.
        """
        args = parse_argstring(self.sim, line)
        ns = self.shell.user_ns
        d = ns['d']
        arm = ns.get('arm')
        steps = args.steps
        state = 'idle'
        logfile = args.log
        if args.continuous or args.breakpoint:
            steps = 1e100
        pc_break = (args.breakpoint or -1) & 0xfffffffe

        if arm:
            # Update existing ARM object, default to 1 step
            if steps is None: steps = 1
            arm.copy_registers_from(ns)
            arm.device = d
        else:
            # New simulator object, default to 0 steps
            if steps is None: steps = 0
            arm = simulate_arm(d)
            ns['arm'] = arm
            self.shell.write('- initialized simulation state\n')
            state = 'INIT'
            arm.copy_registers_to(ns)

            # Simulator shouldn't see the overlay, make sure this is off
            overlay_set(d, None)

        arm.memory.logfile = logfile

        if args.load:
            arm.load_state(args.load)
            arm.copy_registers_to(ns)
            steps = 0

        if args.reset is not None:
            state = 'RST'
            arm.reset(args.reset)

        if args.save:
            arm.save_state(args.save)
            steps = 0

        min_timestamp = 0

        # Capture 'print' output from hook functions
        saved_stdout = sys.stdout
        sys.stdout = Tee(self.shell, logfile)

        try:
            while True:
                if steps > 0:
                    state = 'step'
                    arm.step()
                    steps -= 1
                    arm.copy_registers_to(ns)

                # Throttled summary output to shell
                now = time.time()
                if now >= min_timestamp:
                    self.shell.write('[%4s] %-70s %s\n' % (state, arm.summary_line(), arm.register_trace_line(8)))
                    min_timestamp = now + 0.25

                # Write detailed output to log file
                logfile.write('# %-70s %s\n' % (arm.summary_line(), arm.register_trace_line()))
                assert logfile == arm.memory.logfile

                if (arm.regs[15] & ~1) == pc_break:
                    self.shell.write('- breakpoint reached\n%s' % arm.register_trace())
                    break

                if steps == 0:
                    self.shell.write(arm.register_trace())
                    break
        finally:
            sys.stdout = saved_stdout
            logfile.flush()


class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, s):
        for f in self.files:
            f.write(s)

