import traceback

from pywps import Process, ComplexInput, ComplexOutput, Format

import netCDF4

import ocgis
from ocgis import RequestDataset, OcgOperations
from flyingpigeon.utils import archiveextract, rename_complexinputs


class NCMergeProcess(Process):
    """Merge NetCDF files."""

    def __init__(self):
        inputs = [
            ComplexInput('resource',
                         'NetCDF resource',
                         abstract='NetCDF files, can be OPEnDAP urls.',
                         max_occurs=1000,
                         supported_formats=[
                             Format('application/x-netcdf'),
                             Format('application/x-tar'),
                             Format('application/zip')])]

        outputs = [
            ComplexOutput('output',
                          'Merged NetCDF files',
                          abstract='Temporally merged NetCDF files.',
                          as_reference=True,
                          supported_formats=[Format('application/x-netcdf')])]

        super(NCMergeProcess, self).__init__(
            self._handler,
            identifier='ncmerge',
            title='NetCDF merge',
            version='0.1',
            abstract=('Merge NetCDF files in the time dimension.'),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

    def _handler(self, request, response):
        try:
            ocgis.env.OVERWRITE = True
            nc_files = archiveextract(resource=rename_complexinputs(
                request.inputs['resource']))
            close_mf = False
            try:
                rd = RequestDataset(nc_files)
            except IOError:
                # Suggestion for when the time dimension is not unlimited
                mfnc = netCDF4.MFDataset(nc_files, 'r', aggdim='time')
                rd = RequestDataset(driver='nc', opened=mfnc)
                close_mf = True
            rd.dimension_map.set_bounds('time', None)
            if nc_files[0][-3:] == '.nc':
                out_prefix = nc_files[0][:-3] + '_merged'
            else:
                out_prefix = nc_files[0] + '_merged'
            ops = OcgOperations(dataset=rd, output_format='nc',
                                prefix=out_prefix)
            ret = ops.execute()
            if close_mf:
                mfnc.close()
            response.outputs['output'].file = ret
            response.outputs['output'].output_format = \
                Format('application/x-netcdf')
            return response
        except:
            raise Exception(traceback.format_exc())
