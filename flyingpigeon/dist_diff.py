# -*- encoding: utf8 -*-
"""
Empirical Kullback-Leibler divergence for continuous distributions.

In information theory, the Kullback–Leibler divergence is a non-symmetric 
measure of the difference between two probability distributions P and Q, 
where P is the "true" distribution and Q an approximation. This nuance is
important because D(P||Q) is not equal to D(Q||P). 
    
For probability distributions P and Q of a continuous random variable,
the K–L  divergence is defined as:
    
        D_{KL}(P||Q) = \int p(x) \log{p()/q(x)} dx
    
This formula assumes we have a representation of the probability densities p(x) and q(x). 
In many cases, we only have samples from the distribution, and most methods first 
estimate the densities from the samples and then proceed to compute the
K-L divergence. In [1], the authors propose an algorithm to estimate the K-L divergence 
directly from the sample using an empirical CDF. Even though the CDFs do not converge to their 
true values, the paper proves that the K-L divergence almost surely does converge to its true 
value. 



References
----------

[1] Kullback-Leibler Divergence Estimation of Continuous Distributions (2008). Fernando Pérez-Cruz.

:author: David Huard
:institution: Ouranos inc. 

"""

# TODO: Vectorize the cdf methods in the 1D case.

__all__ = ['KLDiv']

import bisect
import numpy as np

#
def KLDiv(x, y, k=1):
    """Compute the Kullback-Leibler divergence between two multivariate samples.

    Parameters
    ----------
    x : 2D array (n,d)
      Samples from distribution P, which typically represents the true 
      distribution. 
    y : 2D array (m,d)
      Samples from distribution Q, which typically represents the approximate
      distribution.
    k : int or sequence
      The kth neighbours to look for when estimating the density of the
      distributions. Default to 1, which can be noisy. 

          
    Returns
    -------
    out : float or sequence
      The estimated Kullback-Leibler divergence D(P||Q) computed from 
      the distances to the kth neighbour. 
      
    Notes
    -----
    The formula is based on the distance to the kth nearest neighbor, 
    which is roughly proportional to the density. If we use the first 
    neighbor, the result is more noisy than if we a farther neighbour, 
    at the expense of precision in the comparison between the two 
    distributions. 
      
    """
    from scipy.spatial import cKDTree as KDTree
    
    mk = np.iterable(k)
    ka = np.atleast_1d(k)
    
    x = np.atleast_2d(x)
    y = np.atleast_2d(y)
    
    # If array is 1D, flip it. 
    if x.shape[0] == 1:
        x = x.T
    if y.shape[0] == 1:
        y = y.T

    nx,dx = x.shape
    ny,dy = y.shape
    
    # Check the arrays have the same dimension.
    assert(dx == dy)
    
    # Limit the number of dimensions to 10. The algorithm becomes slow otherwise.
    assert(dx < 10)
        
    # Build a KD tree representation of the samples.
    xtree = KDTree(x)
    ytree = KDTree(y)
    
    # Get the k'th nearest neighbour from each points in x for both x and y.
    # We get the values for K + 1 to make sure the output is a 2D array.
    K = max(ka)+1
    r, indx = xtree.query(x, k=K, eps=0, p=2, n_jobs=2); 
    s, indy = ytree.query(x, k=K, eps=0, p=2, n_jobs=2); 
    
    # There is a mistake in the paper. In Eq. 14, the right side misses a negative sign 
    # on the first term of the right hand side. 
    D = []
    for ki in ka:
        # The 0th nearest neighbour in x of x is x, hence we take the k'th + 1, which is 0-based indexing is given by index k.
        D.append( -np.log(r[:,ki]/s[:,ki-1]).sum() * dx / nx + np.log(ny / (nx - 1.)) )
    
    if mk:
        return D
    else:
        return D[0]




