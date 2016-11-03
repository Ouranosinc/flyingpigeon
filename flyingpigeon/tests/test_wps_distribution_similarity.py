import pytest
from scipy import stats
from .common import WpsTestClient, TESTDATA, assert_response_success
from test_dist_diff import analytical_KLDiv as KLdiv
import json, tempfile, os

#@pytest.mark.online
def test_wps_distribution_similarity():
    N = 100
    wps = WpsTestClient()
    p = stats.norm(0, 1)
    q = stats.norm(0.2, 0.9)
    ans = KLdiv(p, q)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fp:
        json.dump(p.rvs(N).tolist(), fp)    
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as fq:
        json.dump(q.rvs(N).tolist(), fq)
    
    datainputs = "[vec_p={0};vec_q={1}]".format(fp.name, fq.name)
    resp = wps.get(service='wps', request='execute', version='1.0.0', identifier='distribution_similarity',
                   datainputs=datainputs)
                   
    os.remove(fp.name)
    os.remove(fq.name)
    assert_response_success(resp)
