import os
import shutil
import time
import json
import tempfile
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from pywps import Process
from pywps import LiteralInput
from pywps import ComplexOutput
from pywps import get_format, configuration
import owslib
from owslib.wfs import WebFeatureService
import ocgis
import netCDF4
from shapely.geometry import shape


# Copying a few recurring functions here for now to avoid conflicts,
# Should be moved to something like utils.py for a proper pull request
# eventually...

def guess_main_variable(ncdataset):
    # The main variable is the one with highest dimensionality, if there are
    # more than one, the one with the larger size is the main variable.

    # Exclude time, lon, lat and variables that are defined as bounds
    var_candidates = []
    bnds_variables = []
    for var_name in ncdataset.variables:
        if var_name in ['time', 'lon', 'lat']:
            continue
        ncvar = ncdataset.variables[var_name]
        if hasattr(ncvar, 'bounds'):
            bnds_variables.append(ncvar.bounds)
        var_candidates.append(var_name)
    var_candidates = list(set(var_candidates) - set(bnds_variables))

    # Find main variable among the candidates
    nd = -1
    size = -1
    for var_name in var_candidates:
        ncvar = ncdataset.variables[var_name]
        if len(ncvar.shape) > nd:
            main_var = var_name
            nd = len(ncvar.shape)
            size = ncvar.size
        elif (len(ncvar.shape) == nd) and (ncvar.size > size):
            main_var = var_name
            size = ncvar.size
    return main_var

def opendap_or_download(resource, output_path=None):
    try:
        nc = netCDF4.Dataset(resource, 'r')
        nc.close()
    except:
        response = urlopen(resource)
        CHUNK = 16 * 1024
        if not output_path:
            output_path = os.getcwd()
        output_file = os.path.join(output_path, os.path.basename(resource))
        with open(output_file, 'wb') as f:
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
        try:
            nc = netCDF4.Dataset(output_file, 'r')
            nc.close()
        except:
            raise IOError("This does not appear to be a valid NetCDF file.")
        return output_file
    return resource

json_format = get_format('JSON')
output_path = configuration.get_config_value('server', 'outputpath')
url_path = configuration.get_config_value('flyingpigeon', 'base_url')

class SubsetWFS(Process):
    def __init__(self):
        inputs = [LiteralInput('resource',
                               'Resource',
                               data_type='string',
                               max_occurs=1000),
                  LiteralInput('typename',
                               'TypeName',
                               data_type='string'),
                  LiteralInput('featureids',
                               'Feature Ids',
                               data_type='string',
                               max_occurs=1000),
                  LiteralInput('geoserver',
                               'Geoserver',
                               data_type='string',
                               min_occurs=0),
                  LiteralInput('mosaic',
                               'Union of multiple regions',
                               data_type='boolean',
                               abstract=("If True, selected regions will be "
                                         "merged nto a single geometry."),
                               min_occurs=0,
                               default=False),
                  LiteralInput('variable',
                               'Variable',
                               data_type='string',
                               min_occurs=0,
                               default=''),]

        outputs = [ComplexOutput('output',
                                 'JSON file with NetCDF outputs',
                                 as_reference=True,
                                 supported_formats=[json_format])]

        super(SubsetWFS, self).__init__(
            self._handler,
            identifier="subset_WFS",
            title="Subset WFS",
            version="0.10",
            abstract=("Return the data whose grid cells intersect the "
                      "selected polygon for each input dataset."),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        list_of_files = []
        for one_resource in request.inputs['resource']:
            # Download if not opendap
            nc_file = opendap_or_download(one_resource.data, '/tmp')
            list_of_files.append(nc_file)

        if 'mosaic' in request.inputs:
            mosaic = request.inputs['mosaic'][0].data
        else:
            mosaic = False

        features = [f.data for f in request.inputs['featureids']]
        typename = request.inputs['typename'][0].data
        if 'geoserver' in request.inputs:
            geoserver = request.inputs['geoserver'][0].data
        else:
            geoserver = configuration.get_config_value(
                "extra", "geoserver")

        try:
            conn = WebFeatureService(url=geoserver, version='2.0.0')
            resp = conn.getfeature([typename,], featureid=features,
                                   outputFormat='application/json')
            feature = json.loads(resp.read())
            crs_code = owslib.crs.Crs(
                feature['crs']['properties']['name']).code
            crs = ocgis.CoordinateReferenceSystem(epsg=crs_code)
            geom = [{'geom': shape(f['geometry']), 'crs': crs, \
                     'properties': f['properties']} \
                    for f in feature['features']]
        except Exception as e:
            msg = ("Failed to fetch features.\ngeoserver: {0} \n"
                   "typename: {1}\nfeatures {2}\n{3}").format(
                      geoserver, typename, features, e)
            raise Exception(msg)

        #if mosaic:
            #new_geom = geom[0]
            #for merge_geom in geom[1:]:
                #new_geom = new_geom.union(merge_geom)
        #geom = new_geom

        output_files = []
        output_urls = []
        for one_file in list_of_files:
            file_name = os.path.basename(one_file)
            if file_name[-3:] == '.nc':
                file_prefix = file_name[:-3]
            else:
                file_prefix = file_name
            ocgis.env.DIR_OUTPUT = os.getcwd()
            nc = netCDF4.Dataset(one_file, 'r')
            var_name = guess_main_variable(nc)
            nc.close()
            rd = ocgis.RequestDataset(one_file, var_name)
            ops = ocgis.OcgOperations(dataset=rd, geom=geom,
                                      snippet=False, output_format='nc',
                                      interpolate_spatial_bounds=True,
                                      prefix=file_prefix).execute()
            mv_dir = tempfile.mkdtemp(dir=output_path)
            mv_file = os.path.join(mv_dir, os.path.basename(ops))
            shutil.move(ops, mv_file)
            output_files.append(mv_file)
            if 'url_path' not in locals():
                url_path = 'file:///'
            output_urls.append(os.path.join(
                url_path, output_path.split('/')[-1], mv_dir.split('/')[-1],
                os.path.basename(mv_file)))

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "result_%s_.json" % (time_str,)
        output_file = os.path.join(output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(json.dumps(output_urls))
        f1.close()
        response.outputs['output'].file = output_file
        response.outputs['output'].output_format = json_format
        response.update_status("done", 100)
        return response
