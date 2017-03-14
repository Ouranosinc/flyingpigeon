# -*- encoding: utf8 -*-
"""
Methods to compute differences between distributions
====================================================

 * kldiv
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

__all__ = ['kldiv',]

import bisect
import numpy as np

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
      distribution. 
    y : 2D array (m,d)
      Samples from distribution Q, which typically represents the 
      approximate       distribution.
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


import ocgis
from ocgis.calc import base
from ocgis.util.helpers import iter_array
from ocgis.util.logging_ocgis import ocgis_lh
from ocgis.exc import SampleSizeNotImplemented, DefinitionValidationError, UnitsValidationError

class DistDiff_old(base.AbstractMultivariateFunction, base.AbstractParameterizedFunction):
    description = 'Return a measure of the difference between two multivariate distributions.'

    key = 'dist_diff'
    units = None
    standard_name = 'dist_diff'
    long_name = "Difference between two distributions."
    parms_definition={'algo':str, 'rv':tuple, 'tv':tuple}
    required_variables = ['rv', 'tv']
    joined_variables = True
    _potential_algo=('kldiv',)
    time_aggregation_external = False

    def calculate(self, rv=[], tv=[], algo='kldiv'):
        assert (algo in self._potential_algo)

        # Check that there is only one time vector in the target data
        # Note that we could eventually loop around multiple locations in the target data, but it could get messy pretty fast.
        tsh = list(tv[0].shape)
        tsh.pop(1) # Pop the time dimension.
        assert np.all(np.equal(tsh,1)) # Check that all dimensions except time are equal to 1.
        q = np.squeeze(np.array(tv)).T

        # Realization, time, level, row, column
        # Aggregation over the variable and time dimensions.
        out = np.empty_like(rv[0][:,:1])
        itr = iter_array(rv[0][:,:1])
        for ie, it, il, ir, ic in itr:
            p = np.vstack((x[ie, :, il, ir, ic] for x in rv)).T
            out[ie, it, il, ir, ic] =  1 #kldiv(p, q, k=1)

        return out

ocgis.FunctionRegistry.append(DistDiff)
ocgis.env.DIR_DATA = '/home/david/projects/PAVICS/birdhouse/flyingpigeon/flyingpigeon/tests/testdata/spatial_analog/'
rfn = 'reference_indicators.nc' # TESTDATA['reference_indicators']
tfn = 'target_indicators.nc'

indices = ['meantemp', 'totalpr']
# Create dataset collection
rrd = ocgis.RequestDataset(rfn, variable=indices, alias=['rv1', 'rv2'])
trd = ocgis.RequestDataset(tfn, variable=indices, alias=['tv1', 'tv2'])
rdc = ocgis.RequestDatasetCollection([rrd, trd])
ops = ocgis.OcgOperations(calc=[{'func':'dist_diff', 'name':'spatial_analog','kwds':{'algo':'kldiv', 'rv':('rv1', 'rv2'), 'tv':('tv1', 'tv2')}},], calc_grouping='all', dataset=[rrd,trd])
ops.execute()

#ocgis.env.DIR_OUTPUT = '/tmp'
#rd = ocgis.RequestDataset(rfn)
#ops = ocgis.OcgOperations(geom=[-100., 50.], select_nearest=True, dataset=rd, output_format='nc', prefix='target')
#e = ops.execute()


"""
The current approach won't work because get_slice_and_calculation is is charge of dealing with index iteration, and assumes symetry across required variables.
"""