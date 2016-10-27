import os

from flyingpigeon.subset import clipping
from pywps.Process import WPSProcess
from owslib.wfs import WebFeatureService
from owslib.fes import *
from owslib.etree import etree

import uuid
import zipfile
import logging
import shutil
logger = logging.getLogger(__name__)


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

        # self.output = self.addComplexOutput(
        #     title="Subsets",
        #     abstract="Tar archive containing the netCDF files",
        #     formats=[{"mimeType":"application/x-tar"}],
        #     asReference=True,
        #     identifier="output",
        #     )
        #
        # self.output_netcdf = self.addComplexOutput(
        #     title="Subsets for one dataset",
        #     abstract="NetCDF file with subsets of one dataset.",
        #     formats=[{"mimeType":"application/x-netcdf"}],
        #     asReference=True,
        #     identifier="ncout",
        #     )

    def execute(self):
        urls = self.getInputValues(identifier='resource')
        mosaic = self.mosaic.getValue()
        featureids = self.featureids.getValue()
        xmlfilter = self.xmlfilter.getValue()
        typename = self.typename.getValue()

        logger.info('urls = %s', urls)
        logger.info('filter = %s', xmlfilter)
        logger.info('mosaic = %s', mosaic)
        logger.info('typename = %s', typename)
        logger.info('featureids = %s', featureids)
    
        self.status.set('Arguments set for WPS subset process', 0)
        logger.debug('starting: num_files=%s' % (len(urls)))

        try:

            #Validate typename first?

            #Connect to WFS server
            wfs = WebFeatureService("http://132.217.140.48:8080/geoserver/wfs", "1.1.0")

            # What type of request will we do
            if featureids is None:
                if xmlfilter is None:
                    filterprop = PropertyIsLike(propertyname='STATE_NAME', literal='TEXAS', wildCard='*')
                    xmlfilter_fromprops = etree.tostring(filterprop.toXML()).decode("utf-8")
                    polygons = wfs.getfeature(typename=typename, filter=xmlfilter_fromprops, outputFormat='shape-zip')
                else:
                    raise Exception('Feature Ids or XML filter required')
            else:
                featurelist = featureids.split(",")
                polygons = wfs.getfeature(typename=typename, featureid=featurelist, outputFormat='shape-zip')

            #get unique name for folder and create it
            unique_dirname = str(uuid.uuid4())
            dirpath = os.path.join('/mnt/shared/', unique_dirname)
            os.mkdir(dirpath)
            filepath = os.path.join(dirpath, 'file.zip')

            #Saves the result in folder and unzips it
            out = open(filepath, 'wb')
            out.write(bytes(polygons.read()))
            out.close()
            zip_ref = zipfile.ZipFile(filepath, 'r')
            zip_ref.extractall(dirpath)
            zip_ref.close()

            #Swith GeoCabinet

            #Do clipping
            # results = clipping(
            #    resource = urls,
            #    polygons = regions, # self.region.getValue(),
            #    mosaic = mosaic,
            #    spatial_wrapping='wrap',
            #    variable = variable,
            #    dir_output = os.path.abspath(os.curdir),
            #    )

            #Remove folder
            shutil.rmtree(dirpath)

            results = True
            logger.info('Done')
        except Exception as e:
            msg = 'WPS clipping failed'
            logger.exception(msg)
            raise Exception(msg)

        if not results:
            raise Exception('no results produced.')

        #self.output.setValue("")
        #self.output_netcdf.setValue("")
        self.status.set('done', 100)
