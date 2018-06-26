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
            [l.rstrip('\n') for l in p.iter()],
            lines,
        )

    def test_empty_stream(self):
        stream = io.StringIO('')
        p = dbcparser.parser.StreamParser(stream)
        self.assertEqual(list(p.iter()), [])

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
            [l.rstrip('\n') for l in p.iter()],
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
            [l.rstrip('\n') for l in p.iter()],
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
            [l.rstrip('\n') for l in p.iter()],
            lines,
        )

    def test_unclosed_str(self):
        stream = io.StringIO('foo "bar')
        p = dbcparser.parser.StreamParser(stream)
        with self.assertRaises(dbcparser.parser.DBCSyntaxError):
            list(p.iter())


class MessageTests(unittest.TestCase):
    def test_simple1(self):
        line = 'BO_ 2566903475 ConverterInputOutput: 8 DCDC'
        match = dbcparser.parser.Message.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '2566903475',
            'name': 'ConverterInputOutput',
            'dlc': '8',
            'transmitter': 'DCDC',
        })

    def test_simple2(self):
        line = 'BO_ 1258 PDORx4_Inv1: 8 INV_1'
        match = dbcparser.parser.Message.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '1258',
            'name': 'PDORx4_Inv1',
            'dlc': '8',
            'transmitter': 'INV_1',
        })

    def test_simple3(self):
        line = 'BO_ 263 Batt107: 4 Vector__XXX'
        match = dbcparser.parser.Message.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '263',
            'name': 'Batt107',
            'dlc': '4',
            'transmitter': 'Vector__XXX',
        })

    def test_whitespace_lots(self):
        line = 'BO_  263  Batt107  :  4  Vector__XXX  '
        match = dbcparser.parser.Message.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '263',
            'name': 'Batt107',
            'dlc': '4',
            'transmitter': 'Vector__XXX',
        })

    def test_whitespace_minimum(self):
        line = 'BO_ 263 Batt107:4 Vector__XXX'
        match = dbcparser.parser.Message.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '263',
            'name': 'Batt107',
            'dlc': '4',
            'transmitter': 'Vector__XXX',
        })


class SignalTests(unittest.TestCase):
    def test_signal_simple(self):
        line = 'SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF'
        match = dbcparser.parser.Signal.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'name': 'Frequency_command',
            'mux': None,
            'start': '23', 'length': '16',
            'endianness': '0', 'signed': '+',
            'factor': '0.1', 'offset': '0',
            'min': '45', 'max': '65',
            'unit': 'Hz',
            'receivers': 'ABC,DEF',
        })

    def test_signal_mux_id(self):
        line = 'SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX'
        match = dbcparser.parser.Signal.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'name': 'CommandSetNVParam_MUX',
            'mux': 'M',
            'start': '7', 'length': '16',
            'endianness': '0', 'signed': '-',
            'factor': '1', 'offset': '0',
            'min': '-32768', 'max': '32767',
            'unit': '',
            'receivers': 'Vector__XXX',
        })

    def test_signal_mux_signal(self):
        line = 'SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX'
        match = dbcparser.parser.Signal.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': '23', 'length': '16',
            'endianness': '0', 'signed': '+',
            'factor': '1', 'offset': '0',
            'min': '0', 'max': '65535',
            'unit': '',
            'receivers': 'Vector__XXX',
        })

    def test_signal_whitespace_lots(self):
        line = '  SG_  Dummy  m0  :  23  |  16  @  0  +  (  1  ,  0  )  [  0  |  65535  ] ""  Vector__XXX  '
        match = dbcparser.parser.Signal.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': '23', 'length': '16',
            'endianness': '0', 'signed': '+',
            'factor': '1', 'offset': '0',
            'min': '0', 'max': '65535',
            'unit': '',
            'receivers': 'Vector__XXX',
        })

    def test_signal_whitespace_minimum(self):
        line = 'SG_ Dummy m0:23|16@0+(1,0)[0|65535]""Vector__XXX'
        match = dbcparser.parser.Signal.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'name': 'Dummy',
            'mux': 'm0',
            'start': '23', 'length': '16',
            'endianness': '0', 'signed': '+',
            'factor': '1', 'offset': '0',
            'min': '0', 'max': '65535',
            'unit': '',
            'receivers': 'Vector__XXX',
        })

class SignalCommentTests(unittest.TestCase):
    def test_simple(self):
        line = 'CM_ SG_ 2164239169 SignalName "this is the comment";'
        match = dbcparser.parser.SignalComment.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '2164239169',
            'name': 'SignalName',
            'comment': 'this is the comment',
        })

    def test_multiline(self):
        line = 'CM_ SG_ 123 SignalName2 "this comment \nextends over multiple lines";'
        match = dbcparser.parser.SignalComment.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '123',
            'name': 'SignalName2',
            'comment': 'this comment \nextends over multiple lines',
        })

    def test_whitespace_lots(self):
        line = 'CM_  SG_  2164239169  SignalName  "this is the comment" ;  '
        match = dbcparser.parser.SignalComment.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '2164239169',
            'name': 'SignalName',
            'comment': 'this is the comment',
        })

    def test_whitespace_minimum(self):
        line = 'CM_ SG_ 2164239169 SignalName"this is the comment";'
        match = dbcparser.parser.SignalComment.REGEX.search(line)
        self.assertEqual(match.groupdict(), {
            'address': '2164239169',
            'name': 'SignalName',
            'comment': 'this is the comment',
        })
