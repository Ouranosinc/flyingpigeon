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
from shapely.geometry import shape, mapping

from osgeo import ogr

logger = logging.getLogger(__name__)

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
            maxmegabites=5000,
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

        self.outputs_netcdf = []
        k = np.arange(0,100)
        for i in k:
            self.outputs_netcdf.append(self.addComplexOutput(
            title="Subsets for one dataset",
            abstract="NetCDF file with subsets of one dataset.",
            formats=[{"mimeType": "application/x-netcdf"}],
            asReference=True,
            identifier="ncout_{}".format(i),
        ))

        t = 0

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

            #Connect to WFS server
            source_shapefile_name = typename.split(":")[1]
            url = config.wfs_url()
            wfs = WebFeatureService(url, "1.1.0")

            # What type of request will we do
            if featureids is None:
                if xmlfilter is not None:
                    polygons = wfs.getfeature(typename=typename, filter=xmlfilter, outputFormat='shape-zip')
                else:
                    raise Exception('Feature Ids or XML filter required')
            else:
                featurelist= featureids.split(",")
                polygons = wfs.getfeature(typename=typename, featureid=featurelist, outputFormat='shape-zip')
                rangedlist = range(0, len(featurelist))
                featureidlist = [str(elem) for elem in rangedlist]

            #get unique name for folder and create it
            unique_dirname = str(uuid.uuid4())
            #unique_dirname = 'toto'
            dirpath = os.path.join(config.cache_path(), unique_dirname)
            if not  os.path.exists(dirpath):
                os.mkdir(dirpath)
            filepath = os.path.join(dirpath, 'file.zip')

            #Saves the result in folder and unzips it
            out = open(filepath, 'wb')
            out.write(bytes(polygons.read()))
            out.close()
            zip_ref = zipfile.ZipFile(filepath, 'r')
            zip_ref.extractall(dirpath)
            zip_ref.close()

            #Has to switch LAT/LON to LON/LAT, because OWlib can't do 1.0.0 and don't accept EPSG:xxxx as srs
            source_shp_path = os.path.join(dirpath, source_shapefile_name + ".shp")
            dest_shapefile_name =source_shapefile_name + "_flipped"
            dest_shp_path = os.path.join(dirpath, dest_shapefile_name + ".shp")

            print dest_shp_path
            print source_shp_path
            args = ("ogr2ogr", "-s_srs", "+proj=latlong +datum=WGS84 +axis=neu +wktext",
                    "-t_srs", "+proj=latlong +datum=WGS84 +axis=enu +wktext", "-simplify", "0.0001", dest_shp_path, source_shp_path)
            output, error = subprocess.Popen(args, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE).communicate()
            logger.info('ogr2ogr info:\n %s ' % output)
            logger.debug('ogr2ogr errors:\n %s ' % error)

            #Do clipping, without forgetting to switch GEOMCABINET
            results = clipping(
                resource=urls,
                polygons=featureidlist,
                mosaic=mosaic,
                spatial_wrapping='wrap',
                variable=variable,
                dir_output=os.path.abspath(os.curdir),
                geomcabinet=dirpath,
                geom=dest_shp_path
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

        l = len(self.outputs_netcdf)
        j = min(l,len(results))

        jj = np.arange(0,j)
        for jjj in jj:
            self.outputs_netcdf[jjj].setValue(results[jjj])



        #i = next((i for i, x in enumerate(results) if x), None)
        #self.output_netcdf.setValue(results[i])



        #self.output_netcdf2.setValue(results[1])

        self.status.set('done', 100)






