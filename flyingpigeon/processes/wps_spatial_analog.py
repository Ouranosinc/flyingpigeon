"""
Processes for spatial analog calculation 
Author: Nils Hempelmann (info@nilshempelmann.de), David Huard (huard.david@ouranos.ca)
"""
#import tarfile
#import os

from pywps.Process import WPSProcess
import logging
from os.path import basename
import numpy as np
from flyingpigeon import dist_diff as dd
# from flyingpigeon.utils import archive
import json, datetime as dt
import netCDF4 as nc

logger = logging.getLogger(__name__)

from flyingpigeon.sdm import _SDMINDICES_

class SDMProcess(WPSProcess):
    
    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier = "spatial_analog",
            title = "Spatial Analog",
            version = "0.9",
            #metadata= [
            #    {"title": "Bayerische Landesanstalt fuer Wald und Forstwirtschaft", "href": "http://www.lwf.bayern.de/"},
            #    {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
            #   ],

            abstract="Spatial analogs based on the comparison of climate indices. The algorithm compares the distribution of the target indices with the distribution of spatially distribution reference indices. The return value is the spatially distributed Kullback-Leibler divergence, an information-theoretic measure of the differences between distribution. A KL divergence of 0 signifies that both distributions are equal.",
            statusSupported=True,
            storeSupported=True
            )

        # Literal Input Data
        # ------------------

        self.reference_nc = self.addComplexInput(
            identifier="reference_nc",
            title="Reference NetCDF Dataset",
            abstract="NetCDF dataset storing the reference indices.",
            minOccurs=1,
            maxOccurs=10,
            maxmegabites=50000,
            formats=[{"mimeType":"application/x-netcdf"}],
            )

        self.target_nc = self.addComplexInput(
            identifier="target_nc",
            title="Target NetCDF dataset",
            abstract="Target NetCDF dataset storing the target indices over the target period.",
            minOccurs=0,
            maxOccurs=10,
            maxmegabites=50000,
            formats=[{"mimeType":"application/x-netcdf"}],
            )

        self.target_json = self.addComplexInput(
            identifier="target_json",
            title="Target JSON dataset",
            abstract="Target JSON dataset storing the target indices over the target period in a dictionary keyed by variable names.",
            minOccurs=0,
            maxOccurs=10,
            maxmegabites=50000,
            formats=[{"mimeType": "application/json"}],
        )

        self.indices = self.addLiteralInput(
            identifier="indices",
            title="Indices",
            abstract="One or more climate indices to use for the comparison.",
            type=type(''),
            minOccurs=1,
            maxOccurs=10,
            )

        self.algo = self.addLiteralInput(
            identifier="algo",
            title="Algorithm",
            abstract="Name of algorithm to use to compute differences.",
            default="kldiv",
            allowedValues=['kldiv', ],
            type=type(''),
            minOccurs=0,
            maxOccurs=1,
        )

        self.refrange = self.addLiteralInput(
            identifier="refrange",
            title="Reference period",
            abstract="Reference period (YYYY-MM-DD/YYYY-MM-DD) for climate conditions (defaults to entire timeseries).",
            default="",
            type=type(''),
            minOccurs=0,
            maxOccurs=1,
            )

        self.targetrange = self.addLiteralInput(
            identifier="targetrange",
            title="Target period",
            abstract="Target periods (YYYY-MM-DD/YYYY-MM-DD) for climate conditions (defaults to entire timeseries). Only applies to netCDF target files.",
            default="",
            type=type(''),
            minOccurs=0,
            maxOccurs=20,
        )

        self.archive_format = self.addLiteralInput(
            identifier="archive_format",
            title="Archive format",
            abstract="Result files will be compressed into archives. Choose an appropriate format.",
            default="tar",
            type=type(''),
            minOccurs=0,
            maxOccurs=1,
            allowedValues=['zip','tar']
            )

        ###########
        ### OUTPUTS
        ###########
        #self.output = self.addComplexOutput(
        #    identifier="output_analogs",
        #    title="Spatial Analogs",
        #    abstract="Archive (tar/zip) containing calculated dissimilarity measure as netCDF files",
        #    formats=[{"mimeType":"application/x-tar"}, {"mimeType":"application/zip"}],
        #    asReference=True,
        #    )
        self.output = self.addLiteralOutput(
            identifier="output_test",
            title="Spatial Analogs",
            type = type(1.0),
        )

    def execute(self):

        self.status.set('Start process', 0)

        try:
            logger.info('reading the arguments')
            reference_nc = self.getInputValues(identifier='reference_nc')
            target_nc = self.getInputValues(identifier='target_nc')
            target_json = self.getInputValues(identifier='target_json')
            indices = self.getInputValues(identifier='indices')
            algo = self.getInputValue(identifier='algo')
            refrange = self.getInputValue(identifier='refrange')
            targetrange = self.getInputValues(identifier='targetrange')
            archive_fmt = self.getInputValue(identifier='archive_format')

        except Exception as e:
            logger.error('failed to read in the arguments %s ' % e)

        if target_nc is None or target_json is None:
            raise ValueError("Target data is missing.")

        # Load target variables
        target_data = {}
        if target_json is not None:
            for target in target_json:
                with open(target, 'r') as f:
                    data = json.load(f)
                    for var in indices:
                        target_data[var] = data[var]

        elif target_nc is not None:
            with nc.MFDataset(target_nc, 'r') as D:
                for var in indices:
                    #TODO : Implement targetrange
                    target_data[var] = D.variables[var][:]

        P = np.vstack(target_data[var] for var in indices).T

        # Load reference dataset
        ptime = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
        if refrange:
            refrange = map(ptime, refrange.split('-'))


        ref_data = {}
        with nc.MFDataset(reference_nc, 'r') as D:
            time = D.variables['time']
            if refrange:
                sl = slice(*nc.date2index(rrange, time, select='nearest'))
            else:
                sl = slice(None, None)

            for var in indices:
                assert D.variables[var].dimensions[0] == 'time'
                ref_data[var] = D.variables[var][sl]

            shape = set([ref_data[var].shape for var in indices])
            assert len(shape) == 1
            shape = shape.pop()

            out_arr = np.ones(shape[1:]) * -999
            I,J = np.indices(shape[1:])
            # TODO: parallelize
            for (i,j) in zip(I.flatten(),J.flatten()):
                Q = np.vstack([ref_data[var][:,i,j] for var in indices]).T
                if np.any(np.isnan(Q)):
                    continue

                if algo == 'kldiv':
                    out_arr[i,j] = dd.kldiv(P, Q)
                else:
                    raise NotImplementedError(algo)

            fn = 'output.nc'
            with nc.Dataset(fn, 'w') as D:
                D.setncattr('source', 'spatial_analog')
                #TODO: Copy dimensions and attributes

            D.createDimension('lat', )
            D.createVariable(algo, float, ('lat', 'lon'))

        #self.output.setValue(fn)

        self.output.setValue(ans)
        self.status.set('done', 100)
