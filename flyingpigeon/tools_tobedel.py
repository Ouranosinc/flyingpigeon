import ocgis
from ocgis import RequestDataset
from ocgis.interface.base.crs import CFWGS84

from netCDF4 import Dataset
import os 
from datetime import datetime, timedelta

from flyingpigeon import config

import logging
logger = logging.getLogger(__name__)

def dummy_monitor(message, status):
    logger.info("%s: progress %s/100", message, status)

def fn_creator( ncs ):
  newnames = []
  for nc in ncs:
    fp ,fn = os.path.split(nc)
    # logger.debug('fn_creator for: %s' % fn)
    ds = Dataset(nc)
    rd = []
    rd = RequestDataset(nc)
    ts = ds.variables['time']
    reftime = reftime = datetime.strptime('1949-12-01', '%Y-%m-%d')
    st = datetime.strftime(reftime + timedelta(days=ts[0]), '%Y%m%d') 
    en = datetime.strftime(reftime + timedelta(days=ts[-1]), '%Y%m%d') 
    
    if (str(ds.project_id) == 'CMIP5'):
    #day_MPI-ESM-LR_historical_r1i1p1
      var = str(rd.variable)
      frq = str(ds.frequency)
      gmodel = str(ds.model_id)
      exp = str(ds.experiment_id)
      ens = str(ds.parent_experiment_rip)
      filename = var + '_' + str( gmodel + '_' + exp + '_' + ens + '_' + str(int(st)) + '-' + str(int(en)) + '.nc')
        
    elif (str(ds.project_id) == 'CORDEX'):
    #EUR-11_ICHEC-EC-EARTH_historical_r3i1p1_DMI-HIRHAM5_v1_day
      var = str(rd.variable)
      dom = str(ds.CORDEX_domain)
      gmodel = str(ds.driving_model_id)
      exp = str(ds.experiment_id)
      ens = str(ds.driving_model_ensemble_member)
      rmodel = str(ds.model_id)
      ver = str(ds.rcm_version_id)
      frq = str(ds.frequency)
      filename = str(var + '_'+ dom + '_' + gmodel + '_' + exp + '_' + ens + '_' + rmodel + '_' + ver + \
        '_' + frq + '_' + str(int(st)) + '-' + str(int(en)) + '.nc' )
    else:
      filename = fn 
      logger.debug('WPS name forwarded :%s' % ( filename))
      
    ##except Exception as e: 
      #msg = 'Could not define file name for file : %s %s' % ( nc , e )
      #logger.error(msg)
      #outlog = outlog + msg + '\n'
    os.rename(nc, os.path.join(fp, filename ))
    newnames.append(os.path.join(fp, filename))
    logger.debug('file name generated and renamed :%s' % ( filename))
  return newnames

def fn_sorter(ncs): 
  ndic = {}
  rndic = {}
  for nc in ncs:
    #logger.debug('file: %s' % nc)
    p, f = os.path.split(nc) 
    n = f.split('_')
    bn = '_'.join(n[0:-1])
    ndic[bn] = []
  for key in ndic: 
    for n in ncs:
      if key in n: 
        ndic[key].append(n)  
  logger.debug('Data Experiment dictionary build: %i experiments found' % (len(ndic.keys())))
  return ndic

def fn_sorter_ch(ncs):
  ndic = {}
  for nc in ncs:
    #logger.debug('file: %s' % nc)
    p, f = os.path.split(nc) 
    n = f.split('_')
    bn = '_'.join(n[0:-1])
    if n[3] != 'historical':
      ndic[bn] = []      
  for key in ndic:
    historical = key.replace('rcp26','historical').replace('rcp45','historical').replace('rcp85','historical')
    for n in ncs:
      if key in n or historical in n: 
        ndic[key].append(n)     
  logger.debug('Data Experiment dictionary build: %i experiments found' % (len(ndic.keys())))
  logger.debug('experiments: %s ' % (ndic.keys()))
  return ndic # rndic
  
def indices( idic, monitor=dummy_monitor ):
  monitor('monitor: starting indices calculation', 6)
  
  group = idic['group'] if idic.has_key('group') else 'year'
  if group == 'mon':
    calc_grouping = ['month']
  else: #  group == 'year':
    calc_grouping = ['year']
  
  logger.debug('calc_grouping = %s' % calc_grouping)
  
  icclim = idic['icclim'] if idic.has_key('icclim') else None
  uris = idic['ncs'] if idic.has_key('ncs') else  None
  concat = idic['concat'] if idic.has_key('concat') else  None
  TG = idic['TG'] if idic.has_key('TG') else  None
  TX = idic['TX'] if idic.has_key('TX') else  None
  TN = idic['TN'] if idic.has_key('TN') else  None
  TXn = idic['TXn'] if idic.has_key('TXn') else  None
  TXx = idic['TXx'] if idic.has_key('TXx') else  None
  TNn = idic['TNn'] if idic.has_key('TNn') else  None
  TNx = idic['TNx'] if idic.has_key('TNx') else  None
  SU = idic['SU'] if idic.has_key('SU') else  None
  CSU = idic['CSU'] if idic.has_key('CSU') else  None
  FD = idic['FD'] if idic.has_key('FD') else  None
  CFD = idic['CFD'] if idic.has_key('CFD') else  None
  TR = idic['TR'] if idic.has_key('TR') else  None
  ID = idic['ID'] if idic.has_key('ID') else  None
  HD17 = idic['HD17'] if idic.has_key('HD17') else  None
  GD4 = idic['GD4'] if idic.has_key('GD4') else  None
  RR = idic['RR'] if idic.has_key('RR') else  None
  RR1 = idic['RR1'] if idic.has_key('RR1') else  None
  CWD = idic['CWD'] if idic.has_key('CWD') else  None
  SDII = idic['SDII'] if idic.has_key('SDII') else  None
  R10mm = idic['R10mm'] if idic.has_key('R10mm') else  None
  R20mm = idic['R20mm'] if idic.has_key('R20mm') else  None
  RX1day = idic['RX1day'] if idic.has_key('RX1day') else  None
  RX5day = idic['RX5day'] if idic.has_key('RX5day') else  None
  SD = idic['SD'] if idic.has_key('SD') else  None
  SD1 = idic['SD1'] if idic.has_key('SD1') else  None
  SD5cm = idic['SD5cm'] if idic.has_key('SD5cm') else  None
  SD50cm = idic['SD50cm'] if idic.has_key('SD50cm') else  None
  CDD = idic['CDD'] if idic.has_key('CDD') else  None
  logger.debug('gcalc_roup set to : %s' % ( group ))
  
  outlog = "Starting the indice calculation at: %s \n" % (datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y'))
  logger.debug('starting icclim indices ... done')
  logger.debug('icclim ... : %s' % ( icclim ))
  
  ocgis.env.OVERWRITE = True
  ocgis.env.DIR_DATA = os.path.curdir
  ocgis.env.DIR_OUTPUT = icclim    
  output_crs = None
  
  logger.debug('settings for ocgis done')
  outlog = outlog + "settings for ocgis done \n"
  
  c = 0 
  for nc in uris :
    c = c + 1 
    monitor('Starting icclim indices for %i of %i experiments ' % (c , len(uris)) , (100/len(uris)*c ))
    
    # loop over the years: 
    
    ds = Dataset(nc)
    ts = ds.variables['time']
    reftime = reftime = datetime.strptime('1949-12-01', '%Y-%m-%d')
    st = int(datetime.strftime(reftime + timedelta(days=ts[0]), '%Y'))
    en = int(datetime.strftime(reftime + timedelta(days=ts[-1]), '%Y'))
    logger.debug('calculation for the years: %i - %i'  % (st , en))
    
    
    for y in range(st,en+1,1):
    
      p, f = os.path.split(os.path.abspath(nc))
      logger.debug('processing file %s ' % (f ))
      bn, ext = os.path.splitext(f)
      n = bn.split('_')
      base = '_'.join(n[0:-1]) # extract the dateinfo
      basename = '%s_%i' % (base, y)
      # = bn # .replace('day', group)
      
      var = f.split('_')[0]
      rd = RequestDataset(nc, var, time_region = {'year':[y]}) # time_range=[dt1, dt2] 
      logger.debug('calculation of experimtent %s with variable %s' % (basename , var))
      
    #for nc in ncs:
      #fp, fn = os.path.split(nc)
      #basename = os.path.splitext(fn)[0]
      #ds = Dataset(nc)
      try:
        if TG == True and var == 'tas': # ds.variables.keys():
          logger.debug('calculation for TG started ')
          TG_file = None
          calc_icclim = [{'func':'icclim_TG','name':'TG'}]
          rds = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix= (basename.replace('tas_','TG_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False)
          TG_file= rds.execute()
          logger.debug('TG calculated ' )
          outlog = outlog + "TG indice processed sucessfully for %s \n" % basename
          monitor('TG indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
          #TG_file = fn_creator( TG_file )
        
        if TX == True and  var =="tasmax" :
          logger.debug('calculation for TX started ')
          TX_file = None
          calc_icclim = [{'func':'icclim_TX','name':'TX'}]
          TX_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmax_','TX_')) , output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TX calculated ' )
          outlog = outlog + "TX indice processed sucessfully for %s \n" % basename
          monitor('TX indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
          
        if TN == True and var =="tasmin" :
          logger.debug('calculation for TN started ')
          TN_file = None
          calc_icclim = [{'func':'icclim_TN','name':'TN'}]
          TN_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','TN_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TN calculated ' )
          outlog = outlog + "TN indice processed sucessfully for %s \n" % basename
          monitor('TN indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if TXx == True and  var =="tasmax" :
          logger.debug('calculation for TXx started ')
          TXx_file = None
          calc_icclim = [{'func':'icclim_TXx','name':'TXx'}]
          TXx_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmax_','TXx_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TXx calculated ' )
          outlog = outlog + "TXx indice processed sucessfully for %s \n" % basename
          monitor('TXx indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if TNx == True and var =="tasmin" :
          logger.debug('calculation for TNx started ')
          TNx_file = None
          calc_icclim = [{'func':'icclim_TNx','name':'TNx'}]
          TN_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','TNx_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TNx calculated ' )
          outlog = outlog + "TNx indice processed sucessfully for %s \n" % basename
          monitor('TNx indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if TNn == True and var =="tasmin" :
          logger.debug('calculation for TNn started ')
          TNn_file = None
          calc_icclim = [{'func':'icclim_TNn','name':'TNn'}]
          TN_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','TNn_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TNn calculated ' )
          outlog = outlog + "TNn indice processed sucessfully for %s \n" % basename
          monitor('TNn indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if SU == True and  var =="tasmax" :
          logger.debug('calculation for SU started ')
          SU_file = None
          calc_icclim = [{'func':'icclim_SU','name':'SU'}]
          SU_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmax_','SU_')), output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SU calculated ' )
          outlog = outlog + "SU indice processed sucessfully for %s \n" % basename
          monitor('SU indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if CSU == True and  var =="tasmax" :
          logger.debug('calculation for CSU started ')
          SU_file = None
          calc_icclim = [{'func':'icclim_CSU','name':'CSU'}]
          CSU_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmax_','CSU_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('CSU calculated ' )
          outlog = outlog + "CSU indice processed sucessfully for %s \n" % basename
          monitor('CSU indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if FD == True and var =="tasmin" :
          logger.debug('calculation for FD started ')
          FD_file = None
          calc_icclim = [{'func':'icclim_FD','name':'FD'}]
          FD_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','FD_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('FD calculated ' )
          outlog = outlog + "FD indice processed sucessfully for %s \n" % basename
          monitor('FD indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if CFD == True and var =="tasmin" :
          logger.debug('calculation for CFD started ')
          CFD_file = None
          calc_icclim = [{'func':'icclim_CFD','name':'CFD'}]
          CFD_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','CFD_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('CFD calculated ' )
          outlog = outlog + "CFD indice processed sucessfully for %s \n" % basename
          monitor('CFD indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if TR == True and var =="tasmin" :
          logger.debug('calculation for TR started ')
          TR_file = None
          calc_icclim = [{'func':'icclim_TR','name':'TR'}]
          TR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmin_','TR_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('TR calculated ' )
          outlog = outlog + "TR indice processed sucessfully for %s \n" % basename
          monitor('TR indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))


        if ID == True and  var =="tasmax" :
          logger.debug('calculation for ID started ')
          ID_file = None
          calc_icclim = [{'func':'icclim_ID','name':'ID'}]
          IR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tasmax_','ID_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('ID calculated ' )
          outlog = outlog + "ID indice processed sucessfully for %s \n" % basename
          monitor('ID indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if HD17 == True and var =="tas" :
          logger.debug('calculation for HD17 started ')
          HD17_file = None
          calc_icclim = [{'func':'icclim_HD17','name':'HD17'}]
          IR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tas_','HD17_')) ,
          output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('HD17 calculated ' )
          outlog = outlog + "HD17 indice processed sucessfully for %s \n" % basename
          monitor('HD17 indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if GD4 == True and var =="tas" :
          logger.debug('calculation for GD4 started ')
          GD4_file = None
          calc_icclim = [{'func':'icclim_GD4','name':'GD4'}]
          IR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('tas_','GD4_')) , output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('GD4 calculated ' )
          outlog = outlog + "GD4 indice processed sucessfully for %s \n" % basename
          monitor('GD4 indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if RR == True and var == "pr" :
          logger.debug('calculation for RR started ')
          RR_file = None
          calc_icclim = [{'func':'icclim_RR','name':'RR'}]
          RR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','RR_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('RR calculated ' )
          outlog = outlog + "RR indice processed sucessfully for %s \n" % basename
          monitor('RR indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if RR1 == True and var == "pr" :
          logger.debug('calculation for RR1 started ')
          RR1_file = None
          calc_icclim = [{'func':'icclim_RR1','name':'RR1'}]
          RR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','RR1_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('RR1 calculated ' )
          outlog = outlog + "RR1 indice processed sucessfully for %s \n" % basename
          monitor('RR1 indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if CWD == True and var == "pr" :
          logger.debug('calculation for CWD started ')
          CWD_file = None
          calc_icclim = [{'func':'icclim_CWD','name':'CWD'}]
          RR_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','CWD_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('CWD calculated ' )
          outlog = outlog + "CWD indice processed sucessfully for %s \n" % basename
          monitor('CWD indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if SDII == True and var == "pr" :
          logger.debug('calculation for SDII started ')
          SDII_file = None
          calc_icclim = [{'func':'icclim_SDII','name':'SDII'}]
          SDII_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','SDII_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SDII calculated ' )
          outlog = outlog + "SDII indice processed sucessfully for %s \n" % basename
          monitor('SDII indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if R10mm == True and var == "pr" :
          logger.debug('calculation for R10mm started ')
          R10mm_file = None
          calc_icclim = [{'func':'icclim_R10mm','name':'R10mm'}]
          R10mm_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','R10mm_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('R10mm calculated ' )
          outlog = outlog + "R10mm indice processed sucessfully for %s \n" % basename
          monitor('R10mm indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if R20mm == True and var == "pr" :
          logger.debug('calculation for R20mm started ')
          R20mm_file = None
          calc_icclim = [{'func':'icclim_R20mm','name':'R20mm'}]
          R20mm_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','R20mm_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('R20mm calculated ' )
          outlog = outlog + "R20mm indice processed sucessfully for %s \n" % basename
          monitor('R20mm indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                    
        if RX1day == True and var == "pr" :
          logger.debug('calculation for RX1day started ')
          RX1day_file = None
          group = ['year']
          calc_icclim = [{'func':'icclim_RX1day','name':'RX1day'}]
          RX1day_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','RX1day_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('RX1day calculated ' )
          outlog = outlog + "RX1day indice processed sucessfully for %s \n" % basename
          monitor('RX1day indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
                                      
        if RX5day == True and var == "pr" :
          logger.debug('calculation for RX5day started ')
          RX5day_file = None
          calc_icclim = [{'func':'icclim_RX5day','name':'RX5day'}]
          RX5day_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','RX5day_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('RX5day calculated ' )
          outlog = outlog + "RX5day indice processed sucessfully for %s \n" % basename
          monitor('RX5day indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if SD == True and var == "prsn" :
          logger.debug('calculation for SD started ')
          SD_file = None
          calc_icclim = [{'func':'icclim_SD','name':'SD'}]
          SD_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('prsn_','SD_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SD calculated ' )
          outlog = outlog + "SD indice processed sucessfully for %s \n" % basename
          monitor('SD indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if SD1 == True and var == "prsn" :
          logger.debug('calculation for SD1 started ')
          SD1_file = None
          calc_icclim = [{'func':'icclim_SD1','name':'SD1'}]
          SD1_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('prsn_','SD1_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SD1 calculated ' )
          outlog = outlog + "SD1 indice processed sucessfully for %s \n" % basename
          monitor('SD1 indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))
            
        if SD5cm == True and var == "prsn" :
          logger.debug('calculation for SD5cm started ')
          SD5cm_file = None
          calc_icclim = [{'func':'icclim_SD5cm','name':'SD5cm'}]
          SD5cm_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('prsn_','SD5cm_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SD5cm calculated ' )
          outlog = outlog + "SD5cm indice processed sucessfully for %s \n" % basename
          monitor('SD5cm indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))     
                    
        if SD50cm == True and var == "prsn" :
          logger.debug('calculation for SD50cm started ')
          SD50cm_file = None
          calc_icclim = [{'func':'icclim_SD50cm','name':'SD50cm'}]
          SD5cm_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('prsn_','SD50cm_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('SD50cm calculated ' )
          outlog = outlog + "SD50cm indice processed sucessfully for %s \n" % basename
          monitor('SD50cm indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))

        if CDD == True and var == "pr" :
          logger.debug('calculation for CDD started ')
          CDD_file = None
          calc_icclim = [{'func':'icclim_CDD','name':'CDD'}]
          SD5cm_file = ocgis.OcgOperations(dataset=rd, calc=calc_icclim, calc_grouping=calc_grouping, prefix=(basename.replace('pr_','CDD_')), output_crs=output_crs, output_format='nc', add_auxiliary_files=False).execute()
          logger.debug('CDD calculated ' )
          outlog = outlog + "CDD indice processed sucessfully for %s \n" % basename
          monitor('CDD indice processed for file %i/%i  ' % (c , len(uris)) , (100/len(uris)* c ))  
        
        logger.debug('processing done for experiment :  %s ' % basename  )    
        outlog = outlog + 'processing done for experiment:  %s \n' % basename    
      except Exception as e:
        msg = 'processing failed for file  : %s %s ' % ( basename , e)
        logger.error(msg)
        outlog = outlog + msg + '\n'
    
  outlog = outlog + "Finished the indice calculation at: %s \n" % (datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y'))
  return outlog;

def cv_creator(icclim, polygons, domain, anomalies, monitor=dummy_monitor ):
  
  monitor('monitor: starting Cordex Viewer preparation ' , 6)
  
  outlog = "Starting the Cordex Viwer preparation at : %s \n" % (datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y'))
  outlog = outlog + "Domain = %s \n" % (domain)
  outlog = outlog + "anomalies = %s \n" % (anomalies)
  
  from ocgis.util.shp_process import ShpProcess
  from ocgis.util.shp_cabinet import ShpCabinetIterator
  from ocgis.util.helpers import get_sorted_uris_by_time_dimension
  import shutil
  
  from cdo import Cdo   
  cdo = Cdo()
  try: 
    logger.debug('starting cv_creator')
    # preparing the working directory 
    ocgis.env.OVERWRITE = True
    ocgis.env.DIR_DATA = icclim
    #ocgis.env.DIR_OUTPUT = polygons    
    output_crs = None
    
    p_dir, p = os.path.split(os.path.abspath(__file__)) 
    SHP_DIR = config.shapefiles_dir()
    logger.debug('SHP_DIR: %s' % SHP_DIR )
    europa = ['AUT','BEL','BGR','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA','GBR','GRC','HUN','HRV','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK','SVN','SWE','NOR','CHE','ISL','MKD','MNE','SRB','MDA','UKR','BIH','ALB','BLR','KOS']
    geoms = '50m_country' # 'world_countries_boundary_file_world_2002'
    ocgis.env.DIR_SHPCABINET = SHP_DIR 
    ocgis.env.OVERWRITE = True
    sc = ocgis.ShpCabinet()
    sci = ShpCabinetIterator(geoms)

    # ref_time = [datetime(1971,01,01),datetime(2000,12,31)]
    ncs = [os.path.join(icclim, f) for f in os.listdir(icclim)]
    
    if any("_rcp" in nc for nc in ncs):
      exp = fn_sorter_ch(ncs) # dictionary with experiment : files
      outlog = outlog + ('dictionary build with %i concatinated experiments of %i files.\n'% (len(exp.keys()), len(ncs)))
    else:
      exp = fn_sorter(ncs) # dictionary with experiment : files
      outlog = outlog + ('dictionary build with %i seperate experiments of %i files.\n'% (len(exp.keys()), len(ncs)))
  except Exception as e:
    msg = 'Clipping preparation failed for : %s %s ' % ( domain , e)
    logger.error(msg)
    outlog = outlog + msg + '\n'
  
  aggregation = ['yr','DJF','MAM','JJA','SON']
  c = 0  
  for key in exp.keys():
    try:
      c = c + 1
      nc = exp[key]
      ncs = get_sorted_uris_by_time_dimension(nc)
      # ncs.sort()
      var = key.split('_')[0]
      scenario = key.split('_')[3]
      rd = RequestDataset(ncs, var) # 
      time_range=[datetime(1971,01,01) , datetime(2000,12,31)]
      
    except Exception as e:
      msg = 'sorting preparation failed for : %s %s ' % ( key , e)
      logger.error(msg)
      outlog = outlog + msg + '\n'
    
    for land in europa:
      try:
        select_ugid = []
        geom_rows = []
        for row in sci:
          if row['properties']['adm0_a3'] == land:
            select_ugid.append(row['properties']['UGID'])
            geom_rows.append(row)
          
        if not os.path.exists(os.path.join(os.curdir + '/anomalies/', var, scenario, land)):
          os.makedirs(os.path.join(os.curdir + '/anomalies/', var, scenario, land))
        OUT_DIR = os.path.join(os.curdir + '/anomalies/', var, scenario, land)
        
        #dir_output = tempfile.mkdtemp()
        ocgis.env.DIR_OUTPUT = OUT_DIR
        
        if var == 'RR' or var == 'R20mm' or var == 'SU' or var ==  'ID': # CDD  CSU  TX  TXx
          calc = [{'func':'sum', 'name':var}] 
        elif var == 'TXx' or var == 'RX5day':
          calc = [{'func':'max', 'name':var}] 
        else :
          calc = [{'func':'mean', 'name':var}] 
        
        for agg in aggregation: 
          try: 
            logger.debug('processing of %s %s %s ' % (var, land, agg))
            calc_grouping= []
            prefix = []
            
            if agg == 'yr':
              calc_grouping= ['year']        
              prefix = key.replace('EUR',land).replace('_mon','_yr').strip('.nc')
              # dir_output = tempfile.mkdtemp()
            elif agg == 'DJF':
              calc_grouping = [[12,1,2] ,'unique']
              prefix = key.replace('EUR',land).replace('_mon','_DJF').strip('.nc')
            elif agg == 'MAM':
              calc_grouping = [[3,4,5],'unique']
              prefix = key.replace('EUR',land).replace('_mon','_MAM').strip('.nc')
            elif agg == 'JJA':
              calc_grouping = [[6,7,8] ,'unique']
              prefix = key.replace('EUR',land).replace('_mon','_JJA').strip('.nc')
            elif agg == 'SON':
              calc_grouping = [[9,10,11] ,'unique']
              prefix = key.replace('EUR',land).replace('_mon','_SON').strip('.nc')
            else: 
             logger.error('no aggregation found')
             
            result =  '%s/%s.nc' % (OUT_DIR, prefix )
            
            tmp_dir = tempfile.mkdtemp(dir='.')
            p1, tmp1 = tempfile.mkstemp(dir='tmp_dir')
            path1, temp_nc = os.path.split(tmp1)
            
            p2, tmp2 = tempfile.mkstemp(dir='tmp_dir')
            path2, temp_ref = os.path.split(tmp2)
            
            try:
              monitor('Clipping %i/%i for polygon: %s' % (c, len( exp.keys()), land) , (100/len( exp.keys() ) * c ))
              geom_ref = ocgis.OcgOperations(dataset=rd,  dir_output=path2, calc=calc, calc_grouping=calc_grouping, output_format='nc', geom=geoms, select_ugid=select_ugid, prefix=temp_ref, add_auxiliary_files=False, time_range=time_range  ).execute()
              
              geom_nc = ocgis.OcgOperations(dataset=rd,  dir_output=path1, calc=calc, calc_grouping=calc_grouping, output_format='nc', geom=geoms, select_ugid=select_ugid, prefix=temp_nc, add_auxiliary_files=False ).execute()
              clipping = True
              outlog = outlog + ('calculation of polygon %s with variable %s ... done \n'% (prefix , var))
              
            except Exception as e:
              clipping = False
              os.close( p1 )
              os.close( p2 )
              shutil.rmtree(tmp_dir) # os.rmdir(tmp_dir)
              msg = 'clipping failed for :%s %s %s ' % (land, agg,  e)
              logger.error(msg)
              outlog = outlog + ('calculation of polygon %s with variable %s ... Failed \n'% (prefix , var))
              
            if clipping == True:
              monitor('Anomalie %i/%i for polygon: %s' % (c, len( exp.keys()), land) , (100/len( exp.keys() ) * c ))
              p3, tmp3 =  tempfile.mkstemp(dir=tmp_dir, suffix='.nc') 
              p4, tmp4 =  tempfile.mkstemp(dir=tmp_dir, suffix='.nc')
              p5, tmp5 =  tempfile.mkstemp(dir=tmp_dir, suffix='.nc')
              
              input1 = '%s' % (geom_nc)
              input2 = '%s' % (geom_ref)
              input3 = ' %s %s ' % (tmp3 , tmp5)
              
              # print result , tmp1 , tmp2 , tmp3  

              cdo.fldmean (input = input1 , output = tmp3)
              
              cdo.timmean (input = input2 , output = tmp4 )
              cdo.fldmean (input = tmp4 , output = tmp5 )
              
              # print input3 , result
            
              cdo.sub(input = input3 , output = result)
              logger.debug( 'done for: %s ' % ( agg ))
              
              try: 
                os.close( p1 )
                os.close( p2 )
                os.close( p3 )
                os.close( p4 )
                os.close( p5 )
              except Exception as e:
                msg = 'failed to close file %s ' % (e)
                logger.error( msg )              
              shutil.rmtree(tmp_dir) # os.rmdir(tmp_dir)
              logger.debug('calculation of file %s with variable %s in %s ... done'% (prefix,var, land)) 
          except Exception as e:
            msg = 'aggregation failed for :%s %s %s ' % (land, agg,  e)
            logger.error(msg)
      except Exception as e:
        msg = 'processing failed for file  : %s %s ' % ( prefix , e)
        logger.error(msg)
        outlog = outlog + ('failed for polygon %s ! %s ... failed !!! \n'% (prefix , e))
  outlog = outlog + "Finish the Cordex Viwer preparation at : %s \n" % (datetime.strftime(datetime.now(), '%H:%M:%S %d-%m-%Y'))
  return outlog;