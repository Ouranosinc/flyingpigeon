import traceback

from urlparse import urlparse
from pywps import Process, LiteralInput, ComplexOutput, get_format
from flyingpigeon.utils import CookieNetCDFTransfer


json_format = get_format('JSON')


class BiasCorrectionProcess(Process):
    """Subset a NetCDF file using bounding box geometry."""

    def __init__(self):
        inputs = [
            LiteralInput('reference_data',
                         'NetCDF reference file',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         data_type='string',
                         max_occurs=1),
            LiteralInput('observed_data',
                         'NetCDF observed file',
                         abstract='',
                         data_type='string',
                         max_occurs=1),
            LiteralInput('future_data',
                         'NetCDF future file',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         data_type='string',
                         max_occurs=1)]

        outputs = [
        ComplexOutput('output_netcdf', 'Function output in netCDF',
                      abstract="The indicator values computed on the original input grid.",
                      as_reference=True,
                      supported_formats=[Format('application/x-netcdf')]
                      ),

        ComplexOutput('output_log', 'Logging information',
                      abstract="Collected logs during process run.",
                      as_reference=True,
                      supported_formats=[Format('text/plain')])]



        super(BiasCorrectionProcess, self).__init__(
            self._handler,
            identifier='biascorrection',
            title='BiasCorrection',
            version='0.1',
            abstract=(''),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        try:
            opendap_hostnames = [
                urlparse(r.data).hostname for r in request.inputs['resource']]
            with CookieNetCDFTransfer(request, opendap_hostnames):
                result = wfs_common(request, response, mode='subsetter',
                                    spatial_mode='bbox')
            return result
        except:
            raise Exception(traceback.format_exc())
