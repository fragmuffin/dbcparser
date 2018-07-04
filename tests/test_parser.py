import unittest
import os
import codecs

# Objects under test
import dbcparser.parser

TEST_DIR = './test-files'

class ParserTests(unittest.TestCase):

    def test_file_small(self):
        filename = os.path.join(TEST_DIR, 'small.dbc')
        with codecs.open(filename, 'r', encoding='utf_8') as stream:
            parser = dbcparser.parser.DBCParser(stream)

            bus = parser.parse(strict=True)
            self.assertIsInstance(bus, dbcparser.Bus)
