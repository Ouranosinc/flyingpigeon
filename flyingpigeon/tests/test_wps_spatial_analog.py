from .common import WpsTestClient, TESTDATA, assert_response_success
import ocgis



def test_wps_spatial_analog():

    wps = WpsTestClient()

    datainputs = "[reference_nc={0};target_json={1};indices=meantemp;indices=totalpr]".format(TESTDATA['reference_indicators'], TESTDATA['target_indicators'])

    resp = wps.get(service='wps', request='execute', version='1.0.0', identifier='spatial_analog',
                   datainputs=datainputs)
    assert_response_success(resp)