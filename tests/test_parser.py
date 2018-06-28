import unittest
import io
import mock

# Objects under test
import dbcparser.parser


class StreamParserTests(unittest.TestCase):

    def test_simple_lines(self):
        lines = [
            'simple',
            '"line starts" with a string',
            'line with "a string at the end"',
            'line with a "string" in the middle',
            'line extends "over\nmultiple" lines',
            'this "line" has "multiple" strings',
            'last line has no newline char',
        ]
        stream = io.StringIO('\n'.join(lines))
        p = dbcparser.parser.StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.line_iter()],
            lines,
        )

    def test_empty_stream(self):
        stream = io.StringIO('')
        p = dbcparser.parser.StreamParser(stream)
        self.assertEqual(list(p.line_iter()), [])

    @mock.patch('dbcparser.parser.CHUNK_SIZE', 1)
    def test_small_chunk_size(self):
        lines = [
            'simple',
            '"line starts" with a string',
            'line with "a string at the end"',
        ]
        stream = io.StringIO('\n'.join(lines))
        p = dbcparser.parser.StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.line_iter()],
            lines,
        )

    @mock.patch('dbcparser.parser.CHUNK_SIZE', 0x1000)  # consumes whole stream
    def test_large_chunk_size(self):
        lines = [
            'simple',
            '"line starts" with a string',
            'line with "a string at the end"',
        ]
        stream = io.StringIO('\n'.join(lines))
        p = dbcparser.parser.StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.line_iter()],
            lines,
        )

    def test_empty_lines(self):
        lines = [
            '',  # 1st line empty
            'line 2',
            '',  # 3rd line empty
            'line 4',
            '',  # last line empty
        ]
        stream = io.StringIO('\n'.join(lines) + '\n')  # force newline char at EOF
        p = dbcparser.parser.StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.line_iter()],
            lines,
        )

    def test_unclosed_str(self):
        stream = io.StringIO('foo "bar')
        p = dbcparser.parser.StreamParser(stream)
        with self.assertRaises(dbcparser.parser.DBCSyntaxError):
            list(p.line_iter())


class FrameTests(unittest.TestCase):
    def test_simple1(self):
        line = 'BO_ 2566903475 ConverterInputOutput: 8 DCDC'
        obj = dbcparser.parser.Frame.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 2566903475,
            'name': 'ConverterInputOutput',
            'dlc': 8,
            'transmitter': 'DCDC',
        })

    def test_simple2(self):
        line = 'BO_ 1258 PDORx4_Inv1: 8 INV_1'
        obj = dbcparser.parser.Frame.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 1258,
            'name': 'PDORx4_Inv1',
            'dlc': 8,
            'transmitter': 'INV_1',
        })

    def test_simple3(self):
        line = 'BO_ 263 Batt107: 4 Vector__XXX'
        obj = dbcparser.parser.Frame.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 263,
            'name': 'Batt107',
            'dlc': 4,
            'transmitter': None,
        })

    def test_whitespace_lots(self):
        line = 'BO_  263  Batt107  :  4  Vector__XXX  '
        obj = dbcparser.parser.Frame.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 263,
            'name': 'Batt107',
            'dlc': 4,
            'transmitter': None,
        })

    def test_whitespace_minimum(self):
        line = 'BO_ 263 Batt107:4 Vector__XXX'
        obj = dbcparser.parser.Frame.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 263,
            'name': 'Batt107',
            'dlc': 4,
            'transmitter': None,
        })


class SignalTests(unittest.TestCase):
    def test_signal_simple(self):
        line = 'SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF'
        obj = dbcparser.parser.Signal.from_line(line)
        self.assertEqual(obj.dict(), {
            'name': 'Frequency_command',
            'mux': None,
            'start': 23, 'length': 16,
            'little_endian': False, 'signed': False,
            'factor': 0.1, 'offset': 0.,
            'min': 45., 'max': 65.,
            'unit': 'Hz',
            'receivers': ['ABC', 'DEF'],
        })

    def test_signal_mux_id(self):
        line = 'SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX'
        obj = dbcparser.parser.Signal.from_line(line)
        self.assertEqual(obj.dict(), {
            'name': 'CommandSetNVParam_MUX',
            'mux': 'M',
            'start': 7, 'length': 16,
            'little_endian': False, 'signed': True,
            'factor': 1., 'offset': 0.,
            'min': -32768., 'max': 32767.,
            'unit': '',
            'receivers': [],
        })

    def test_signal_mux_signal(self):
        line = 'SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX'
        obj = dbcparser.parser.Signal.from_line(line)
        self.assertEqual(obj.dict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': 23, 'length': 16,
            'little_endian': False, 'signed': False,
            'factor': 1., 'offset': 0.,
            'min': 0., 'max': 65535,
            'unit': '',
            'receivers': [],
        })

    def test_signal_whitespace_lots(self):
        line = '  SG_  Dummy  m0  :  23  |  16  @  0  +  (  1  ,  0  )  [  0  |  65535  ] ""  Vector__XXX  '
        obj = dbcparser.parser.Signal.from_line(line)
        self.assertEqual(obj.dict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': 23, 'length': 16,
            'little_endian': False, 'signed': False,
            'factor': 1., 'offset': 0.,
            'min': 0., 'max': 65535.,
            'unit': '',
            'receivers': [],
        })

    def test_signal_whitespace_minimum(self):
        line = 'SG_ Dummy m0:23|16@0+(1,0)[0|65535]""Vector__XXX'
        obj = dbcparser.parser.Signal.from_line(line)
        self.assertEqual(obj.dict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': 23, 'length': 16,
            'little_endian': False, 'signed': False,
            'factor': 1., 'offset': 0.,
            'min': 0., 'max': 65535.,
            'unit': '',
            'receivers': [],
        })

class SignalCommentTests(unittest.TestCase):
    def test_simple(self):
        line = 'CM_ SG_ 2164239169 SignalName "this is the comment";'
        obj = dbcparser.parser.SignalComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 2164239169,
            'name': 'SignalName',
            'comment': 'this is the comment',
        })

    def test_multiline(self):
        line = 'CM_ SG_ 123 SignalName2 "this comment \nextends over multiple lines";'
        obj = dbcparser.parser.SignalComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 123,
            'name': 'SignalName2',
            'comment': 'this comment \nextends over multiple lines',
        })

    def test_whitespace_lots(self):
        line = 'CM_  SG_  2164239169  SignalName  "this is the comment" ;  '
        obj = dbcparser.parser.SignalComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 2164239169,
            'name': 'SignalName',
            'comment': 'this is the comment',
        })

    def test_whitespace_minimum(self):
        line = 'CM_ SG_ 2164239169 SignalName"this is the comment";'
        obj = dbcparser.parser.SignalComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 2164239169,
            'name': 'SignalName',
            'comment': 'this is the comment',
        })


class FrameCommentTests(unittest.TestCase):
    def test_simple(self):
        line = 'CM_ BO_ 2365573367  "Fault bits.";'
        obj = dbcparser.parser.FrameComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 2365573367,
            'comment': 'Fault bits.',
        })

    def test_multiline(self):
        line = 'CM_ BO_ 123  "multiline comment\nspans multiple lines... go figure!";'
        obj = dbcparser.parser.FrameComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 123,
            'comment': 'multiline comment\nspans multiple lines... go figure!',
        })

    def test_whitespace_lots(self):
        line = 'CM_  BO_  321  "commentz" ;  '
        obj = dbcparser.parser.FrameComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 321,
            'comment': 'commentz',
        })


class NodeListTests(unittest.TestCase):
    def test_simple(self):
        line = 'BU_: ABC DEF'
        obj = dbcparser.parser.NodeList.from_line(line)
        self.assertEqual(obj.dict(), {
            'nodes': ['ABC', 'DEF'],
        })

    def test_empty(self):
        line = 'BU_:'
        obj = dbcparser.parser.NodeList.from_line(line)
        self.assertEqual(obj.dict(), {
            'nodes': [],
        })

    def test_whitespace_lots(self):
        line = 'BU_  :  ABC  DEF  '
        obj = dbcparser.parser.NodeList.from_line(line)
        self.assertEqual(obj.dict(), {
            'nodes': ['ABC', 'DEF'],
        })

    def test_whitespace_minimum(self):
        line = 'BU_:ABC DEF'
        obj = dbcparser.parser.NodeList.from_line(line)
        self.assertEqual(obj.dict(), {
            'nodes': ['ABC', 'DEF'],
        })


class NodeCommentTests(unittest.TestCase):
    def test_simple(self):
        line = 'CM_ BU_ testBU "sender ECU";'
        obj = dbcparser.parser.NodeComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'node': 'testBU',
            'comment': 'sender ECU',
        })

    def test_multiline(self):
        line = 'CM_ BU_ NodeX "comment over\nmultiple lines";'
        obj = dbcparser.parser.NodeComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'node': 'NodeX',
            'comment': 'comment over\nmultiple lines',
        })

    def test_whitespace_lots(self):
        line = 'CM_  BU_  testBU  "sender ECU"  ;  '
        obj = dbcparser.parser.NodeComment.from_line(line)
        self.assertEqual(obj.dict(), {
            'node': 'testBU',
            'comment': 'sender ECU',
        })


class EnumerationTests(unittest.TestCase):
    def test_simple(self):
        line = 'VAL_ 291 Signal 1 "one" 2 "two" 3 "three";'
        obj = dbcparser.parser.Enumeration.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 291,
            'signal': 'Signal',
            'enums': {1: 'one', 2: 'two', 3: 'three'},
        })

    def test_singular(self):
        line = 'VAL_ 123 Foo 100 "bar";'
        obj = dbcparser.parser.Enumeration.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 123,
            'signal': 'Foo',
            'enums': {100: 'bar'},
        })

    def test_whitespace_lots(self):
        line = 'VAL_  291  Signal  1  "one with spaces"  2  "two"  3  "three"  ;  '
        obj = dbcparser.parser.Enumeration.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 291,
            'signal': 'Signal',
            'enums': {1: 'one with spaces', 2: 'two', 3: 'three'},
        })

    def test_whitespace_minimum(self):
        line = 'VAL_ 291 Signal 1"one"2"two"3"three";'
        obj = dbcparser.parser.Enumeration.from_line(line)
        self.assertEqual(obj.dict(), {
            'address': 291,
            'signal': 'Signal',
            'enums': {1: 'one', 2: 'two', 3: 'three'},
        })


class ValueTableTests(unittest.TestCase):
    def test_simple(self):
        line = 'VAL_TABLE_ Relay 0 "Open" 1 "Closed" 2 "Error" 3 "N/A";'
        obj = dbcparser.parser.ValueTable.from_line(line)
        self.assertEqual(obj.dict(), {
            'table': 'Relay',
            'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
        })

    def test_whitespace_lots(self):
        line = 'VAL_TABLE_  Relay  0  "Open"  1  "Closed"  2  "Error"  3  "N/A"  ;  '
        obj = dbcparser.parser.ValueTable.from_line(line)
        self.assertEqual(obj.dict(), {
            'table': 'Relay',
            'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
        })

    def test_whitespace_minimum(self):
        line = 'VAL_TABLE_ Relay 0"Open"1"Closed"2"Error"3"N/A";'
        obj = dbcparser.parser.ValueTable.from_line(line)
        self.assertEqual(obj.dict(), {
            'table': 'Relay',
            'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
        })
