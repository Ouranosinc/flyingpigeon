import pytest
import unittest

from pywps import Service
#from pywps.tests import assert_response_success

from .common import TESTDATA, client_for
from flyingpigeon.processes import WFSClippingProcess


@pytest.mark.online
def test_wps_subset_WFS():
    client = client_for(Service(processes=[WFSClippingProcess()]))
    # This would work, but need to allow > 1 mb file download in some config
    # somewhere. The input is an url in request.inputs['resource'][0].url
    # where the @xlink:href= part is removed.
    # The location of the (temporary) file on disk is in
    # request.inputs['resource'][0].file and (presumably) the actual data
    # stream of the file is in request.inputs['resources'][0].data
    # Perhaps there is a setting somewhere to download (big) data, but
    # not keep the data stream in .data, just the location in .file...
    datainputs = "resource=@xlink:href=http://outarde.crim.ca:8083/thredds/fileServer/birdhouse/nrcan/nrcan_canada_daily/nrcan_canada_daily_pr_1960.nc;typename=lala;featureids=ff"
    # datainputs = "resource=@xlink:href=http://outarde.crim.ca:8083/thredds/fileServer/birdhouse/wps_outputs/flyingpigeon/ncout-fa00f5f0-6395-11e7-a67b-0242ac150002.nc;typename=usa:states;featureids=states.4"

    # If not using xlink, the url is empty and this string appears in
    # requests.inputs['resource'][0].data
    #datainputs = "resource=http://outarde.crim.ca:8083/thredds/dodsC/birdhouse/wps_outputs/flyingpigeon/ncout-fa00f5f0-6395-11e7-a67b-0242ac150002.nc;typename=lala;featureids=ff"
    resp = client.get(
        service='WPS', request='Execute', version='1.0.0',
        identifier='subset_WFS',
        datainputs=datainputs)
    raise IOError(str(resp.get_data()))
    #assert_response_success(resp)
