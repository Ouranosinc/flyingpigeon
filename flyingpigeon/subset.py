# import ocgis

from .exceptions import CalculationException
from .utils import drs_filename, get_variable, calc_grouping , sort_by_filename

from malleefowl import wpslogging as logging
#import logging

logger = logging.getLogger(__name__)
from os.path import dirname, join, getsize, abspath

DIR_MASKS = join(abspath(dirname(__file__)), 'processes', 'masks')
DIR_SHP = join(abspath(dirname(__file__)), 'processes', 'shapefiles')

def countries():
    """
    :return: a list of all countries codes.
    """
    countries = _COUNTRIES_.keys()
    countries.sort()
    return countries

def countries_longname():
    """
    :return: the longname of all countries.
    """
    longname = ''
    for country in countries(): 
      longname = longname + "%s : %s \n" % (country, _COUNTRIES_[country]['longname'])
    return longname

def masking(resource, mask, prefix=None, dir_output=None):
  """
  Returns a list of masked netCDF file(s) path(es).  
  :param resource: string path to netCDF resource
  :param mask: predifined mask ('EUR-11', 'EUR-44')
  :param prefix:  prefix for filename. If prefix is not set, a filename will be created
  :param dir_output: directory for output file. If dir_output is not set, a tempdir will be created
  """
  from cdo import Cdo
  cdo = Cdo()
  from tempfile import mkstemp
  from os import system, path 
  
  if dir_output == None: 
    dir_output = path.curdir
  nc_mask = path.join(DIR_MASKS, mask + '.nc')
  
  if prefix == None: 
    p1 , resource_masked = mkstemp(dir = dir_output, suffix='.nc')
  else: 
    resource_masked = path.join(dir_output, prefix + '.nc')
# try:
  call = "cdo div '%s' '%s' '%s'" % ( resource , nc_mask , resource_masked)
  system(call)
  return resource_masked


def clipping(resource=[], variable=None, dimension_map=None, calc=None,  
  calc_grouping= None, prefix=None, polygons='Europe', dir_output=None):
  """ returns list of clipped netCDF files
  possible entries: 
  :param resource: list of input netCDF files
  :param variable: variable (string) to be used in netCDF
  :param dimesion_map: specify a dimension map input netCDF has unconventional dimension
  :param calc: ocgis calculation argument
  :param calc_grouping: ocgis calculation grouping 
  :param prefix: prfix for output file name
  :param polygons: list of polygons to be used. if more than 1 in the list, a appropriate mosaik will be clipped
  :param output_format: output_format (default='nc')
  :param dir_output: specify a output location
  """
  from ocgis import OcgOperations, RequestDataset , env
  from ocgis.util.large_array import compute
  from flyingpigeon.utils import get_variable
  from numpy import sqrt
  env.DIR_SHPCABINET = DIR_SHP
  env.OVERWRITE = True
  limit_memory_mb = 475.0 # to reduce the load of the memory, calculation is perfored in chunks

  if type(resource) != list: 
    resource = list([resource])
  if type(polygons) != list:
    polygons = list([polygons])
  
  try:
    geoms = []
    for polygon in polygons: 
      geoms.append(get_geom(polygon))
    if len(geoms) > 1: 
      logger.error('polygons belong to differnt shapefiles! mosaik is not possible %s', geoms)
    else: 
      geom = geoms[0]
      #print 'geom: %s' % (geom)
  except Exception as e:
    logger.error('geom identification failed %s', e)
  
  ugids = get_ugid(polygons=polygons, geom=geom)
  #print 'ugids: %s' % (ugids)
  ncs = sort_by_filename(resource)
  geom_files = []
  
  for key in ncs:
    if variable == None:
      variable = get_variable(ncs[key])
      logger.info('variable %s detected in resource' % (variable))  
    try:    
      rd = RequestDataset(ncs[key], variable=variable, dimension_map=dimension_map)
      env.DIR_OUTPUT = dir_output
      env.PREFIX = prefix    
      ops = OcgOperations(dataset=rd, 
        calc=calc, 
        calc_grouping=calc_grouping,
        output_format='nc', # necessary for chunked execution  
        select_ugid=ugids, 
        geom=geom, 
        add_auxiliary_files=False)
      # swith beween chunking and 'en block' computation  
      fsize = 0 
      for nc in ncs[key]: 
        fsize = fsize + getsize(nc)
      if fsize / 1000000 <= 500:          
        geom_file = ops.execute()
        geom_files.append( geom_file )
      else: 
        # calcultion of chunk size
        size = ops.get_base_request_size()
        nb_time_coordinates_rd = size['variables'][variable]['temporal']['shape'][0]
        element_in_kb = size['total']/reduce(lambda x,y: x*y,size['variables'][variable]['value']['shape'])
        element_in_mb = element_in_kb*0.001
        tile_dim = sqrt(limit_memory_mb/(element_in_mb*nb_time_coordinates_rd))
        geom_file = compute(ops, tile_dimension=int(tile_dim), verbose=True)
        geom_files.append( geom_file )
    except Exception as e:
      msg = 'ocgis calculations failed for %s ' % (key)
      logger.exception(msg)
      raise CalculationException(msg, e)
  return  geom_files

def get_dimension_map(resource): 
  """ returns the dimension map for a file, required for ocgis processing. 
  file must have a DRS conform filename (see: utils.drs_filename())
  
  :param resource: str input file path
  """

  from os.path import basename
  file_name = basename(resource)
  
  dim_map1 = {'X': {'variable': 'lon', 'dimension': 'x', 'pos': 2},
              'Y': {'variable': 'lat', 'dimension': 'y', 'pos': 1},
              'T': {'variable': 'time', 'dimension': 'time', 'pos': 0}}
  
  #dim_map2 = {'X': {'variable': 'lon', 'dimension': 'x', 'pos': 2},
              #'Y': {'variable': 'lat', 'dimension': 'y', 'pos': 1},
              #'T': {'variable': 'time', 'dimension': 'time', 'pos': 0, 'bounds': 'time_bnds'}}
  
  dim_map3 = {'X': {'variable': 'rlon', 'dimension': 'x', 'pos': 2},
              'Y': {'variable': 'rlat', 'dimension': 'y', 'pos': 1},
              'T': {'variable': 'time', 'dimension': 'time', 'pos': 0 }}

  dim_map4 = {'X': {'variable': 'Actual_longitude', 'dimension': 'x', 'pos': 2},
              'Y': {'variable': 'Actual_latitude', 'dimension': 'y', 'pos': 1},
              'T': {'variable': 'time', 'dimension': 'time', 'pos': 0 }}

  dim_map5 = {'X': {'variable': 'x', 'dimension': 'x', 'pos': 2},
              'Y': {'variable': 'y', 'dimension': 'y', 'pos': 1},
              'T': {'variable': 'time', 'dimension': 'time', 'pos': 0 }}
  
  if 'CM5A-MR_WRF331F' in file_name: 
    dimension_map = dim_map1
  elif 'CNRM-CM5_CNRM-ALADIN53' in file_name: 
    dimension_map = dim_map1
  elif 'MPI-ESM-LR_REMO019' in file_name: 
    dimension_map = dim_map1
  elif 'CLMcom-CCLM4-8-17' in file_name:
    dimension_map = dim_map1
  elif '_v11.0' in file_name: # EOBS Data
    dimension_map = dim_map4
  #elif 'EOBS' in file_name:   
    #dimension_map = dim_map5
  else:     
    dimension_map = None
    
  return dimension_map


def get_shp_column_values(geom, columnname): 
  """ returns a list of all entries the shapefile columnname
  :param geom: name of the shapefile
  :param columnname: Column name to be intereted
  """
  from ocgis import env, ShpCabinetIterator
  #import ocgis
  
  env.DIR_SHPCABINET = DIR_SHP
  sci = ShpCabinetIterator(geom)
  
  vals = []
  for row in sci: 
    vals.append(row['properties'][columnname])
  return vals


# === Functions for Clipping:
def get_ugid(polygons='FRA', geom='50m_country'):
    """
    returns geometry id of given polygon in a given shapefile.
    :param polygons: string or list of the region polygons 
    :param geom: available shapefile possible entries: '50m_country', 'NUTS2'
    """
    from ocgis import env, ShpCabinetIterator
    #from ocgis import env
    
    if type(polygons) != list:
      polygons = list([polygons])
    
    env.DIR_SHPCABINET = DIR_SHP
    sc_iter = ShpCabinetIterator(geom)
    result = []
    
    if geom == 'countries':
      for row in sc_iter:
        for polygon in polygons:
          if row['properties']['ADM0_A3'] == polygon:
            result.append(row['properties']['UGID'])
              
    # elif geom == 'NUTS2':
    #   for row in sc_iter:
    #     for polygon in polygons:
    #       if row['properties']['NUTS_ID'] == polygon:
    #         result.append(row['properties']['UGID'])

    elif geom == 'extremoscope':
      for row in sc_iter:
        for polygon in polygons:
          if row['properties']['HASC_1'] == polygon:
            result.append(row['properties']['UGID'])
              
    elif geom == 'continents':
      for row in sc_iter:
        for polygon in polygons:
          if row['properties']['CONTINENT'] == polygon:
            result.append(row['properties']['UGID'])    
    else:
      from ocgis import ShpCabinet
      sc = ShpCabinet(DIR_SHP)
      logger.error('geom: %s not found in ShapeCabinet. Available geoms are: %s ', geom, sc) 

    return result

def get_geom(polygon):

  if polygon in _COUNTRIES_: # (polygon) == 3:
    geom = 'countries'
  elif polygon in _POLYGONS_EXTREMOSCOPE_: #len(polygon) == 5 and polygon[2] == '.': 
    geom = 'extremoscope'
  elif polygon in _CONTINENTS_: 
    geom = 'continents'
  else:
    logger.error('polygon: %s not found in geoms' % polygon) 

  return geom  

# === Available Polygons
_CONTINENTS_ = get_shp_column_values(geom='continents', columnname='CONTINENT') 

_COUNTRIES_ = {}
_COUNTRIES_Europe_ = {}
_POLYGONS_EXTREMOSCOPE_ = get_shp_column_values(geom='extremoscope', columnname='HASC_1')

# === popultate poligon dictionaties 
ADM0_A3 = get_shp_column_values(geom='countries', columnname='ADM0_A3')
NAMELONG = get_shp_column_values(geom='countries', columnname='NAME_LONG')
CONTINENT = get_shp_column_values(geom='countries', columnname='CONTINENT')
for c , key in enumerate(ADM0_A3): 
  _COUNTRIES_[key] = dict(longname=NAMELONG[c])

for c , key in enumerate(ADM0_A3):
  if CONTINENT[c] == 'Europe':
    _COUNTRIES_Europe_[key] = dict(longname=NAMELONG[c])