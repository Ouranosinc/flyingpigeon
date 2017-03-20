"""
Processes for spatial analog calculation

Author: David Huard (huard.david@ouranos.ca),
        Nils Hempelmann (info@nilshempelmann.de)
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
import ocgis
from ocgis.calc import base
from ocgis.util.helpers import iter_array
from ocgis.calc.base import AbstractMultivariateFunction, \
    AbstractParameterizedFunction, AbstractFieldFunction
from ocgis.collection.field import OcgField

logger = logging.getLogger(__name__)

class Dissimilarity(AbstractFieldFunction,
        AbstractParameterizedFunction):

    key = 'dissimilarity'
    long_name = 'Dissimilarity metric comparing two samples'
    standard_name = 'dissimilarity_metric'
    description = 'Metric evaluating the dissimilarity between two ' \
                  'multivariate samples'
    parms_definition = {'algo': str, 'reference': OcgField, 'candidate':tuple}
    required_variables = ['candidate', 'reference']
    _potential_algo = dd.__all__


    def calculate(self, reference=None, candidate=None, algo='seuclidean'):
        """

        Parameters
        ----------
        reference : OgcField
            The reference distribution the different candidates are compared
            to.
        """
        assert (algo in self._potential_algo)
        metric = getattr(dd, algo) # Get the function from the module.

        ref = np.array([reference[c].get_value() for c in
                        candidate]).squeeze().T

        # Access the variable object by name from the calculation field.
        cfields = [self.field[c] for c in candidate]
        cdata = [c.get_value() for c in cfields]
        cv = np.array(cdata)

        # Output array
        shape_fill = cdata[0].shape[1:]
        fill = np.zeros(shape_fill)

        # Perform computation along the time axis
        itr = iter_array(cdata[0])
        for it, ir, ic in itr:
            # Reference array
            p = np.ma.masked_invalid(cv[:, :, ir, ic]).T

            # Compress masked values. If resulting array is too small, the functions will simply return NaN.
            pc = p.compress(~p.mask.any(1), 0)

            if pc.shape[0] < 5:
                fill[ir,ic] = np.nan
                continue

                fill[ir, ic] = metric(ref, pc)

        variable = self.get_fill_variable(cfields[0], algo, shape_fill,
         variable_value=np.ma.masked_invalid(fill))

        # Add the output variable to calculations variable collection. This is what is returned by the execute() call.
        self.vc.add_variable(variable)



        # The get_value() call returns a numpy array. Mask is retrieved by get_mask(). You can get a masked array
        # by using get_masked_value(). These return references.
        #value = np.apply_along_axis(func, 0, candidate.get_value())


        # Recommended that this method is used to create the output variables. Adds appropriate calculations attributes,
        # extra record information for tabular output, etc. At the very least, it is import to reuse the dimensions
        # appropriately as they contain global/local bounds for parallel IO. You can pass a masked array to
        # "variable_value".
        #variable = self.get_fill_variable(lhs, self.alias, lhs.dimensions,
        # variable_value=value)
        # Add the output variable to calculations variable collection. This is what is returned by the execute() call.
        #self.vc.add_variable(variable)

ocgis.FunctionRegistry.append(Dissimilarity)


class SpatialAnalogProcess(WPSProcess):
    
    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier = "spatial_analog",
            title = "Spatial Analog",
            version = "0.9",
            #metadata= [
            #    {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
            #   ],

            abstract="Spatial analogs based on the comparison of climate indices. The algorithm compares the distribution of the target indices with the distribution of spatially distribution reference indices. The return value is the spatially distributed Kullback-Leibler divergence, an information-theoretic measure of the differences between distribution. A KL divergence of 0 signifies that both distributions are equal.",
            statusSupported=True,
            storeSupported=True
            )

        # Literal Input Data
        # ------------------

        self.resource = self.addComplexInput(
            identifier="resource",
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
            minOccurs=1,
            maxOccurs=10,
            maxmegabites=50000,
            formats=[{"mimeType":"application/x-netcdf"}],
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
            abstract="Target period (YYYY-MM-DD/YYYY-MM-DD) for climate conditions (defaults to entire timeseries). Only applies to netCDF target files.",
            default="",
            type=type(''),
            minOccurs=0,
            maxOccurs=1,
        )

        self.targetlocation = self.addLiteralInput(
            identifier="targetlocation",
            title="Target geographical coordinates",
            abstract="Geographical coordinates (lon,lat) of the target location.",
            default=""
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


    def execute_ocgis(self):
        import ocgis

        urls = self.getInputValues(identifier='resource')
        target_nc = self.getInputValues(identifier='target_nc')
        indices = self.getInputValues(identifier='indices')
        algo = self.getInputValue(identifier='algo')
        refrange = self.getInputValue(identifier='refrange')
        targetrange = self.getInputValues(identifier='targetrange')
        archive_fmt = self.getInputValue(identifier='archive_format')

        logger.info('urls = {0}'.format(urls))
        logger.info('target = {0}'.format(target_nc or target_json))
        logger.info('indices = {0]'.format(indices))
        logger.info('algo = {0}'.format(algo))
        logger.info('refrange = {0}'.format(refrange))
        logger.info('targetrange = {0}'.format(targetrange))

        self.status.set('Arguments set for spatial analog process',0)
        logger.debug('starting: num_files = {0}'.format(len(urls)))

        try:
            ref_rd = ocgis.RequestDataset(urls, variable=indices, alias='reference')
            tar_rd = ocgis.RequestDataset(target_nc, variable=indices, alias='target')
            rdc = ocgis.RequestDatasetCollection(ref_rd, tar_rd)
            results = spatial_analog_calc(
                resource=urls,
                variables=indices,
                )

        except Exception as e:
            msg = 'Spatial analog failed'
            logger.exception(msg)
            raise Exception(msg)

        if not results:
            raise Exception('no results produced')

        try:
            from flyingpigeon.utils import archive
            tarf = archive(results)
            logger.info('Tar file prepared')
        except Exception as e:
            msg = 'Tar file preparation failed'
            logger.exception(msg)
            raise Exception(msg)

        self.output.setValue(tarf)

        i = next((i for (i, x) in enumerate(results) if x), None)
        self.output_netcdf.setValue(results[i])

        self.status.set('done', 100)



    def execute_simple(self):

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
