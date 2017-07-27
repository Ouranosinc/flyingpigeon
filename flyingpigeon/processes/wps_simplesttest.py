from pywps import Process
from pywps import LiteralInput, LiteralOutput


# The name chosen here must also be in the "super" call, and a corresponding
# "identifier" in the "super" call.
class SimplestTest(Process):
    def __init__(self):
        inputs = [LiteralInput('one_integer',
                               'Some integer input',
                               data_type='integer')]

        outputs = [LiteralOutput('repeated_integer',
                                 'Echo of the input',
                                 data_type='integer')]

        super(SimplestTest, self).__init__(
            self._handler,
            identifier='simplesttest',
            title='Simplest Test',
            version='0.1',
            inputs=inputs,
            outputs=outputs)

    def _handler(self, request, response):
        one_integer = request.inputs['one_integer'][0].data
        response.outputs['repeated_integer'].data = one_integer
        return response
