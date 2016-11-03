"""
Process to compute differences between distributions. 
At the moment, only includes the Kullback-Leibler divergence.  
Author: Nils Hempelmann (info@nilshempelmann.de), David Huard (huard.david@ouranos.ca)
"""
#import tarfile
#import os

from pywps.Process import WPSProcess
import logging
logger = logging.getLogger(__name__)



class DistributionSimilarityProcess(WPSProcess):
    
  def __init__(self):
    WPSProcess.__init__(
      self,
      identifier = "distribution_similarity",
      title = "Similarity between distributions",
      version = "0.9",
      #metadata= [
      #    {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
      #   ],
      abstract="Returns a measure of the difference D(P,Q) between two distributions P and Q, each described by a sample of values x and y.",
      statusSupported=True,
      storeSupported=True
      )
      
  ###########
  ### INPUTS
  ###########
    self.algo = self.addLiteralInput(
      identifier="algo",
      title="Algorithm",
      abstract="Name of algorithm to use to compute differences.",
      default="kldiv",
      allowedValues=['kldiv',],
      type=type(''),
      minOccurs=1,
      maxOccurs=1,
    )
    self.vec_p = self.addComplexInput(
      identifier="vec_p",
      title="List of values from P",
      abstract="",
      minOccurs=1,
      maxOccurs=500,
      maxmegabites=50000,
      formats=[{"mimeType":"json"}],
      )

    self.vec_q = self.addComplexInput(
      identifier="vec_q",
      title="List of values from Q",
      abstract="",
      minOccurs=1,
      maxOccurs=1,
      maxmegabites=50000,
      formats=[{"mimeType":"json"}],
      )
    """
    self.nc_p = self.addComplexInput(
      identifier="nc_p",
      title="NetCDF file for P",
      abstract="NetCDF file  holding the sample from P, the 'true' distribution.",
      minOccurs=1,
      maxOccurs=500,
      maxmegabites=50000,
      formats=[{"mimeType":"application/x-netcdf"}],
      )

    self.nc_q = self.addComplexInput(
      identifier="nc_q",
      title="NetCDF file for Q",
      abstract="NetCDF file  holding the different samples from Q, the 'approximate' distribution.",
      minOccurs=1,
      maxOccurs=1,
      maxmegabites=50000,
      formats=[{"mimeType":"application/x-netcdf"}],
      )
    """
  ###########
  ### OUTPUTS
  ###########
    self.out = self.addLiteralOutput(
      identifier="out",
      title="Distribution difference",
      data_type='float',
      abstract="Measures of the difference between the distribution of P and Q.",
      )
  """
  self.ncout = self.addComplexOutput(
      identifier="ncout",
      title="Distribution differences",
      abstract="Measures of the differences between the distribution of P and Q.",
      formats=[{"mimeType":"application/x-netcdf"}],
      asReference=True,
      )
  """

    
  def execute(self):
    from os.path import basename
    from flyingpigeon.utils import archive
    from flyingpigeon import dist_diff as dd

    self.status.set('Start process', 0)
  
    try: 
      logger.info('Reading the arguments')
      #nc_p = self.getInputValues(identifier='nc_p')
      #nc_q = self.getInputValues(identifier='nc_q')
      self.algo = self.getInputValues(identifier='algo')
      self.vec_p = selg.getInputValues(identifier='vec_p')
      self.vec_q = selg.getInputValues(identifier='vec_q')
      
      logger.info("algo: {0}".format(algo))
      logger.info("{0} items for P; {1} items for Q".format(len(vec_p), len(vec_q)))                       
      #logger.info("Inputs:\nnc_p: {0}\nc_q: {1}\nalgo: {2}".format(nc_p, nc_q, algo))
      self.status.set('Arguments read', 5)  
      
    except Exception as e: 
      logger.error('failed to read in the arguments %s ' % e)
      
    if algo == 'kldiv':
      self.out.setValue( dd.kldiv(vec_p, vec_q) )
    else:
      raise ValueError(self.algo)  
      
    self.status.set('Finished process', 100)
    
  


