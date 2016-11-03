import pytest

from flyingpigeon import dist_diff as dd
import numpy as np
from numpy.testing import assert_equal as aeq, assert_almost_equal as aaeq
from scipy import stats
from scipy import integrate

# ==================================================================== #
#                       Analytical results
# ==================================================================== #
def analytical_KLDiv(p, q):
    """Return the Kullback-Leibler divergence between two distributions.
    
    Parameters
    ----------
    p, q : scipy.frozen_rv 
      Scipy frozen distribution instances, e.g. stats.norm(0,1)
      
    Returns
    -------
    out : float
      The Kullback-Leibler divergence computed by numerically integrating
      p(x)*log(p(x)/q(x)).
    """
    func = lambda x: p.pdf(x) * np.log(p.pdf(x) / q.pdf(x))
    a = 1E-5
    return integrate.quad(func, max(p.ppf(a), q.ppf(a)), min(p.isf(a), q.isf(a)))[0]
# ==================================================================== #

@pytest.mark.slow
class TestKLDIV:   
    #
    def accuracy_vs_kth(self, N=100, trials=100):
        """Evalute the accuracy of the algorithm as a function of k.
        
        Parameters
        ----------
        N : int
          Number of random samples.
        trials : int
          Number of independent drawing experiments. 
        
        Returns
        -------
        (err, stddev) The mean error and standard deviation around the 
        analytical value for different values of k from 1 to 15.
        """
        p = stats.norm(0, 1)
        q = stats.norm(0.2, 0.9)
            
        k = np.arange(1,16)
        
        out = []
        for n in range(trials):
            out.append( dd.kldiv(p.rvs(N), q.rvs(N), k) )
        out = np.array(out)
        
        # Compare with analytical value
        err = out - analytical_KLDiv(p, q)
        
        # Return mean and standard deviation
        return err.mean(0), err.std(0)
    #    
    def test_accuracy(self):
        m, s = self.accuracy_vs_kth(N=500, trials=300)
        aaeq(np.mean(m[0:2]), 0, 2)
    #    
    def test_different_sample_size(self):
        
        p = stats.norm(2,1)
        q = stats.norm(2.6, 1.4)
        
        ra = analytical_KLDiv(p, q)
            
        N = 6000
        # Same sample size for x and y
        re = [dd.kldiv(p.rvs(N), q.rvs(N)) for i in range(30)]
        aaeq(np.mean(re), ra, 2)
        
        # Different sample sizes
        re = [dd.kldiv(p.rvs(N*2), q.rvs(N)) for i in range(30)]
        aaeq(np.mean(re), ra, 2)
        
        re = [dd.kldiv(p.rvs(N), q.rvs(N*2)) for i in range(30)]
        aaeq(np.mean(re), ra, 2)
    #
    def test_mvnormal(self):
        """Compare the results to the figure 2 in the paper."""
        from numpy.random import normal, multivariate_normal
        from numpy.testing import assert_equal, assert_almost_equal
        
        N = 10000
        p = normal(0,1, size=(N,2))
        q = multivariate_normal([.5, -.5], [[.5,.1],[.1, .3]], size=N)
        
        aaeq(dd.kldiv(p,q), 1.39, 1)
        aaeq(dd.kldiv(q,p), 0.62, 1)
    
    
    
