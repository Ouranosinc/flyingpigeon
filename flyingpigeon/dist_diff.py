# -*- encoding: utf8 -*-
"""
Methods to compute differences between distributions
====================================================

 * Standardized Euclidean Distance
 * Nearest Neighbour
 * Zech-Aslan statistic
 * Friedman-Rasfsky run statistic
 * Kullback-Leibler divergence

 
 * others to be implemented, see Grenier, Patrick, et al. "An assessment of six dissimilarity metrics for climate analogs." Journal of Applied Meteorology and Climatology 52.4 (2013): 733-752.


kldiv
-----
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

__all__ = ['kldiv', ]

import bisect
import numpy as np
from scipy import spatial
from scipy.spatial import cKDTree as KDTree

def SED(x,y):
    """Standardized Euclidean Distance between x and y."""

    sx = np.std(x, 0)
    sy = np.std(y, 0)

    return np.sqrt( ((x-y)**2 / sx / sy).sum(1) )


def check_sample_shape(x,y):
    """
    Make sure x and y conform to the conventions used in all the dissimilarity metrics. x and y should be (n,d) and
    (m,d) arrays.

    :param x: array of the reference sample.
    :param y: array of the candidate sample.
    :return: Return two-dimensional arrays (n,d), (m,d).
    """
    x = np.atleast_2d(x)
    y = np.atleast_2d(y)

    # If array is 1D, flip it.
    if x.shape[0] == 1:
        x = x.T
    if y.shape[0] == 1:
        y = y.T

    nx, dx = x.shape
    ny, dy = y.shape

    # Check the arrays have the same dimension.
    assert (dx == dy)

    return x,y

def standardize(x,y):
    """Standardize x and y by the square root of the product of their standard deviation.

    :param x: Array (n,d)
    :param y: Array (m,d)
    :return: Standardized arrays x', y'
    """
    s = np.sqrt(x.std(0, ddof=1) * y.std(0, ddof=1))
    return x/s, y/s

def seuclidean(x, y):
    """Compute the Euclidean distance between the mean of a multivariate candidate sample (y) with respect to the mean
    of a reference sample (x).

    This metric considers neither the information from individual points nor the standard deviation of the candidate
    distribution.

    :param x: Array (n,d) of reference sample.
    :param y: Array (m,d) of candidate sample.
    :return: Standardized Euclidean Distance between the mean of the samples ranging from 0 to infinity.
    """
    x,y = check_sample_shape(x,y)

    mx = x.mean(0)
    my = y.mean(0)

    return spatial.distance.seuclidean(mx, my, x.var(0, ddof=1))

def nearest_neighbor(x,y):
    """
    Compute a dissimilarity metric based on the number of points in the pooled sample whose nearest neighbor belongs to
    the same distribution.

    :param x: Reference sample.
    :param y: Candidate sample.
    :return: Nearest-Neighbor dissimilarity metric ranging from 0 to 1.
    """
    x, y = check_sample_shape(x, y)
    x, y = standardize(x, y)

    nx, dx = x.shape

    # Pool the samples and find the nearest neighbours
    xy = np.vstack([x,y])
    tree = KDTree(xy)
    r, ind = tree.query(xy, k=2, eps=0, p=2, n_jobs=2);

    # Identify points whose neighbors are from the same sample
    same = ~np.logical_xor(*(ind < nx).T)

    return same.mean()


def zech_aslan(x,y):
    """
    Compute a dissimimilarity metric based on an analogy with the energy of a cloud of electrical charges.

    :param x: Reference sample.
    :param y: Candidate sample
    :return: Zech-Aslan dissimilarity metric ranging from -infinity to infinity.
    """

    x, y = check_sample_shape(x, y)
    nx, d = x.shape
    ny, d = y.shape

    xy = np.vstack([x,y])
    v = x.std(0, ddof=1) * y.std(0, ddof=1)
    #v = xy.std(0, ddof=1)

    dx  = spatial.distance.pdist(x, 'seuclidean', V=v)
    dy  = spatial.distance.pdist(y, 'seuclidean', V=v)
    dxy = spatial.distance.squareform( spatial.distance.pdist(xy, 'seuclidean', V=v))

    phix = -np.log(dx).sum()/nx/(nx-1)
    phiy = -np.log(dy).sum()/ny/(ny-1)
    phixy = np.log(dxy[nx:, :nx]).sum() / nx / ny

    return phix + phiy + phixy

def friedman_rafsky(x,y):
    """Compute a dissimilarity metric based on the Friedman-Rafsky runs statistics.

    The algorithm builds a minimal spanning tree (the subset of edges connecting all points that minimizes the total
    edge length) then counts the edges linking points from the same distribution.

    :param x: Reference sample array (n,d).
    :param y: Candidate sample array (m,d).
    :return: Friedman-Rafsky dissimilarity metric ranging from 0 to (m+n-1)/(m+n).
    """
    from sklearn import neighbors
    from scipy.sparse.csgraph import minimum_spanning_tree

    x, y = check_sample_shape(x, y)
    nx, d = x.shape
    ny, d = y.shape
    n = nx+ny

    xy = np.vstack([x,y])

    # Compute the NNs and the minimum spanning tree
    G = neighbors.kneighbors_graph(xy, n_neighbors=n-1, mode='distance')
    MST = minimum_spanning_tree(G, overwrite=True)
    edges = np.array(MST.nonzero()).T

    # Number of points whose neighbor is from the other sample
    diff = np.logical_xor(*(edges < nx).T).sum()

    return 1. - (1. + diff)/n




def kldiv(x, y, k=1):
    """Compute the Kullback-Leibler divergence between two multivariate samples.
    
        D(P||Q) = \frac{d}{n} \sum_i^n \log{\frac{r_k(x_i)}{s_k(x_i)}} + \log{\frac{m}{n-1}}
        
    where r_k(x_i) and s_k(x_i) are, respectively, the euclidean distance 
    to the kth neighbour of x_i in the x array (excepting x_i) and
    in the y array.  

    Parameters
    ----------
    x : 2D array (n,d)
      Samples from distribution P, which typically represents the true 
      distribution (reference).
    y : 2D array (m,d)
      Samples from distribution Q, which typically represents the 
      approximate distribution (candidate)
    k : int or sequence
      The kth neighbours to look for when estimating the density of the
      distributions. Defaults to 1, which can be noisy. 

          
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

    mk = np.iterable(k)
    ka = np.atleast_1d(k)

    x, y = check_sample_shape(x, y)

    nx, dx = x.shape
    ny, dy = y.shape

    # Limit the number of dimensions to 10. The algorithm becomes slow otherwise.
    assert (dx < 10)

    # Not enough data to draw conclusions.
    if nx < 5 or ny < 5:
        return np.nan

    # Build a KD tree representation of the samples.
    xtree = KDTree(x)
    ytree = KDTree(y)

    # Get the k'th nearest neighbour from each points in x for both x and y.
    # We get the values for K + 1 to make sure the output is a 2D array.
    K = max(ka) + 1
    r, indx = xtree.query(x, k=K, eps=0, p=2, n_jobs=2);
    s, indy = ytree.query(x, k=K, eps=0, p=2, n_jobs=2);

    # There is a mistake in the paper. In Eq. 14, the right side misses a negative sign 
    # on the first term of the right hand side. 
    D = []
    for ki in ka:
        # The 0th nearest neighbour in x of x is x, hence we take the k'th + 1, which is 0-based indexing is given by index k.
        D.append(-np.log(r[:, ki] / s[:, ki - 1]).sum() * dx / nx + np.log(ny / (nx - 1.)))

    if mk:
        return D
    else:
        return D[0]


