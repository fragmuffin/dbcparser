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

    def line_iter(self):
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
    REGEX = None  # overridden to be a: _sre.SRE_Pattern (return from re.compile)
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

    def dict(self):
        """
        Return this object as a dict

        :return: object with each attribute as a dict key/value pair
        :rtype: :class:`dict`
        """
        return {
            v: getattr(self, v)
            for v in self.REGEX.groupindex.keys()
        }

    def __init__(self, **kwargs):
        for (key, val) in kwargs.items():
            if val is None:
                setattr(self, key, None)
            else:
                setattr(self, key, self.TYPE_MAP.get(key, str)(val))


# --- Types
def _t_transmitter(value):
    if value == 'Vector__XXX':  # Null node
        return None
    return value

def _t_endianness(value):
    return value == '1'

def _t_signed(value):
    return value == '-'

def _t_receivers(value):
    return [
        rx.strip() for rx in value.split(',')
        if rx != 'Vector__XXX'  # Null node
    ]

def _t_node_list(value):
    return [
        node for node in re.split(r'\s+', value)
        if node  # remove ''
    ]

_t_enum_list_regex = re.compile(r'(\d+)\s*"([^"]*)"')
def _t_enum_list(value):
    enums = {}
    for m in _t_enum_list_regex.finditer(value):
        (k, v) = m.groups()
        enums[int(k)] = v
    return enums


class Frame(LineObject):
    # Examples:
    #   BO_ 2566903475 ConverterInputOutput: 8 DCDC
    #   BO_ 1258 PDORx4_Inv1: 8 INV_1
    #   BO_ 263 Batt107: 4 Vector__XXX
    REGEX = re.compile(r'''
        ^BO_\s+                 # line start
        (?P<address>\d+)\s*     # address (decimal)
        (?P<name>\S+)\s*:\s*    # frame name
        (?P<dlc>\d+)\s+         # dlc
        (?P<transmitter>\S+)    # transmitter, mandatory, only 1
        \s*$                    # line end
    ''', re.VERBOSE)

    TYPE_MAP = {
        'address': int,
        'name': str,
        'dlc': int,
        'transmitter': _t_transmitter,
    }


class Signal(LineObject):
    # Examples:
    #   SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF
    #   SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX
    #   SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX
    REGEX = re.compile(r'''
        ^\s*SG_\s+                  # line start, can be tabbed in (fault tolerant)
        (?P<name>\S+)\s*            # signal name
        (?P<mux>(M|m\d+))?\s*:\s*   # frame multiplexing: M index, m1 signal where index is 1
        (?P<start>\d+)\s*\|\s*      # start bit
        (?P<length>\d+)\s*@\s*      # length (bits)
        (?P<little_endian>[01])\s*  # 0 big endian, 1 little endian
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

    TYPE_MAP = {
        'name': str,
        'mux': str,
        'start': int,
        'length': int,
        'little_endian': _t_endianness,
        'signed': _t_signed,
        'factor': float,
        'offset': float,
        'min': float,
        'max': float,
        'unit': str,
        'receivers': _t_receivers,
    }


class SignalComment(LineObject):
    # Examples:
    #   CM_ SG_ 2164239169 SignalName "this is the comment";
    #   CM_ SG_ 123 SignalName2 "this comment
    #   extends over multiple lines";
    REGEX = re.compile(r'''
        ^CM_\s+SG_\s+           # line start
        (?P<address>\d+)\s+     # frame address
        (?P<name>\w+)\s*        # signal name
        "(?P<comment>.*)"\s*    # comment
        ;\s*$                   # end of line
    ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    TYPE_MAP = {
        'address': int,
        'name': str,
        'comment': str,
    }


class FrameComment(LineObject):
    # Examples:
    #   CM_ BO_ 2365573367  "Fault bits.";
    #   CM_ BO_ 123  "multiline comment
    #   spans multiple lines... go figure!";
    REGEX = re.compile(r'''
        ^CM_\s+BO_\s+           # line start
        (?P<address>\d+)\s+     # frame address
        "(?P<comment>.*)"\s*    # comment
        ;\s*$                   # end of line
    ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    TYPE_MAP = {
        'address': int,
        'comment': str,
    }


class NodeList(LineObject):
    # Examples:
    #   BU_ ABC DEF
    #   BU_ Node1 INV_1 AUX
    REGEX = re.compile(r'''
        ^BU_\s*:\s*         # line start
        (?P<nodes>.*)\s*    # nodes list (space separated)
        $                   # line end
    ''', re.VERBOSE)

    TYPE_MAP = {
        'nodes': _t_node_list,
    }


class NodeComment(LineObject):
    # Example:
    #   CM_ BU_ testBU "sender ECU";
    #   CM_ BU_ NodeX "comment over
    #   multiple lines";
    REGEX = re.compile(r'''
        ^CM_\s+BU_\s+           # line start
        (?P<node>\S+)\s+        # node name
        "(?P<comment>.*)"\s*    # comment
        ;\s*$                   # line end
    ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    TYPE_MAP = {
        'node': str,
        'comment': str,
    }


class Enumeration(LineObject):
    # Example:
    #   VAL_ 291 Signal 1 "one" 2 "two" 3 "three";
    REGEX = re.compile(r'''
        ^VAL_\s+            # line start
        (?P<address>\d+)\s+ # frame address
        (?P<signal>\S+)\s+  # signal name
        (?P<enums>(
            \d+\s*          # value (decimal)
            "[^"]*"\s*      # enumeration name
        )+)\s*              # one or many
        ;\s*$               # line end
    ''', re.VERBOSE)

    TYPE_MAP = {
        'address': int,
        'signal': str,
        'enums': _t_enum_list,
    }


class ValueTable(LineObject):
    # Example:
    #   VAL_TABLE_ Baudrate 0 "125K" 1 "250K" 2 "500K" 3 "1M";
    REGEX = re.compile(r'''
        ^VAL_TABLE_\s+      # line start
        (?P<table>\S+)\s+   # table name
        (?P<enums>(
            \d+\s*          # value (decimal)
            "[^"]*"\s*      # enumeration name
        )+)\s*              # one or many
        ;\s*$               # line end
    ''', re.VERBOSE)

    TYPE_MAP = {
        'tble': str,
        'enums': _t_enum_list,
    }


# ----- Defines
class GlobalDefine(LineObject):
    # Examples:
    #   BA_DEF_ "Thingy" INT 0 65535;
    REGEX = re.compile(r'''
        ^BA_DEF_\s*             # line start
        "(?P<name>[^"]*)"\s*    # name
        (?P<type>\S+)           # type
        (\s+(?P<params>.*))?\s* # type parameters
        ;\s*$                   # line end
    ''', re.VERBOSE)

    TYPE_MAP = {
        'name': str,
    }

    def __init__(self, **kwargs):
        # Set type from (type_str, params) pair
        type_str = kwargs.pop('type')
        params = kwargs.pop('params')

        # Map type
        self.type = {
            'STR': str, 'STRING': str,
            'INT': int,
            'HEX': int,
            'FLOAT': float,
            'BOOL': bool,
            'ENUM': tuple,
        }[type_str]

        # Set type-specific attributes
        if self.type in (int, float):
            # min, max
            self.params = tuple(
                self.type(v) for v in re.split(r'\s+', params)
            )
        elif self.type is tuple:  # ENUM
            # enums
            value_regex = re.compile(r'"(?P<val>[^"]+)"')
            self.params = self.type(
                m.group('val').strip()
                for m in value_regex.finditer(params)
            )
        elif self.type is bool:
            self.params = tuple(
                v.lower() == 'true'
                for v in re.split('\s+', params)
                if v  # ignore blanks
            )
        else:
            self.params = None

        super(GlobalDefine, self).__init__(**kwargs)


class SignalDefine(GlobalDefine):
    # Examples:
    #   BA_DEF_ SG_ "DisplayDecimalPlaces" INT 0 65535;
    #   BA_DEF_ SG_ "GenSigStartValue" FLOAT -3.4E+038 3.4E+038;
    #   BA_DEF_ SG_ "HexadecimalOutput" BOOL False True;
    #   BA_DEF_ SG_ "LongName" STR;
    REGEX = re.compile(r'''
        ^BA_DEF_\s+SG_\s*       # line start
        "(?P<name>[^"]*)"\s*    # name
        (?P<type>\S+)           # type
        (\s+(?P<params>.*))?\s* # type parameters
        ;\s*$                   # line end
    ''', re.VERBOSE)


class FrameDefine(GlobalDefine):
    # Examples:
    #   BA_DEF_ BO_ "GenMsgCycleTime" INT 0 65535;
    #   BA_DEF_ BO_ "Receivable" BOOL False True;
    REGEX = re.compile(r'''
        ^BA_DEF_\s+BO_\s*       # line start
        "(?P<name>[^"]*)"\s*    # name
        (?P<type>\S+)           # type
        (\s+(?P<params>.*))?\s* # type parameters
        ;\s*$                   # line end
    ''', re.VERBOSE)


class NodeDefine(GlobalDefine):
    # Examples:
    #   BA_DEF_ BU_ "NWM-Knoten" ENUM  "nein","ja";
    #   BA_DEF_ BU_ "NWM-Stationsadresse" HEX 0 63;
    REGEX = re.compile(r'''
        ^BA_DEF_\s+BU_\s*       # line start
        "(?P<name>[^"]*)"\s*    # name
        (?P<type>\S+)           # type
        (\s+(?P<params>.*))?\s* # type parameters
        ;\s*$                   # line end
    ''', re.VERBOSE)


# ----- Attributes
# TODO


# ======= TODO:

# ----- Attributes
# Global Attribute
"^BA_ +\"([A-Za-z0-9\-\_]+)\" +([\"A-Za-z0-9\-\_\.]+);"

# Frame Attribute
"^BA_ +\"(.*)\" +BO_ +(\w+) +(.+);"

# Signal Attribute
"^BA_ +\"(.*)\" +SG_ +(\w+) +(\w+) +(.+);"

# Node Attribute
"^BA_ +\"(.*)\" +BU_ +(\w+) +(.+);"

# ----- Other
# Signal Group
"^SIG_GROUP_ +(\w+) +(\w+) +(\w+) +\:(.*);"

# Signal Value Type
"^SIG_VALTYPE_ +(\w+) +(\w+) +\:(.*);"

# Default Value
"^BA_DEF_DEF_ +\"([A-Za-z0-9\-_\.]+)\" +(.+)\;"

# ?
"^BO_TX_BU_ ([0-9]+) *: *(.+);"

# ?
"^SG_MUL_VAL_ +([0-9]+) +([A-Za-z0-9\-_]+) +([A-Za-z0-9\-_]+) +([0-9]+)\-([0-9]+) *;"
