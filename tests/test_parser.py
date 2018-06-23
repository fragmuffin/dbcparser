import unittest
import io
import mock

# Objects under test
from dbcparser.parser import StreamParser

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
        p = StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.iter()],
            lines,
        )

    def test_empty_stream(self):
        stream = io.StringIO('')
        p = StreamParser(stream)
        self.assertEqual(list(p.iter()), [])

    @mock.patch('dbcparser.parser.CHUNK_SIZE', 1)
    def test_small_chunks(self):
        lines = [
            'simple',
            '"line starts" with a string',
            'line with "a string at the end"',
        ]
        stream = io.StringIO('\n'.join(lines))
        p = StreamParser(stream)

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
        p = StreamParser(stream)

        self.assertEqual(
            [l.rstrip('\n') for l in p.iter()],
            lines,
        )