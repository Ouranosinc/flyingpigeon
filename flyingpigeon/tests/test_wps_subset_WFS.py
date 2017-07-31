import os
import sys
import unittest
import ConfigParser
import json

from pywps import Service
from pywps.tests import client_for
import netCDF4

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
        if self.config_dict['wps_host']:
            self.wps_host = self.config_dict['wps_host']
        else:
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
        wps_tests_utils.config_is_available(
            ['netcdf_file_01', 'typename_01', 'featureids_01', 'geoserver_01'],
            self.config_dict)
        html_response = wps_tests_utils.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=subset_WFS&DataInputs=resource={0};'
             'typename={1};featureids={2};geoserver={3}').format(
                self.config_dict['netcdf_file_01'],
                self.config_dict['typename_01'],
                self.config_dict['featureids_01'],
                self.config_dict['geoserver_01']),
            self.client)
        outputs = wps_tests_utils.parse_execute_response(html_response)
        output_json = outputs['outputs']['output']
        if output_json[:7] == 'file://':
            output_json = output_json[7:]
            f1 = open(output_json, 'r')
            json_data = json.loads(f1.read())
            f1.close()
        else:
            json_data = wps_tests_utils.get_wps_xlink(output_json)
        output_netcdf = json_data[0]
        if output_netcdf[:7] == 'file://':
            output_netcdf = output_netcdf[7:]
        else:
            output_netcdf = '/tmp/testtmp.nc'
            f1 = open(output_netcdf, 'w')
            f1.write(wps_tests_utils.get_wps_xlink(output_netcdf))
            f1.close()
        nc = netCDF4.Dataset(output_netcdf,'r')
        nclon = nc.variables['lon']
        nclat = nc.variables['lat']
        ncvar = nc.variables['dummy']
        self.assertEqual(nclon.shape, (3, 3))
        self.assertEqual(nclat.shape, (3, 3))
        self.assertEqual(nclon[0,0], 13)
        self.assertEqual(nclon[2,2], 25)
        self.assertEqual(nclat[0,0], 8.5)
        self.assertEqual(nclat[2,2], 18.5)
        self.assertEqual(ncvar.shape, (3, 3))
        self.assertEqual(ncvar[0,1], 13)
        self.assertEqual(ncvar[2,0], 32)

suite = unittest.TestLoader().loadTestsFromTestCase(TestSubsetWFS)

if __name__ == '__main__':
    run_result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not run_result.wasSuccessful())
