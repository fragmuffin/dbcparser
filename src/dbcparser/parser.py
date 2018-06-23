#import six
import re


# Nested parsing design
#   As the DBC file is parsed, each nested block of code is compartmentalised
#   with a nested parser instance.
#   Each StreamParser iterates through the given stream object, shifting its
#   cursor until the parser finds code it deems invalid, or EOF.


# Optimum chunk size?
#   Too large: each character will be read in multiple times
#              (because the file's cursor is rewound for each line found)
#   Too small: takes more runtime to process.
#
#   Since, in this relatively simple case, runtime is cheap, a lower chunk
#   size is favorable.
#
#   On a cursory look through DBC files, lines are typically ~50 characters
#   in length. So setting the chunk size ot ~20% line size will require 5
#   loops to process 1 line... a respectable trade-off.
CHUNK_SIZE = 10


class DBCSyntaxError(ValueError):
    pass


class StreamParser(object):
    REGEX = None

    def __init__(self, stream):
        self.stream = stream

    def parse(self):
        raise NotImplementedError()


    def iter(self):
        r"""
        Generator that yields one *line* each iteration.

        Before yielding, the stream is seeked to just after the ``\n`` denoting
        the end of the line.
        This allows for nested parsing of the same stream.

        **Define "line"**

        A line ends with a ``\n`` unless it's inside a string (``""``).
        So technically a *dbc line* may span over multiple lines.

        **Escape character?**

        Strings in a properly formatted dbc file *don't* contain ``"``
        characters. So no; special characters *cannot* be escaped and used
        inside a string.
        """

        chr_regex = re.compile(r'["\n]')  # match: quotes || new-line
        string_state = False  # not inside "" quotes

        while True:  # per line
            line = ''

            while True:  # per chunk
                chunk = self.stream.read(CHUNK_SIZE)
                if not chunk:
                    break  # EOF
                line += chunk  # to be stripped if newline found inside chunk

                for m in chr_regex.finditer(chunk):
                    if m.group() == '"':
                        string_state = not string_state
                    elif not string_state:  # == '\n'
                        # rewind stream to start of the next line
                        chunk_excess = len(chunk) - m.end()
                        self.stream.seek(self.stream.tell() - chunk_excess)
                        line = line[:len(line) - chunk_excess]
                        break  # will return line
                else:
                    continue
                break

            # return a line if there's something to return, otherwise EOF
            if line:
                if string_state:  # still inside a string, line is invalid
                    raise DBCSyntaxError("String was not closed before end of DBC line")
                yield line
            else:
                break


class DBCParser(StreamParser):
    pass


class MessageParser(StreamParser):
    # Examples:
    #   BO_ 2566903475 ConverterInputOutput: 8 DCDC
    #   BO_ 1258 PDORx4_Inv1: 8 INV_1
    #   BO_ 263 Batt107: 4 Vector__XXX
    REGEX = re.compile(r'''
        ^BO_\s+                 # line start
        (?P<address>\d+)\s*     # address (decimal)
        (?P<name>\S+)\s*:\s*    # message name
        (?P<dlc>\d+)\s+         # dlc
        (?P<transmitter>\S+)    # transmitter, mandatory, only 1
        \s*$                    # line end
    ''', re.VERBOSE)


class SignalParser(StreamParser):
    # Examples:
    #   SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF
    #   SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX
    #   SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX
    REGEX = re.compile(r'''
        ^\s*SG_\s+                  # line start, can be tabbed in (fault tolerant)
        (?P<name>\S+)\s*            # signal name
        (?P<mux>m\d*)?\s*:\s*       # message multiplexing: M index, m1 signal where index is 1
        (?P<start>\d+)\s*\|\s*      # start bit
        (?P<length>\d+)\s*@\s*      # length (bits)
        (?P<signed>\d+)\s*          # signed
        (?P<endianness>(-|\+))\s+   # + motorola, - intel
        \(
            (?P<factor>[^,]+),      # factor
            (?P<offset>[^\)]+)      # offset
        \)\s*
        \[
            (?P<min>[^,]+),         # minimum value
            (?P<max>[^\]]+)         # maximum value
        \]\s*
        "(?P<unit>[^"]*)"\s*        # unit string: eg: sec, Amps, DegC
        (?P<receivers>.*)           # receivers, a csv list
        \s*$                        # end of line
    ''', re.VERBOSE)


class SignalCommentParser(StreamParser):
    # Examples:
    #   CM_ SG_ 2164239169 SignalName "this is the comment";
    #   CM_ SG_ 123 SignalName2 "this comment
    #   extends over multiple lines";
    REGEX = re.compile(r'''
        ^CM_\s+ST_\s+           # line start
        (?P<address>\d+)\s+     # message address
        "(?P<comment>.*)"\s+    # comment
        ;\s*$                   # end of line
    ''', re.MULTILINE | re.VERBOSE)
