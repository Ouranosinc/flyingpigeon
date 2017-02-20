import pytest

from .common import WpsTestClient, TESTDATA, assert_response_success

@pytest.mark.skip(reason="no way of currently testing this")
def test_wps_spatial_averager_WFS_single_datainput_one_poly():
    wps = WpsTestClient()
    datainputs = "[resource={0};typename=usa:states;featureids=states.49]".format(
       TESTDATA['cmip5_tasmax_2006_nc'])
    resp = wps.get(service='wps', request='execute', version='1.0.0',
                   identifier='spatial_averager_WFS',
                   datainputs=datainputs)
    assert_response_success(resp)

@pytest.mark.skip(reason="no way of currently testing this")
def test_wps_spatial_averager_WFS_single_datainput_several_polys():
    wps = WpsTestClient()
    datainputs = "[resource={0};typename=usa:states;featureids=states.49,states.11".format(
        TESTDATA['cmip5_tasmax_2006_nc'])
    resp = wps.get(service='wps', request='execute', version='1.0.0',
                   identifier='spatial_averager_WFS',
                   datainputs=datainputs)
    assert_response_success(resp)

@pytest.mark.skip(reason="no way of currently testing this")
def test_wps_spatial_averager_WFS_several_datainputs_one_poly():
    wps = WpsTestClient()
    datainputs = "[resource={0};resource={1};typename=usa:states;featureids=states.49]".format(
        TESTDATA['cmip5_tasmax_2006_nc'], TESTDATA['cmip5_pr_1850_nc'])
    resp = wps.get(service='wps', request='execute', version='1.0.0',
                   identifier='spatial_averager_WFS',
                   datainputs=datainputs)
    assert_response_success(resp)

@pytest.mark.skip(reason="no way of currently testing this")
def test_wps_spatial_averager_WFS_several_datainputs_several_polys():
    wps = WpsTestClient()
    datainputs = "[resource={0};resource={1};typename=usa:states;featureids=states.49,states.11]".format(
        TESTDATA['cordex_tasmax_2006_nc'], TESTDATA['cordex_tasmax_2007_nc'])
    resp = wps.get(service='wps', request='execute', version='1.0.0',
                   identifier='spatial_averager_WFS',
                   datainputs=datainputs)
    assert_response_success(resp)