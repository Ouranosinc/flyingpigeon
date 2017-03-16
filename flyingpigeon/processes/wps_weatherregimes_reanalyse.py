"""
Processes for Weather Classification
Author: Nils Hempelmann (nils.hempelmann@lsce.ipsl.fr)
"""

from flyingpigeon.datafetch import _PRESSUREDATA_
from flyingpigeon.weatherregimes import _TIMEREGIONS_
from pywps.Process import WPSProcess

from flyingpigeon.log import init_process_logger

# from datetime import  date

import logging
logger = logging.getLogger(__name__)


class WeatherRegimesRProcess(WPSProcess):
    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="weatherregimes_reanalyse",
            title="Weather Regimes -- Reanalyses data",
            version="0.9",
            metadata=[
                {"title": "LSCE", "href": "http://www.lsce.ipsl.fr/en/index.php"},
                {"title": "Documentation", "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
                ],
            abstract="Weather Regimes based on pressure patterns, fetching selected Realayses Datasets",
            statusSupported=True,
            storeSupported=True
            )

        # Literal Input Data
        # ------------------
        self.BBox = self.addBBoxInput(
            identifier="BBox",
            title="Bounding Box",
            abstract="coordinates to define the region for weather classification ('EPSG:4326')",
            minOccurs=1,
            maxOccurs=1,
            crss=['EPSG:4326']
            )

        # self.BBox = self.addLiteralInput(
        #     identifier="BBox",
        #     title="Region",
        #     abstract="coordinates to define the region: (minlon,maxlon,minlat,maxlat)",
        #     default='-80,22.5,50,70', #  cdo syntax: 'minlon,maxlon,minlat,maxlat' ;\
        #  ocgis syntax (minlon,minlat,maxlon,maxlat)
        #     type=type(''),
        #     minOccurs=1,
        #     maxOccurs=1,
        #     )

        self.season = self.addLiteralInput(
            identifier="season",
            title="Time region",
            abstract="Select the months to define the time region (all == whole year will be analysed)",
            default="DJF",
            type=type(''),
            minOccurs=1,
            maxOccurs=1,
            allowedValues=_TIMEREGIONS_.keys()
            )

        self.period = self.addLiteralInput(
            identifier="period",
            title="Period for weatherregime calculation",
            abstract="Period for analysing the dataset",
            default="19700101-20101231",
            type=type(''),
            minOccurs=1,
            maxOccurs=1,
            )

        self.anualcycle = self.addLiteralInput(
            identifier="anualcycle",
            title="Period for anualcycle calculation",
            abstract="Period for anual cycle calculation",
            default="19700101-19991231",
            type=type(''),
            minOccurs=1,
            maxOccurs=1,
            )

        self.reanalyses = self.addLiteralInput(
            identifier="reanalyses",
            title="Reanalyses Data",
            abstract="Choose a reanalyses dataset for comparison",
            default="NCEP_slp",
            type=type(''),
            minOccurs=1,
            maxOccurs=1,
            allowedValues=_PRESSUREDATA_
            )

        self.kappa = self.addLiteralInput(
            identifier="kappa",
            title="Nr of Weather regimes",
            abstract="Set the number of clusters to be detected",
            default=4,
            type=type(1),
            minOccurs=1,
            maxOccurs=1,
            allowedValues=range(2, 11)
            )

        ######################
        # define the outputs
        ######################

        self.Routput_graphic = self.addComplexOutput(
            identifier="Routput_graphic",
            title="Weather Regime Pressure map",
            abstract="Weather Classification",
            formats=[{"mimeType": "image/pdf"}],
            asReference=True,
            )

        self.output_pca = self.addComplexOutput(
            identifier="output_pca",
            title="R - datafile",
            abstract="Principal components (PCA)",
            formats=[{"mimeType": "text/plain"}],
            asReference=True,
            )

        self.output_classification = self.addComplexOutput(
            identifier="output_classification",
            title="R - workspace",
            abstract="Weather regime classification",
            formats=[{"mimeType": "application/octet-stream"}],
            asReference=True,
            )

        self.output_netcdf = self.addComplexOutput(
            identifier="output_netcdf",
            title="netCDF reference",
            abstract="Prepared netCDF file as input for weatherregime calculation",
            formats=[{"mimeType": "application/x-netcdf"}],
            asReference=True,
            )

        self.output_log = self.addComplexOutput(
            identifier="output_log",
            title="Logging information",
            abstract="Collected logs during process run.",
            formats=[{"mimeType": "text/plain"}],
            asReference=True,
        )

    def execute(self):

        init_process_logger('log.txt')
        self.output_log.setValue('log.txt')

        logger.info('Start process')
        from datetime import datetime as dt
        from flyingpigeon import weatherregimes as wr
        from tempfile import mkstemp

        self.status.set('execution started at : %s ' % dt.now(), 5)

        ################################
        # reading in the input arguments
        ################################
        try:
            logger.info('read in the arguments')
            # resources = self.getInputValues(identifier='resources')
            season = self.getInputValues(identifier='season')[0]
            bbox_obj = self.BBox.getValue()
            model_var = self.getInputValues(identifier='reanalyses')[0]
            period = self.getInputValues(identifier='period')[0]
            anualcycle = self.getInputValues(identifier='anualcycle')[0]
            model, variable = model_var.split('_')

            kappa = int(self.getInputValues(identifier='kappa')[0])
            logger.info('period %s' % str(period))
            logger.info('season %s' % str(season))
        except Exception as e:
            logger.debug('failed to read in the arguments %s ' % e)

        try:
            start = dt.strptime(period.split('-')[0], '%Y%m%d')
            end = dt.strptime(period.split('-')[1], '%Y%m%d')

            if bbox_obj is not None:
                logger.info("bbox_obj={0}".format(bbox_obj.coords))
                bbox = [bbox_obj.coords[0][0], bbox_obj.coords[0][1], bbox_obj.coords[1][0], bbox_obj.coords[1][1]]
                logger.info("bbox={0}".format(bbox))
            else:
                bbox = None

        except Exception as e:
            logger.debug('failed to transform BBOXObject  %s ' % e)

        ###########################
        # set the environment
        ###########################

        self.status.set('fetching data from archive', 10)

        try:
            if model == 'NCEP':
                if 'z' in variable:
                    level = variable.strip('z')
                    conform_units_to = None
                else:
                    level = None
                    conform_units_to = 'hPa'
            elif '20CRV2' in model:
                if 'z' in variable:
                    level = variable.strip('z')
                    conform_units_to = None
                else:
                    level = None
                    conform_units_to = 'hPa'
            else:
                logger.error('Reanalyses dataset not known')
            logger.info('environment set')
        except Exception as e:
            msg = 'failed to set environment %s ' % e
            logger.error(msg)
            raise Exception(msg)

        ##########################################
        # fetch Data from original data archive
        ##########################################

        from flyingpigeon.datafetch import reanalyses as rl
        try:
            model_nc = rl(start=start.year,
                          end=end.year,
                          dataset=model,
                          variable=variable)
            logger.info('reanalyses data fetched')
        except Exception as e:
            msg = 'failed to get reanalyses data  %s' % e
            logger.debug(msg)
            raise Exception(msg)

        self.status.set('fetching data done', 15)
        ############################################################
        # get the required bbox and time region from resource data
        ############################################################

        self.status.set('subsetting region of interest', 17)
        # from flyingpigeon.weatherregimes import get_level
        from flyingpigeon.ocgis_module import call

        time_range = [start, end]
        model_subset = call(resource=model_nc, variable=variable,
                            geom=bbox, spatial_wrapping='wrap', time_range=time_range,
                            # conform_units_to=conform_units_to
                            )
        logger.info('Dataset subset done: %s ' % model_subset)

        self.status.set('dataset subsetted', 19)
        ##############################################
        # computing anomalies
        ##############################################
        self.status.set('computing anomalies ', 19)

        cycst = anualcycle.split('-')[0]
        cycen = anualcycle.split('-')[0]
        reference = [dt.strptime(cycst, '%Y%m%d'), dt.strptime(cycen, '%Y%m%d')]
        logger.debug('reference time: %s' % reference)
        model_anomal = wr.get_anomalies(model_subset, reference=reference)

        #####################
        # extracting season
        #####################
        self.status.set('normalizing data', 21)
        model_season = wr.get_season(model_anomal, season=season)

        self.status.set('anomalies computed and  normalized', 24)
        #######################
        # call the R scripts
        #######################
        self.status.set('Start weather regime clustering ', 25)
        import shlex
        import subprocess
        from flyingpigeon import config
        from os.path import curdir, exists, join

        try:
            rworkspace = curdir
            Rsrc = config.Rsrc_dir()
            Rfile = 'weatherregimes_model.R'

            infile = model_season  # model_subset #model_ponderate
            modelname = model
            yr1 = start.year
            yr2 = end.year
            ip, output_graphics = mkstemp(dir=curdir, suffix='.pdf')
            ip, file_pca = mkstemp(dir=curdir, suffix='.txt')
            ip, file_class = mkstemp(dir=curdir, suffix='.Rdat')

            args = ['Rscript', join(Rsrc, Rfile), '%s/' % curdir,
                    '%s/' % Rsrc, '%s' % infile, '%s' % variable,
                    '%s' % output_graphics, '%s' % file_pca,
                    '%s' % file_class, '%s' % season,
                    '%s' % start.year, '%s' % end.year,
                    '%s' % model_var, '%s' % kappa]
            logger.info('Rcall builded')
        except Exception as e:
            msg = 'failed to build the R command %s' % e
            logger.debug(msg)
            raise Exception(msg)
        try:
            output, error = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            logger.info('R outlog info:\n %s ' % output)
            logger.debug('R outlog errors:\n %s ' % error)
            if len(output) > 0:
                self.status.set('**** weatherregime in R suceeded', 90)
            else:
                logger.error('NO! output returned from R call')
        except Exception as e:
            msg = 'weatherregime in R %s ' % e
            logger.error(msg)
            raise Exception(msg)

        self.status.set('Weather regime clustering done ', 80)
        ############################################
        # set the outputs
        ############################################
        self.status.set('Set the process outputs ', 95)

        self.Routput_graphic.setValue(output_graphics)
        self.output_pca.setValue(file_pca)
        self.output_classification.setValue(file_class)
        self.output_netcdf.setValue(model_season)
