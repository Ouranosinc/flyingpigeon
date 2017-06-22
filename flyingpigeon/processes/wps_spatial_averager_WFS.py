import os
import uuid
import zipfile
import logging
import subprocess
import json

from flyingpigeon.subset import clipping
from flyingpigeon import config
from pywps.Process import WPSProcess
from owslib.wfs import WebFeatureService

logger = logging.getLogger(__name__)

class WFSClippingProcess(WPSProcess):
    def __init__(self):
        WPSProcess.__init__(
            self, 
            identifier="spatial_averager_WFS",
            title="Spatial averager WFS",
            version="0.1",
            abstract="Fetch a shapefile from a WFS server and return averaged timeseries in JSON for all the polygons it contains",
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

        self.tarout = self.addComplexOutput(
            identifier="tarout",
            title="Tarfile",
            abstract="tar archive containing the value tables",
            formats=[{"mimeType": "application/x-tar"}],
            asReference=True,
        )

    def execute(self):
        urls = self.getInputValues(identifier='resource')
        featureids = self.featureids.getValue()
        xmlfilter = self.xmlfilter.getValue()
        typename = self.typename.getValue()
        variable = self.variable.getValue()

        logger.info('urls = %s', urls)
        logger.info('filter = %s', xmlfilter)
        logger.info('typename = %s', typename)
        logger.info('featureids = %s', featureids)
    
        self.status.set('Arguments set for WPS spatial averager process', 0)
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
            dirpath = os.path.join(config.cache_path(), unique_dirname)
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
            args = ("ogr2ogr", "-s_srs", "\"+proj=latlong +datum=WGS84 +axis=neu +wktext\"",
                    "-t_srs", "\"+proj=latlong +datum=WGS84 +axis=enu +wktext\"",  dest_shp_path, source_shp_path)
            popen = subprocess.Popen(args, stdout=subprocess.PIPE)
            popen.wait()

            #Do clipping, without forgetting to switch GEOMCABINET
            timeseries = clipping(
                resource=urls,
                polygons=featureidlist,
                spatial_wrapping='wrap',
                variable=variable,
                dir_output=os.path.abspath(os.curdir),
                historical_concatination=False,
                geomcabinet=dirpath,
                geom=dest_shapefile_name,
                output_format='numpy',
                spatial_operation='clip',
                aggregate=True,
                interpolate_spatial_bounds=True
                )
            logger.info('WPS spatial averager done')
        except Exception as e:
            msg = 'WPS spatial averaging failed'
            logger.exception(msg)
            raise Exception(msg)

        # This gives the masked array
        # timeseries[n][1].items()[0][1].variables.items()[m][1].value

        if not timeseries:
            raise Exception('no results produced.')
        else:
            for poly_idx in range(len(timeseries)):
                result_nested_list = timeseries[poly_idx][1].items()[0][1].variables.items()[0][1].value.tolist()
                flatten=lambda l: sum(map(flatten,l),[]) if isinstance(l,list) else [l]
                result_list = flatten(result_nested_list)
                file_path = os.path.join(config.output_path(), 'output{}.json'.format(poly_idx))
                with open(file_path, 'w') as fp:
                    json.dump(result_list, fp)
                fp.close()

        self.status.set('done', 100)






