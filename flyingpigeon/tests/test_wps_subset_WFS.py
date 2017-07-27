import os
import sys
import unittest
import ConfigParser
import json

from pywps import Service
from pywps.tests import client_for

try:
    from flyingpigeon.tests import wps_tests_utils
except ImportError:
    import wps_tests_utils


class TestSubsetWFS(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        if os.path.isfile('configtests.cfg'):
            self.config.read('configtests.cfg')
        else:
            self.config.read('flyingpigeon/tests/configtests.cfg')
        self.config_dict = dict(self.config.items('subsetwfs'))
        sys.path.append('/'.join(os.getcwd().split('/')[:-1]))
        from flyingpigeon.processes import SubsetWFS
        self.client = client_for(Service(processes=[SubsetWFS()]))
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

    def test_process_exists(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = wps_tests_utils.parse_getcapabilities(html_response)
        self.assertTrue('subset_WFS' in processes)

    def test_describeprocess(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=subset_WFS'),
            self.client)
        describe_process = wps_tests_utils.parse_describeprocess(html_response)
        self.assertTrue('mosaic' in describe_process[0]['inputs'])
        self.assertTrue('output' in describe_process[0]['outputs'])

    def test_subset_wfs_01(self):
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=subset_WFS&DataInputs=resource=http://myserver/thredds/dodsC/birdhouse/nrcan/nrcan_canada_daily/nrcan_canada_daily_pr_1960.nc;'
             'typename=usa:states;featureids=states.1;geoserver=http://myserver/geoserver/wfs'),
            self.client)
        outputs = wps_tests_utils.parse_execute_response(html_response)
        output_file = outputs['outputs']['output']
        if output_file[:7] == 'file://':
            output_file = output_file[7:]
        f1 = open(output_file, 'r')
        json_data = json.loads(f1.read())
        f1.close()
        self.assertEqual(json_data, '')

suite = unittest.TestLoader().loadTestsFromTestCase(TestSubsetWFS)

if __name__ == '__main__':
    run_result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not run_result.wasSuccessful())
