from datetime import date 
from pywps.Process import WPSProcess

from flyingpigeon.datafetch import _PRESSUREDATA_

import logging
logger = logging.getLogger(__name__)

class AnalogsProcess(WPSProcess):
  
  def __init__(self):
    # definition of this process
    WPSProcess.__init__(self, 
      identifier = "analogs_model",
      title="Analogues -- Detection",
      version = "0.9",
      metadata= [
              {"title": "LSCE", "href": "http://www.lsce.ipsl.fr/en/index.php"},
              {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/descriptions/analogues.html#analogues-of-circulation"}
              ],
      abstract="Search for days with analogue pressure pattern in a climate model data set",
      statusSupported=True,
      storeSupported=True
      )

    self.resource = self.addComplexInput(
      identifier="resource",
      title="Resource",
      abstract="URL to netCDF file",
      minOccurs=1,
      maxOccurs=1000,
      maxmegabites=5000,
      formats=[{"mimeType":"application/x-netcdf"}],
      )

    self.BBox = self.addBBoxInput(
        identifier="BBox",
        title="Bounding Box",
        abstract="coordinates to define the region to be analysed",
        minOccurs=1,
        maxOccurs=1,
        crss=['EPSG:4326']
        )
         
    self.dateSt = self.addLiteralInput(
      identifier="dateSt",
      title="Start date of analysis period",
      abstract="This is a Date: 2013-07-15",
      default="2013-07-15",
      type=type(date(2013,7,15)),
      minOccurs=0,
      maxOccurs=1,
      )
    
    self.dateEn = self.addLiteralInput(
      identifier="dateEn",
      title="End date of analysis period",
      abstract="This is a Date: 2013-12-31",
      default="2014-12-31",
      type=type(date(2014,12,31)),
      minOccurs=0,
      maxOccurs=1,
      )

    self.refSt = self.addLiteralInput(
      identifier="refSt",
      title="Start reference period",
      abstract="Start YEAR of reference period",
      default="2013-01-01",
      type=type(date(1955,01,01)),
      minOccurs=0,
      maxOccurs=1,
      )
    
    self.refEn = self.addLiteralInput(
      identifier="refEn",
      title="End reference period",
      abstract="End YEAR of reference period",
      default="2014-12-31",
      type=type(date(1957,12,31)),
      minOccurs=0,
      maxOccurs=1,
      )
    
    self.seasonwin = self.addLiteralInput(
      identifier="seasonwin",
      title="Seasonal window",
      abstract="Number of days befor and after the date to be analysed",
      default=30,
      type=type(1),
      minOccurs=0,
      maxOccurs=1,
      )

    self.nanalog = self.addLiteralInput(
      identifier="nanalog",
      title="Nr of analogues",
      abstract="Number of analogues to be detected",
      default=20,
      type=type(1),
      minOccurs=0,
      maxOccurs=1,
      )

    self.normalize = self.addLiteralInput(
      identifier="normalize",
      title="normalization",
      abstract="Normalize by subtraction of annual cycle",
      default='base',
      type=type(''),
      minOccurs=1,
      maxOccurs=1,
      allowedValues=['None','base','sim','own']
        )

    self.distance = self.addLiteralInput(
      identifier="dist",
      title="Distance",
      abstract="Distance function to define analogues",
      default='euclidean',
      type=type(''),
      minOccurs=1,
      maxOccurs=1,
      allowedValues=['euclidean','mahalanobis','cosine','of']
        )

    self.outformat = self.addLiteralInput(
      identifier="outformat",
      title="output file format",
      abstract="Choose the format for the analogue output file",
      default="ascii",
      type=type(''),
      minOccurs=1,
      maxOccurs=1,
      allowedValues=['ascii','netCDF4']
      )

    self.timewin = self.addLiteralInput(
      identifier="timewin",
      title="Time window",
      abstract="Number of days following the analogue day the distance will be averaged",
      default=1,
      type=type(1),
      minOccurs=0,
      maxOccurs=1,
      )



    ### ###################
    # define the outputs
    ### ###################

    self.config = self.addComplexOutput(
      identifier="config",
      title="Config File",
      abstract="Config file used for the Fortran process",
      formats=[{"mimeType":"text/plain"}],
      asReference=True,
      )

    self.analogs = self.addComplexOutput(
      identifier="analogs",
      title="Analogues File",
      abstract="mulit-column text file",
      formats=[{"mimeType":"text/plain"}],
      asReference=True,
      )
    
    self.output_netcdf = self.addComplexOutput(
      title="prepared netCDF",
      abstract="NetCDF file with subset and normaized values",
      formats=[{"mimeType":"application/x-netcdf"}],
      asReference=True,
      identifier="ncout",
      )


  def execute(self):
    import time # performance test
    process_start_time = time.time() # measure process execution time ...
     
    from os import path
    from tempfile import mkstemp
    from datetime import datetime as dt

    from flyingpigeon import analogs
    from flyingpigeon.ocgis_module import call
    from flyingpigeon.datafetch import reanalyses
    from flyingpigeon.utils import get_variable

    self.status.set('execution started at : %s '  % dt.now(),5)
    start_time = time.time() # measure init ...
    
    #######################
    ### read input parameters
    #######################
    try:
      self.status.set('read input parameter : %s '  % dt.now(),5) 
      resource = self.getInputValues(identifier='resource')
      refSt = self.getInputValues(identifier='refSt')
      refEn = self.getInputValues(identifier='refEn')
      dateSt = self.getInputValues(identifier='dateSt')
      dateEn = self.getInputValues(identifier='dateEn')
      normalize = self.getInputValues(identifier='normalize')[0]
      distance = self.getInputValues(identifier='dist')[0]
      outformat = self.getInputValues(identifier='outformat')[0]
      timewin = int(self.getInputValues(identifier='timewin')[0])
      bbox_obj = self.BBox.getValue()
      seasonwin = int(self.getInputValues(identifier='seasonwin')[0])
      nanalog = int(self.getInputValues(identifier='nanalog')[0])
      
      # region = self.getInputValues(identifier='region')[0]
      # bbox = [float(b) for b in region.split(',')]
      # experiment = self.getInputValues(identifier='experiment')[0] 
      # dataset , var = experiment.split('_')
      
      logger.info('input parameters set')
    except Exception as e: 
      msg = 'failed to read input prameter %s ' % e
      logger.error(msg)  
      raise Exception(msg)

    ######################################
    ### convert types and set environment
    ######################################
    try:  
      refSt = dt.strptime(refSt[0],'%Y-%m-%d')
      refEn = dt.strptime(refEn[0],'%Y-%m-%d')
      dateSt = dt.strptime(dateSt[0],'%Y-%m-%d')
      dateEn = dt.strptime(dateEn[0],'%Y-%m-%d')

      if normalize == 'None': 
        seacyc = False
      else: 
        seacyc = True         
      
      if outformat == 'ascii': 
        outformat = '.txt'
      elif outformat == 'netCDF':
        outformat = '.nc'
      else:
        logger.error('output format not valid')

      start = min( refSt, dateSt )
      end = max( refEn, dateEn )

      if bbox_obj is not None:
        logger.info("bbox_obj={0}".format(bbox_obj.coords))
        bbox = [bbox_obj.coords[0][0], bbox_obj.coords[0][1],bbox_obj.coords[1][0],bbox_obj.coords[1][1]]
        logger.info("bbox={0}".format(bbox))
      else:
        bbox=None

      logger.info('environment set')
    except Exception as e: 
      msg = 'failed to set environment %s ' % e
      logger.error(msg)  
      raise Exception(msg)

    logger.debug("init took %s seconds.", time.time() - start_time)
    self.status.set('Read in and convert the arguments', 5)
   

    ########################
    # input data preperation 
    ########################

    ##TODO: Check if files containing more than one dataset

    self.status.set('Start preparing input data', 12)
    start_time = time.time()  # mesure data preperation ...
    try:
      variable = get_variable(resource)

      archive = call(resource=resource, time_range=[refSt , refEn], geom=bbox, spatial_wrapping='wrap') 
      simulation = call(resource=resource, time_range=[dateSt , dateEn], geom=bbox, spatial_wrapping='wrap')
      if seacyc == True:
        seasoncyc_base, seasoncyc_sim = analogs.seacyc(archive, simulation, method=normalize)
      else:
        seasoncyc_base = None  
        seasoncyc_sim=None
    except Exception as e:
      msg = 'failed to prepare archive and simulation files %s ' % e
      logger.debug(msg)
      raise Exception(msg)
    ip, output = mkstemp(dir='.',suffix='.txt')
    output_file =  path.abspath(output)
    files=[path.abspath(archive), path.abspath(simulation), output_file]

    logger.debug("data preperation took %s seconds.", time.time() - start_time)

    ############################
    # generating the config file
    ############################
    
    self.status.set('writing config file', 15)
    start_time = time.time() # measure write config ...
    
    try:  
      config_file = analogs.get_configfile(
        files=files,
        seasoncyc_base = seasoncyc_base,  
        seasoncyc_sim=seasoncyc_sim,
        timewin=timewin, 
        varname=variable, 
        seacyc=seacyc, 
        cycsmooth=91, 
        nanalog=nanalog, 
        seasonwin=seasonwin, 
        distfun=distance,
        outformat=outformat,
        calccor=True,
        silent=False, 
        period=[dt.strftime(refSt,'%Y-%m-%d'),dt.strftime(refEn,'%Y-%m-%d')], 
        bbox="%s,%s,%s,%s" % (bbox[0],bbox[2],bbox[1],bbox[3]))
    except Exception as e:
      msg = 'failed to generate config file %s ' % e
      logger.debug(msg)
      raise Exception(msg)

    logger.debug("write_config took %s seconds.", time.time() - start_time)
      
    #######################
    # CASTf90 call 
    #######################
    import subprocess
    import shlex

    start_time = time.time() # measure call castf90
    
    self.status.set('Start CASTf90 call', 20)
    try:
      #self.status.set('execution of CASTf90', 50)
      cmd = 'analogue.out %s' % path.relpath(config_file)
      #system(cmd)
      args = shlex.split(cmd)
      output,error = subprocess.Popen(args, stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
      logger.info('analogue.out info:\n %s ' % output)
      logger.debug('analogue.out errors:\n %s ' % error)
      self.status.set('**** CASTf90 suceeded', 90)
    except Exception as e: 
      msg = 'CASTf90 failed %s ' % e
      logger.error(msg)  
      raise Exception(msg)

    logger.debug("castf90 took %s seconds.", time.time() - start_time)
    
    self.status.set('preparting output', 99)
    self.config.setValue( config_file )
    self.analogs.setValue( output_file )
    self.output_netcdf.setValue( simulation )
    
    self.status.set('execution ended', 100)

    logger.debug("total execution took %s seconds.", time.time() - process_start_time)
