import os
import sys
import unittest
import ConfigParser

from pywps import Service
from pywps.tests import client_for

try:
    from flyingpigeon.tests import wps_tests_utils
except ImportError:
    import wps_tests_utils


class TestSimplest(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        if os.path.isfile('configtests.cfg'):
            self.config.read('configtests.cfg')
        else:
            self.config.read('flyingpigeon/tests/configtests.cfg')
        self.config_dict = dict(self.config.items('simplesttest'))
        sys.path.append('/'.join(os.getcwd().split('/')[:-1]))
        from flyingpigeon.processes import SimplestTest
        self.client = client_for(Service(processes=[SimplestTest()]))
        self.wps_host = None

    def test_getcapabilities(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        self.assertTrue(html_response)

    def test_getcapabilities_repeat(self):
        for i in range(10):
            html_response = wps_tests_utils.wps_response(
                self.wps_host,
                '?service=WPS&request=GetCapabilities&version=1.0.0',
                self.client)
            self.assertTrue(html_response)

    def test_process_exists_pavicrawler(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = wps_tests_utils.parse_getcapabilities(html_response)
        self.assertTrue('simplesttest' in processes)

    def test_describeprocess_pavicrawler(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=simplesttest'),
            self.client)
        describe_process = wps_tests_utils.parse_describeprocess(html_response)
        self.assertTrue('one_integer' in describe_process[0]['inputs'])
        self.assertTrue('repeated_integer' in describe_process[0]['outputs'])

    def test_simplest_01(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=simplesttest&DataInputs=one_integer={0}').format(
                self.config_dict['number1']),
            self.client)
        outputs = wps_tests_utils.parse_execute_response(html_response)
        self.assertEqual(int(outputs['outputs']['repeated_integer']),
                         int(self.config_dict['number1']))

suite = unittest.TestLoader().loadTestsFromTestCase(TestSimplest)

if __name__ == '__main__':
    run_result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not run_result.wasSuccessful())
