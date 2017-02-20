import os
import uuid
import zipfile
import logging
import shutil
import subprocess

import numpy as np


from flyingpigeon.subset import clipping
from flyingpigeon import config
from pywps.Process import WPSProcess
from owslib.wfs import WebFeatureService

from netCDF4 import Dataset
from netCDF4 import MFDataset
import fiona
import json
from shapely.geometry import shape, mapping
from shapely.ops import cascaded_union

import osgeo.ogr as ogr
import osgeo.osr as osr

logger = logging.getLogger(__name__)

MAX_NUMBER_OUTPUTS_NETCDF = 1
MAXMEGIGABITS = 5000
SIMPLIFY_TOLERANCE=0.0001

def Polygonize(geom, geoms_list):
    if geom.GetGeometryType() is ogr.wkbPolygon:
        geoms_list.append(geom.Clone())
    elif geom.GetGeometryType() is ogr.wkbMultiPolygon:
        for i in range(0, geom.GetGeometryCount()):
            geom2 = geom.GetGeometryRef(i)
            if geom2.GetGeometryType() is ogr.wkbPolygon:
                geoms_list.append(geom2.Clone())
            elif geom2.GetGeometryType() is ogr.wkbMultiPolygon:
                Polygonize(geom2.GetGeometryRef(i), geoms_list)

class WFSClippingProcess(WPSProcess):
    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="subset_WFS",
            title="Subset WFS",
            version="0.1",
            abstract="Fetch a shapefile from a WFS server and clip each input dataset with all the polygons it contains",
            statusSupported=True,
            storeSupported=True
            )

        self.resource = self.addComplexInput(
            identifier="resource",
            title="Resource",
            abstract="NetCDF File",
            minOccurs=1,
            maxOccurs=1000,
            maxmegabites=MAXMEGIGABITS,
            formats=[{"mimeType":"application/x-netcdf"}],
            )

        self.typename = self.addLiteralInput(
            identifier="typename",
            title="TypeName",
            abstract="Layer to fetch from WFS server",
            type=type(''),
            minOccurs=1,
            maxOccurs=1
            )

        self.featureids = self.addLiteralInput(
            identifier="featureids",
            title="Feature Ids",
            abstract="List of unique feature ids",
            type=type(''),
            minOccurs=0,
            maxOccurs=1
        )

        self.xmlfilter = self.addLiteralInput(
            identifier="filter",
            title="XML filter",
            abstract="XML-encoded OGC filter expression",
            type=type(''),
            minOccurs=0,
            maxOccurs=1
            )

        self.variable = self.addLiteralInput(
            identifier="variable",
            title="Variable",
            abstract="Variable to be expected in the input files (Variable will be detected if not set)",
            default=None,
            type=type(''),
            minOccurs=0,
            maxOccurs=1,
            )

        self.mosaic = self.addLiteralInput(
            identifier="mosaic",
            title="Mosaic",
            abstract="If Mosaic is checked, selected polygons will be merged to one Mosaic for each input file",
            default=False,
            type=type(False),
            minOccurs=0,
            maxOccurs=1,
        )

        self.output = self.addComplexOutput(
            title="Subsets",
            abstract="Tar archive containing the netCDF files",
            formats=[{"mimeType":"application/x-tar"}],
            asReference=True,
            identifier="output",
        )

        # self.output_netcdf = self.addComplexOutput(
        #     title="Subsets for one dataset",
        #     abstract="NetCDF file with subsets of one dataset.",
        #     formats=[{"mimeType":"application/x-netcdf"}],
        #     asReference=True,
        #     identifier="ncout",
        # )

        # Creates multiple outputs in case of multiple features inputs without mosaic.
        # The output WPS response will enumerate only the outputs used if pywps (pywps/Wps/Execute/__init__.py) is
        # modified with :
            #if len(output.metadata):
            #    if 'bypass_output_empty_value' in output.metadata[0]:
            #        if output.metadata[0]['bypass_output_empty_value'] and output.value is None:
            #            continue

        # The number of features cannot exceed more than MAX_NUMBER_OUTPUTS_NETCDF in mosaic=False
        self.outputs_netcdf = []
        k = np.arange(0,MAX_NUMBER_OUTPUTS_NETCDF)
        for i in k:
            self.outputs_netcdf.append(self.addComplexOutput(
            title="Subsets for one dataset",
            abstract="NetCDF file with subsets of one dataset.",
            formats=[{"mimeType": "application/x-netcdf"}],
            asReference=True,
            identifier="ncout_{}".format(i),
            metadata=[{"bypass_output_empty_value":True}]
        ))

    def execute(self):
        urls = self.getInputValues(identifier='resource')
        mosaic = self.mosaic.getValue()
        featureids = self.featureids.getValue()
        xmlfilter = self.xmlfilter.getValue()
        typename = self.typename.getValue()
        variable = self.variable.getValue()
        logger.info('urls = %s', urls)
        logger.info('filter = %s', xmlfilter)
        logger.info('mosaic = %s', mosaic)
        logger.info('typename = %s', typename)
        logger.info('featureids = %s', featureids)

        self.status.set('Arguments set for WPS subset process', 0)
        logger.debug('starting: num_files=%s' % (len(urls)))

        try:
            # Connect to WFS server
            source_shapefile_name = typename.split(":")[1]
            url = config.wfs_url()
            wfs = WebFeatureService(url, "1.1.0")

            # What type of request will we do
            if featureids is None:
                if xmlfilter is not None:
                    polygons = wfs.getfeature(typename=typename, filter=xmlfilter, outputFormat='application/json')
                else:
                    raise Exception('Feature Ids or XML filter required')
            else:
                featurelist = featureids.split(",")
                polygons = wfs.getfeature(typename=typename, featureid=featurelist, outputFormat='application/json')

            #decode json
            polygons_geojson = json.load(polygons)

            #list all polygons
            geoms_list = []
            for feature in polygons_geojson['features']:
                geom = json.dumps(feature['geometry'])
                geom = ogr.CreateGeometryFromJson(geom)
                geoms_list.append(geom)

            # create the data source
            driver = ogr.GetDriverByName("ESRI Shapefile")
            # get unique name for folder and create it
            unique_dirname = str(uuid.uuid4())
            # unique_dirname = 'toto'
            dirpath = os.path.join(config.cache_path(), unique_dirname)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            source_shp_path = os.path.join(dirpath, source_shapefile_name + ".shp")
            data_source = driver.CreateDataSource(source_shp_path)

            # create the spatial reference, WGS84
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)

            geom_inputs = []
            if mosaic :
                geom_u = geoms_list[0]
                for geom  in geoms_list:
                    geom_u = geom_u.Union(geom)
                geom_inputs.append(geom_u.SimplifyPreserveTopology(SIMPLIFY_TOLERANCE))
                mosaic=False #bypass mosaic in OGCGis.  Process a Multipolygon composed from the union of all inputs
            else :
                geom_inputs = [geom.SimplifyPreserveTopology(SIMPLIFY_TOLERANCE) for geom in geoms_list]

            # create the layer
            layer = data_source.CreateLayer("data", srs, ogr.wkbUnknown)

            rangedlist = range(0, len(geom_inputs))
            featureidlist = [str(elem) for elem in rangedlist]

            # Create the source shape file
            for geom in geom_inputs:
                feature = ogr.Feature(layer.GetLayerDefn())
                # Set the feature geometry using the point
                feature.SetGeometry(geom)
                # Create the feature in the layer (shapefile)
                layer.CreateFeature(feature)
                # Dereference the feature
                feature = None

            # Save and close the data source
            data_source = None

            # Do clipping, without forgetting to switch GEOMCABINET
            results = clipping(
                resource=urls,
                polygons=featureidlist,
                mosaic=mosaic,
                spatial_wrapping='wrap',
                variable=variable,
                dir_output=os.path.abspath(os.curdir),
                geomcabinet=dirpath,
                geom=source_shp_path
            )
            logger.info('WPS clipping done')
        except Exception as e:
            msg = 'WPS clipping failed'
            logger.exception(msg)
            raise Exception(msg)

        if not results:
            raise Exception('no results produced.')

        # prepare tar file
        try:
            from flyingpigeon.utils import archive
            tarf = archive(results)
            logger.info('Tar file prepared')
        except Exception as e:
            msg = 'Tar file preparation failed'
            logger.exception(msg)
            raise Exception(msg)

        self.output.setValue(tarf)

        n_output = len(self.outputs_netcdf)
        n_output_to_save = min(n_output, len(results))

        #populate outputs list
        idxs = np.arange(0, n_output_to_save)
        for idx in idxs:
            self.outputs_netcdf[idx].setValue(results[idx])

        self.status.set('done', 100)







