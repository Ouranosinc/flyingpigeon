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

from flyingpigeon.sdm import _SDMINDICES_

class DistributionDifferenceProcess(WPSProcess):
    
    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier = "distribution_difference",
            title = "Difference between distributions",
            version = "0.9",
            #metadata= [
            #    {"title": "Bayerische Landesanstalt fuer Wald und Forstwirtschaft", "href": "http://www.lwf.bayern.de/"},
            #    {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
            #   ],

            abstract="This returns a measure of the difference D(P,Q) between two distributions P and Q, each described by a sample of values x and y.",
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

        ###########
        ### OUTPUTS
        ###########

        self.ncout = self.addComplexOutput(
            identifier="ncout",
            title="Distribution differences",
            abstract="Measures of the differences between the distribution of P and Q.",
            formats=[{"mimeType":"application/x-netcdf"}],
            asReference=True,
            )

    def execute(self):
        from os.path import basename
        from flyingpigeon.utils import archive
        from flyingpigeon import dist_diff

        self.status.set('Start process', 0)
      
        try: 
            logger.info('Reading the arguments')
            nc_p = self.getInputValues(identifier='nc_p')
            nc_q = self.getInputValues(identifier='nc_q')
            algo = self.getInputValues(identifier='algo')
                       
            logger.info("Inputs:\nnc_p: {0}\nc_q: {1}\nalgo: {2}".format(nc_p, nc_q, algo))
            
        except Exception as e: 
            logger.error('failed to read in the arguments %s ' % e)
