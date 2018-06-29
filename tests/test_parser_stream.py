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
