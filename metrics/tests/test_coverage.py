import os
import StringIO
from unittest import TestCase
from mock import patch, MagicMock
from ddt import ddt, unpack, data
from ..coverage import CoverageData, CoverageParseError, configure_datadog


@ddt
class CoverageTest(TestCase):

    def setUp(self):
        self.data = CoverageData()

    @data(
        ['simple.xml', '*', 84.615384615385],
        ['simple.xml', 'group_1/*.py', 83.333333333333],
        ['simple.xml', 'group_2/*.py', 85.714285714286],
        ['simple.xml', 'none', None],
        ['missing_filename.xml', '*.py', 84.615384615385],
        ['unicode_filename.xml', '*.py', 84.615384615385],
        ['missing_line_root.xml', '*.py', 84.615384615385],
        ['missing_line_hits.xml', '*.py', 84.61538461538461],
        ['missing_line_num.xml', '*.py', 84.61538461538461],
        ['non_int_hits.xml', '*.py', 84.61538461538461],
        ['non_int_line_num.xml', '*.py', 84.61538461538461]
    )
    @unpack
    def test_add_report(self, report_name, pattern, expected_coverage):
        self.data.add_report(self._report_fixture('simple.xml'))
        actual = self.data.coverage(pattern)

        if expected_coverage is not None:
            self.assertAlmostEqual(actual, expected_coverage, places=3)
        else:
            self.assertIs(actual, None)

    def test_report_overlap(self):
        self.data.add_report(self._report_fixture('overlap_1.xml'))
        self.data.add_report(self._report_fixture('overlap_2.xml'))
        self.assertAlmostEqual(self.data.coverage('group_1/*.py'), 83.333333333333, places=3)

    def test_invalid_xml(self):
        with self.assertRaises(CoverageParseError):
            self.data.add_report(self._report_fixture('invalid.xml'))

    def test_unicode_pattern(self):
        self.data.add_report(self._report_fixture('simple.xml'))
        self.assertIs(self.data.coverage(u'\u9202.py'), None)

    @staticmethod
    def _report_fixture(name):
        """
        Load the fixture with filename `name` and return the contents as a `str`.
        """
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", name)
        with open(path) as fixture_file:
            return fixture_file.read()


class MainTest(TestCase):

    @patch('sys.stdout', new_callable=StringIO.StringIO)
    def test_configure_datadog(self, mock_stdout):
        """
        If no DATADOG_API_KEY is set, the script should exit with a helpful message.
        """
        helpful_message = u"Must specify DataDog API key with env var DATADOG_API_KEY\n"
        _env_vars= dict(os.environ)
        os.environ.clear()
        with self.assertRaises(SystemExit):
            configure_datadog()
        self.assertEqual(mock_stdout.getvalue(), helpful_message)
        os.environ.update(_env_vars)

