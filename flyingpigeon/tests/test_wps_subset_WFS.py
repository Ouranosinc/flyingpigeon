import pytest
import numpy as np

from .common import WpsTestClient, TESTDATA, assert_response_success

datainputs = "[resource={0};typename=opengeo:countries;featureids=countries.227;mosaic=False]".format( TESTDATA['cmip5_tasmax_2006_nc'])
datainputs = "[resource={0};typename=ADMINBOUNDARIES:canada_admin_boundaries;featureids=canada_admin_boundaries.3;mosaic=False]".format(TESTDATA['cmip5_tasmax_2006_nc'])



# def test_wps_subset_WFS_WATERSHEDS_BV_N3_S():
#     do_not_test = [6551]
#     idx_countries = np.arange(1, 7348)
#     for idx in idx_countries:
#         if not idx in do_not_test:
#             datainputs = "[resource={};typename=WATERSHEDS:BV_N3_S;featureids=BV_N3_S.{};mosaic=False]".format(
#                 TESTDATA['cmip5_tasmax_2006_nc'], idx)
#
#             wps = WpsTestClient()
#             resp = wps.get(service='wps', request='execute', version='1.0.0',
#                        identifier='subset_WFS',
#                        datainputs=datainputs)
#             print resp.data
#             print datainputs
#             assert_response_success(resp)
#
# def test_wps_subset_WFS_WATERSHEDS_BV_N2_S():
#     do_not_test = []
#     idx_countries = np.arange(1, 3300)
#     for idx in idx_countries:
#         if not idx in do_not_test:
#             datainputs = "[resource={};typename=WATERSHEDS:BV_N2_S;featureids=BV_N2_S.{};mosaic=False]".format(
#                 TESTDATA['cmip5_tasmax_2006_nc'], idx)
#
#             wps = WpsTestClient()
#             resp = wps.get(service='wps', request='execute', version='1.0.0',
#                        identifier='subset_WFS',
#                        datainputs=datainputs)
#             print resp.data
#             print datainputs
#             assert_response_success(resp)
#
# def test_wps_subset_WFS_WATERSHEDS_BV_N1_S():
#     do_not_test = []
#     idx_countries = np.arange(1, 790)
#     for idx in idx_countries:
#         if not idx in do_not_test:
#             datainputs = "[resource={};typename=WATERSHEDS:BV_N1_S;featureids=BV_N1_S.{};mosaic=False]".format(
#                 TESTDATA['cmip5_tasmax_2006_nc'], idx)
#
#             wps = WpsTestClient()
#             resp = wps.get(service='wps', request='execute', version='1.0.0',
#                        identifier='subset_WFS',
#                        datainputs=datainputs)
#             print resp.data
#             print datainputs
#             assert_response_success(resp)


#Test opengeo:countries

def test_wps_subset_WFS_OPENGEO_CONTRIES():
    do_not_test = [12, 71]  # None polygons with Topological problems
    idx_countries = np.arange(1, 242)
    for idx in idx_countries:
        if not idx in do_not_test:
            datainputs = "[resource={};typename=opengeo:countries;featureids=countries.{};mosaic=False]".format(
                TESTDATA['cmip5_tasmax_2006_nc'], idx)

            wps = WpsTestClient()
            resp = wps.get(service='wps', request='execute', version='1.0.0',
                       identifier='subset_WFS',
                       datainputs=datainputs)
            print resp.data
            print datainputs
            assert_response_success(resp)

#Test ADMINBOUNDARIES

def test_wps_subset_WFS_CANADA_ADMINBOUNDARIES():
    do_not_test = []
    idx_countries = np.arange(1, 14)
    for idx in idx_countries:
        if not idx in do_not_test:
            datainputs = "[resource={};typename=ADMINBOUNDARIES:canada_admin_boundaries;featureids=canada_admin_boundaries.{};mosaic=False]".format(
                TESTDATA['cmip5_tasmax_2006_nc'], idx)

            wps = WpsTestClient()
            resp = wps.get(service='wps', request='execute', version='1.0.0',
                       identifier='subset_WFS',
                       datainputs=datainputs)
            print resp.data
            print datainputs
            assert_response_success(resp)



