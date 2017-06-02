import pytest

from .common import WpsTestClient, TESTDATA, assert_response_success

@pytest.mark.online
def test_wps_indices_simple():
    wps = WpsTestClient()
    datainputs = "geoserver={0};typename={1};featureids={2};mosaic={3};resource=files@xlink:href={4}"\
        .format("http://outarde.crim.ca:8087/geoserver", "usa:states", "states.1", "false", "TESTDATA['cmip5_tasmax_2006_nc']")

    resp = wps.get(service='wps', request='execute', version='1.0.0',
                   identifier='subset_polygon',
                   datainputs=datainputs)

    assert_response_success(resp)