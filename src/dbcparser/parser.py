#import six
import re


# Nested parsing design
#   As the DBC file is parsed, each nested block of code is compartmentalised
#   with a nested parser instance.
#   Each StreamParser iterates through the given stream object, shifting its
#   cursor until the parser finds code it deems invalid, or EOF.


# Optimum chunk size?
#   Too large: each stream character will be read multiple times
#              (because the file's cursor is decreased for each line found)
#   Too small: takes more runtime to process.
#
#   Since, in this relatively simple case, runtime is cheap, a lower chunk
#   size is favorable.
#
#   On a cursory look through DBC files, lines are typically ~50 characters
#   in length. So setting the chunk size to ~20% line size will require 5
#   loops to process 1 line... a respectable trade-off.
CHUNK_SIZE = 10


# --------- Exceptions
class DBCSyntaxError(ValueError):
    pass



# --------- Base Parser
class StreamParser(object):
    REGEX = None

    def __init__(self, stream, stack=[]):
        self.stream = stream
        self.stack = stack

    @classmethod
    def new_from(cls, other):
        """
        ::

            message_parser = MessageParser.new_from(self)
        """
        return cls(
            stream=other.stream,
            stack=other.stack,
        )

    def parse(self):
        raise NotImplementedError()

    def push(self, line):
        self.stack.append(line)

    def pop(self):
        return self.stack.pop(0)

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

        # empty stack before pulling new data
        while self.stack:
            yield self.pop()

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
                else:  # True if for loop did not `break`
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
    def parse(self):
        pass


class LineObject(object):
    TYPE_MAP = {}

    @classmethod
    def from_line(cls, line):
        """
        Builds an instance from the given line.

        If the line does not match ``cls.REGEX``, ``None`` is returned.

        :return: instance of this class, or None
        :rtype: ``cls``
        """
        match = cls.REGEX.search(line)
        if match:
            return cls(**match.groupdict())
        return None

    def __init__(self, **kwargs):
        for (k, v) in kwargs.items():
            setattr(self, k, self.TYPE_MAP.get(k, str))


class Message(LineObject):
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

    TYPE_MAP = {
        'address': int,
        'name': str,
        'dlc': int,
        'transmitter': str,
    }

class Signal(LineObject):
    # Examples:
    #   SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF
    #   SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX
    #   SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX
    REGEX = re.compile(r'''
        ^\s*SG_\s+                  # line start, can be tabbed in (fault tolerant)
        (?P<name>\S+)\s*            # signal name
        (?P<mux>(M|m\d+))?\s*:\s*   # message multiplexing: M index, m1 signal where index is 1
        (?P<start>\d+)\s*\|\s*      # start bit
        (?P<length>\d+)\s*@\s*      # length (bits)
        (?P<endianness>[01])\s*     # 0 motorola, 1 intel
        (?P<signed>[+-])\s*         # - signed, + not signed
        \(
            \s*(?P<factor>[^,]+?)\s*,   # factor
            \s*(?P<offset>[^\)]+?)\s*   # offset
        \)\s*
        \[
            \s*(?P<min>[^,]+?)\s*\|     # minimum value
            \s*(?P<max>[^\]]+?)\s*      # maximum value
        \]\s*
        "(?P<unit>[^"]*)"\s*        # unit string: eg: sec, Amps, DegC
        (?P<receivers>.*?)          # receivers, a csv list
        \s*$                        # end of line
    ''', re.VERBOSE)



class SignalComment(LineObject):
    # Examples:
    #   CM_ SG_ 2164239169 SignalName "this is the comment";
    #   CM_ SG_ 123 SignalName2 "this comment
    #   extends over multiple lines";
    REGEX = re.compile(r'''
        ^CM_\s+SG_\s+           # line start
        (?P<address>\d+)\s+     # message address
        (?P<name>[^\s"]+)\s*    # signal name
        "(?P<comment>.*)"\s*    # comment
        ;\s*$                   # end of line
    ''', re.MULTILINE | re.DOTALL | re.VERBOSE)
