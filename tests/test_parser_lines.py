import unittest

# Objects under test
import dbcparser.parser


class LineObjectTest(unittest.TestCase):
    CLASS = None  # override to test class
    def assertParsedLine(self, line, expected):
        obj = self.CLASS.from_line(line)
        self.assertIsNotNone(obj)
        self.assertEqual(obj.dict(), expected)


class FrameTests(LineObjectTest):
    CLASS = dbcparser.parser.Frame

    def test_simple1(self):
        self.assertParsedLine(
            'BO_ 2566903475 ConverterInputOutput: 8 DCDC',
            {
                'address': 2566903475,
                'name': 'ConverterInputOutput',
                'dlc': 8,
                'transmitter': 'DCDC',
            }
        )

    def test_simple2(self):
        self.assertParsedLine(
            'BO_ 1258 PDORx4_Inv1: 8 INV_1',
            {
                'address': 1258,
                'name': 'PDORx4_Inv1',
                'dlc': 8,
                'transmitter': 'INV_1',
            }
        )

    def test_simple3(self):
        self.assertParsedLine(
            'BO_ 263 Batt107: 4 Vector__XXX',
            {
                'address': 263,
                'name': 'Batt107',
                'dlc': 4,
                'transmitter': None,
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'BO_  263  Batt107  :  4  Vector__XXX  ',
            {
                'address': 263,
                'name': 'Batt107',
                'dlc': 4,
                'transmitter': None,
            }
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'BO_ 263 Batt107:4 Vector__XXX',
            {
                'address': 263,
                'name': 'Batt107',
                'dlc': 4,
                'transmitter': None,
            }
        )


class SignalTests(LineObjectTest):
    CLASS = dbcparser.parser.Signal

    def test_signal_simple(self):
        self.assertParsedLine(
            'SG_ Frequency_command : 23|16@0+ (0.1,0) [45|65] "Hz" ABC,DEF',
            {
                'name': 'Frequency_command',
                'mux': None,
                'startbit': 23, 'length': 16,
                'little_endian': False, 'signed': False,
                'factor': 0.1, 'offset': 0.,
                'minimum': 45., 'maximum': 65.,
                'unit': 'Hz',
                'receivers': ['ABC', 'DEF'],
            }
        )

    def test_signal_mux_id(self):
        self.assertParsedLine(
            'SG_ CommandSetNVParam_MUX M  : 7|16@0- (1,0) [-32768|32767] "" Vector__XXX',
            {
                'name': 'CommandSetNVParam_MUX',
                'mux': 'M',
                'startbit': 7, 'length': 16,
                'little_endian': False, 'signed': True,
                'factor': 1., 'offset': 0.,
                'minimum': -32768., 'maximum': 32767.,
                'unit': '',
                'receivers': [],
            }
        )

    def test_signal_mux_signal(self):
        self.assertParsedLine(
            'SG_ Dummy m0  : 23|16@0+ (1,0) [0|65535] "" Vector__XXX',
            {
                'name': 'Dummy',
                'mux': 'm0',
                'startbit': 23, 'length': 16,
                'little_endian': False, 'signed': False,
                'factor': 1., 'offset': 0.,
                'minimum': 0., 'maximum': 65535,
                'unit': '',
                'receivers': [],
            }
        )

    def test_signal_whitespace_lots(self):
        self.assertParsedLine(
            '  SG_  Dummy  m0  :  23  |  16  @  0  +  (  1  ,  0  )  [  0  |  65535  ] ""  Vector__XXX  ',
            {
                'name': 'Dummy',
                'mux': 'm0',
                'startbit': 23, 'length': 16,
                'little_endian': False, 'signed': False,
                'factor': 1., 'offset': 0.,
                'minimum': 0., 'maximum': 65535.,
                'unit': '',
                'receivers': [],
            }
        )

    def test_signal_whitespace_minimum(self):
        self.assertParsedLine(
            'SG_ Dummy m0:23|16@0+(1,0)[0|65535]""Vector__XXX',
            {
                'name': 'Dummy',
                'mux': 'm0',
                'startbit': 23, 'length': 16,
                'little_endian': False, 'signed': False,
                'factor': 1., 'offset': 0.,
                'minimum': 0., 'maximum': 65535.,
                'unit': '',
                'receivers': [],
            }
        )


class SignalCommentTests(LineObjectTest):
    CLASS = dbcparser.parser.SignalComment

    def test_simple(self):
        self.assertParsedLine(
            'CM_ SG_ 2164239169 SignalName "this is the comment";',
            {
                'address': 2164239169,
                'name': 'SignalName',
                'comment': 'this is the comment',
            }
        )

    def test_multiline(self):
        self.assertParsedLine(
            'CM_ SG_ 123 SignalName2 "this comment \nextends over multiple lines";',
            {
                'address': 123,
                'name': 'SignalName2',
                'comment': 'this comment \nextends over multiple lines',
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'CM_  SG_  2164239169  SignalName  "this is the comment" ;  ',
            {
                'address': 2164239169,
                'name': 'SignalName',
                'comment': 'this is the comment',
            }
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'CM_ SG_ 2164239169 SignalName"this is the comment";',
            {
                'address': 2164239169,
                'name': 'SignalName',
                'comment': 'this is the comment',
            }
        )


class FrameCommentTests(LineObjectTest):
    CLASS = dbcparser.parser.FrameComment

    def test_simple(self):
        self.assertParsedLine(
            'CM_ BO_ 2365573367  "Fault bits.";',
            {
                'address': 2365573367,
                'comment': 'Fault bits.',
            }
        )

    def test_multiline(self):
        self.assertParsedLine(
            'CM_ BO_ 123  "multiline comment\nspans multiple lines... go figure!";',
            {
                'address': 123,
                'comment': 'multiline comment\nspans multiple lines... go figure!',
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'CM_  BO_  321  "commentz" ;  ',
            {
                'address': 321,
                'comment': 'commentz',
            }
        )


class NodeListTests(LineObjectTest):
    CLASS = dbcparser.parser.NodeList

    def test_simple(self):
        self.assertParsedLine(
            'BU_: ABC DEF',
            {'nodes': ['ABC', 'DEF']},
        )

    def test_empty(self):
        self.assertParsedLine('BU_:', {'nodes': []})

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'BU_  :  ABC  DEF  ',
            {'nodes': ['ABC', 'DEF']}
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'BU_:ABC DEF',
            {'nodes': ['ABC', 'DEF']}
        )


class NodeCommentTests(LineObjectTest):
    CLASS = dbcparser.parser.NodeComment

    def test_simple(self):
        self.assertParsedLine(
            'CM_ BU_ testBU "sender ECU";',
            {
                'node': 'testBU',
                'comment': 'sender ECU',
            }
        )

    def test_multiline(self):
        self.assertParsedLine(
            'CM_ BU_ NodeX "comment over\nmultiple lines";',
            {
                'node': 'NodeX',
                'comment': 'comment over\nmultiple lines',
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'CM_  BU_  testBU  "sender ECU"  ;  ',
            {
                'node': 'testBU',
                'comment': 'sender ECU',
            }
        )


class EnumerationTests(LineObjectTest):
    CLASS = dbcparser.parser.Enumeration

    def test_simple(self):
        self.assertParsedLine(
            'VAL_ 291 Signal 1 "one" 2 "two" 3 "three";',
            {
                'address': 291,
                'signal': 'Signal',
                'enums': {1: 'one', 2: 'two', 3: 'three'},
            }
        )

    def test_singular(self):
        self.assertParsedLine(
            'VAL_ 123 Foo 100 "bar";',
            {
                'address': 123,
                'signal': 'Foo',
                'enums': {100: 'bar'},
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'VAL_  291  Signal  1  "one with spaces"  2  "two"  3  "three"  ;  ',
            {
                'address': 291,
                'signal': 'Signal',
                'enums': {1: 'one with spaces', 2: 'two', 3: 'three'},
            }
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'VAL_ 291 Signal 1"one"2"two"3"three";',
            {
                'address': 291,
                'signal': 'Signal',
                'enums': {1: 'one', 2: 'two', 3: 'three'},
            }
        )


class ValueTableTests(LineObjectTest):
    CLASS = dbcparser.parser.ValueTable

    def test_simple(self):
        self.assertParsedLine(
            'VAL_TABLE_ Relay 0 "Open" 1 "Closed" 2 "Error" 3 "N/A";',
            {
                'table': 'Relay',
                'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'VAL_TABLE_  Relay  0  "Open"  1  "Closed"  2  "Error"  3  "N/A"  ;  ',
            {
                'table': 'Relay',
                'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
            }
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'VAL_TABLE_ Relay 0"Open"1"Closed"2"Error"3"N/A";',
            {
                'table': 'Relay',
                'enums': {0: 'Open', 1: 'Closed', 2: 'Error', 3: 'N/A'},
            }
        )


# ------------- Defines
class GlobalDefineTests(LineObjectTest):
    KEY = ''
    CLASS = dbcparser.parser.GlobalDefine

    def test_int(self):
        self.assertParsedLine(
            'BA_DEF_%s "DisplayDecimalPlaces" INT 0 65535;' % self.KEY,
            {
                'name': 'DisplayDecimalPlaces',
                'type': int,
                'params': (0, 65535),
            }
        )

    def test_hex(self):
        self.assertParsedLine(
            'BA_DEF_%s "some_value" HEX 0 63;' % self.KEY,
            {
                'name': 'some_value',
                'type': int,
                'params': (0, 63),
            }
        )

    def test_float(self):
        self.assertParsedLine(
            'BA_DEF_%s "GenSigStartValue" FLOAT -3.4E+038 3.4E+038;' % self.KEY,
            {
                'name': 'GenSigStartValue',
                'type': float,
                'params': (-3.4E+038, 3.4E+038),
            }
        )

    def test_string(self):
        self.assertParsedLine(
            'BA_DEF_%s "Foo" STRING;' % self.KEY,
            {
                'name': 'Foo',
                'type': str,
                'params': None,
            }
        )

    def test_bool(self):
        self.assertParsedLine(
            'BA_DEF_%s "bar" BOOL True False;' % self.KEY,
            {
                'name': 'bar',
                'type': bool,
                'params': (True, False),
            }
        )

    def test_enum(self):
        self.assertParsedLine(
            'BA_DEF_%s "enom_nom" ENUM "a","b","c";' % self.KEY,
            {
                'name': 'enom_nom',
                'type': tuple,
                'params': ('a', 'b', 'c'),
            }
        )


class SignalDefineTests(GlobalDefineTests):
    KEY = ' SG_'
    CLASS = dbcparser.parser.SignalDefine


class FrameDefineTests(GlobalDefineTests):
    KEY = ' BO_'
    CLASS = dbcparser.parser.FrameDefine


class NodeDefineTests(GlobalDefineTests):
    KEY = ' BU_'
    CLASS = dbcparser.parser.NodeDefine


# ------------- Attributes
class GlobalAttributeTests(LineObjectTest):
    CLASS = dbcparser.parser.GlobalAttribute

    def test_int(self):
        self.assertParsedLine('BA_ "Foo" 123;', {'name': 'Foo', 'value': 123})
        self.assertParsedLine('BA_ "Foo" -123;', {'name': 'Foo', 'value': -123})

    def test_float(self):
        floats = ['10.23', '-10.23', '.23', '-12.', '+4.5e-5', '4.5e5', '-4.5e+5']
        for v in floats:
            self.assertParsedLine(
                'BA_ "a" %s;' % v,
                {'name': 'a', 'value': float(v)}
            )

    def test_hex(self):
        self.assertParsedLine('BA_ "Foo" 0x0;', {'name': 'Foo', 'value': 0})
        self.assertParsedLine('BA_ "Foo" 0XABC;', {'name': 'Foo', 'value': 0xABC})

    def test_string(self):
        self.assertParsedLine('BA_ "x" "abc";', {'name': 'x', 'value': 'abc'})
        self.assertParsedLine('BA_ "x" foo bar;', {'name': 'x', 'value': 'foo bar'})


class SignalAttributeTests(LineObjectTest):
    CLASS = dbcparser.parser.SignalAttribute

    def test_simple(self):
        self.assertParsedLine(
            'BA_ "GenSigStartValue" SG_ 2365565505 V50to88pct 2000.0;',
            {
                'name': 'GenSigStartValue',
                'address': 2365565505,
                'signal_name': 'V50to88pct',
                'value': 2000.0,
            }
        )

    def test_whitespace_lots(self):
        self.assertParsedLine(
            'BA_  "DisplayDecimalPlaces"  SG_  2634007031  ControlSwRev  2 ;  ',
            {
                'name': 'DisplayDecimalPlaces',
                'address': 2634007031,
                'signal_name': 'ControlSwRev',
                'value': 2,
            }
        )

    def test_whitespace_minimum(self):
        self.assertParsedLine(
            'BA_"GenSigStartValue"SG_ 123 Dummy 0.0;',
            {
                'name': 'GenSigStartValue',
                'address': 123,
                'signal_name': 'Dummy',
                'value': 0.0,
            }
        )

class FrameAttributeTests(LineObjectTest):
    CLASS = dbcparser.parser.FrameAttribute

    def test_simple(self):
        self.assertParsedLine(
            'BA_ "GenMsgSendType" BO_ 2164239169 1;',
            {
                'name': 'GenMsgSendType',
                'address': 2164239169,
                'value': 1,
            }
        )

    def test_str(self):
        self.assertParsedLine(
            'BA_ "GenMsgStartValue" BO_ 2164239169 "0000000000000000";',
            {
                'name': 'GenMsgStartValue',
                'address': 2164239169,
                'value': '0000000000000000',
            }
        )

class NodeAttributeTests(LineObjectTest):
    CLASS = dbcparser.parser.NodeAttribute

    def test_simple(self):
        self.assertParsedLine(
            'BA_ "NetworkNode" BU_ testBU 273;',
            {
                'name': 'NetworkNode',
                'node': 'testBU',
                'value': 273,
            }
        )


# ------------- Other
class DefaultValueTests(LineObjectTest):
    CLASS = dbcparser.parser.DefaultValue

    def test_simple(self):
        self.assertParsedLine(
            'BA_DEF_DEF_ "GenMsgCycleTime" 65535;',
            {
                'name': 'GenMsgCycleTime',
                'value': 65535,
            }
        )
