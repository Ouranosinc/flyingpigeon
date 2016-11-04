"""
Process to compute differences between distributions. 
At the moment, only includes the Kullback-Leibler divergence.  
Author: Nils Hempelmann (info@nilshempelmann.de), David Huard (huard.david@ouranos.ca)
"""
#import tarfile
#import os

from pywps.Process import WPSProcess
from flyingpigeon import dist_diff as dd
import logging, json
logger = logging.getLogger(__name__)


class DSProcess(WPSProcess):
  def __init__(self):
    WPSProcess.__init__(
      self,
      identifier = "distribution_similarity",
      title = "Similarity between distributions",
      version = "0.9",
      #metadata= [
      #    {"title": "Bayerische Landesanstalt fuer Wald und Forstwirtschaft", "href": "http://www.lwf.bayern.de/"},
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
      minOccurs=0,
      maxOccurs=1,
      )
            
    self.vec_p = self.addComplexInput(
      identifier="vec_p",
      title="List of values from P",
      abstract="",
      minOccurs=1,
      maxOccurs=1,
      maxmegabites=50000,
      formats=[{"mimeType":"application/json"}],
      )

    self.vec_q = self.addComplexInput(
      identifier="vec_q",
      title="List of values from Q",
      abstract="",
      minOccurs=1,
      maxOccurs=1,
      maxmegabites=50000,
      formats=[{"mimeType":"application/json"}],
      )
    
    ###########
    ### OUTPUTS
    ###########
    self.output = self.addLiteralOutput(
      identifier="output",
      title="Distribution difference",
      type=type(1.0),
      abstract="Measures of the difference between the distribution of P and Q.",
      )
  


  def execute(self):
    
    self.status.set('Start process', 0)
    
    try: 
      logger.info('Reading the arguments')
      self.algo = self.getInputValues(identifier='algo')[0]
      self.vec_p = self.getInputValues(identifier='vec_p')[0]
      self.vec_q = self.getInputValues(identifier='vec_q')[0]
      
      logger.info("algo: {0}".format(self.algo))
      logger.debug("algo: {0}".format(self.algo))
      logger.info("{0} items for P; {1} items for Q".format(len(self.vec_p), len(self.vec_q)))                       
      logger.debug("{0} items for P; {1} items for Q".format(len(self.vec_p), len(self.vec_q)))                       
      self.status.set('Arguments read', 5)  
      
    except Exception as e: 
      logger.error('failed to read in the arguments %s ' % e)
      
    if self.algo == 'kldiv':
      with open(self.vec_p, 'r') as f:
        p = json.load(f)
      with open(self.vec_q, 'r') as f:
        q = json.load(f)

      out = dd.kldiv(p, q)
      logger.info("Out: {0}".format(out))
      self.output.setValue( out )
    else:
      raise ValueError("Unrecognized algorithm", self.algo)  
    
    self.status.set('Finished process', 100)


  

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
    
  self.ncout = self.addComplexOutput(
      identifier="ncout",
      title="Distribution differences",
      abstract="Measures of the differences between the distribution of P and Q.",
      formats=[{"mimeType":"application/x-netcdf"}],
      asReference=True,
      )
  """
