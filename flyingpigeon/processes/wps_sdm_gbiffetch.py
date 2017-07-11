"""
Processes to fetch data from GBIF data base
Author: Nils Hempelmann (info@nilshempelmann.de)
"""

from pywps.Process import WPSProcess

from flyingpigeon.log import init_process_logger

import logging
logger = logging.getLogger(__name__)


class GBIFfetchProcess(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="sdm_gbiffetch",
            title="SDM -- GBIF data fetch",
            version="0.1",
            metadata=[
                {"title": "Documentation",
                 "href": "http://flyingpigeon.readthedocs.io/en/latest/"},
                {"title": "GBIF", "href": "http://gbif.org/"}
            ],
            abstract="Species occurence search in Global Biodiversity \
             Infrastructure Facillity (GBIF)",
            statusSupported=True,
            storeSupported=True
        )

        # Literal Input Data
        # ------------------

        self.taxon_name = self.addLiteralInput(
            identifier="taxon_name",
            title="Tree Species",
            abstract="Scientific name of tree species",
            type=type(''),
            minOccurs=1,
            maxOccurs=1,
            default='Fagus sylvatica'
        )

        """
        # TODO: bbox does not work
        self.BBox = self.addBBoxInput(
            identifier="BBox",
            title="Bounding Box",
            abstract="coordinates to define the region for occurence data fetch",
            minOccurs=1,
            maxOccurs=1,
            crss=['EPSG:4326']
        )
        """

        ###########
        # OUTPUTS
        ###########

        self.output_csv = self.addComplexOutput(
            identifier="output_csv",
            title="Tree species table",
            abstract="Extracted CSV file containing the tree species table ",
            formats=[{"mimeType": "text/csv"}],
            asReference=True,
        )

        self.output_map = self.addComplexOutput(
            identifier="output_map",
            title="Graphic of species occurences",
            abstract="PNG graphic file showing the presence of tree species \
            according to GBIF data fetch",
            formats=[{"mimeType": "image/png"}],
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

        self.status.set('Start process', 0)
        from flyingpigeon import sdm

        try:
            logger.info('reading the arguments')
            taxon_name = self.getInputValues(identifier='taxon_name')[0]
            # bbox_obj = self.BBox.getValue()
            # bbox = [bbox_obj.coords[0][0],
            #         bbox_obj.coords[0][1],
            #         bbox_obj.coords[1][0],
            #         bbox_obj.coords[1][1]]
            bbox = [-180, -90, 180, 90]
            logger.info("bbox={0}".format(bbox))
            logger.info("Taxon Name = %s", taxon_name)
        except Exception as e:
            msg = 'failed to read in the arguments.'
            logger.exception(msg)
            raise Exception(msg)

        try:
            self.status.set('Fetching GBIF Data', 10)
            gbifdic = sdm.get_gbif(taxon_name, bbox=bbox)
        except Exception as e:
            msg = 'failed to search gbif.'
            logger.exception(msg)
            raise Exception(msg)

        try:
            self.status.set('write csv file', 70)
            gbifcsv = sdm.gbifdic2csv(gbifdic)
        except Exception as e:
            msg = 'failed to write csv file.'
            logger.exception(msg)
            raise Exception(msg)

        try:
            self.status.set('plot map', 80)
            from flyingpigeon.visualisation import map_gbifoccurrences
            latlon = sdm.latlon_gbifdic(gbifdic)
            occurence_map = map_gbifoccurrences(latlon)
        except Exception as e:
            msg = 'failed to plot occurence map.'
            logger.exception(msg)
            raise Exception(msg)

        self.output_map.setValue(occurence_map)
        self.output_csv.setValue(gbifcsv)

        # write folder statistics:
        import shlex
        import subprocess
        import os
        import socket
        logger.debug('HOSTNAME: %s ' % socket.gethostname())

        cmd = 'stat %s/' % os.path.abspath(os.curdir)
        args = shlex.split(cmd)
        output, error = subprocess.Popen(
                        args, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                        ).communicate()

        logger.debug('temp folder statistics: %s  ERRORS: %s' % (output, error))
        self.status.set('done', 100)
