import pytest
from scipy import stats
from .common import WpsTestClient, TESTDATA, assert_response_success
from test_dist_diff import analytical_KLDiv as KLdiv
import json, tempfile, os
from numpy.testing import assert_approx_equal as aae
from flyingpigeon.dist_diff import kldiv

def test_wps_distribution_similarity():
    N = 100
    wps = WpsTestClient()
    P = stats.norm(0, 1)
    Q = stats.norm(0.2, 0.9)
    th_ans = KLdiv(P, Q)

    rp = P.rvs(N)
    rq = Q.rvs(N)

    ans = kldiv(rp, rq)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as fp:
        json.dump(rp.tolist(), fp)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as fq:
        json.dump(rq.tolist(), fq)
    
    datainputs = "[vec_p=file://{0};vec_q=file://{1}]".format(fp.name, fq.name)
    resp = wps.get(service='wps', request='execute', version='1.0.0', identifier='distribution_similarity',
                   datainputs=datainputs)

    os.remove(fp.name)
    os.remove(fq.name)
    assert_response_success(resp)

    out = resp.xpath_text('/wps:ExecuteResponse'
                            '/wps:ProcessOutputs'
                            '/wps:Output'
                            '/wps:Data'
                            '/wps:LiteralData'
                        )
    aae(out, ans, 4)

