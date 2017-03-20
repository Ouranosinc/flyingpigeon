from flyingpigeon.tests.common import WpsTestClient, TESTDATA, \
    assert_response_success
import ocgis
import numpy as np
from flyingpigeon.processes import wps_spatial_analog as sa

import pytest
from ocgis.calc.base import AbstractMultivariateFunction, \
    AbstractParameterizedFunction, AbstractFieldFunction
from ocgis.test.base import TestBase, AbstractTestField
from ocgis.collection.field import OcgField
from ocgis import RequestDataset, OcgOperations, FunctionRegistry
from ocgis.variable.base import Variable
import datetime as dt
class MockMultiParamFunction(AbstractFieldFunction, AbstractMultivariateFunction, AbstractParameterizedFunction):
    key = 'mock_mpf'
    long_name = 'expand the abbreviations again'
    standard_name = 'mock_multi_param_function'
    description = 'Used for testing a multivariate, parameterized field function'
    parms_definition = {'the_exponent': int, 'offset': float}
    required_variables = ('lhs', 'rhs')

    def calculate(self, lhs=None, rhs=None, the_exponent=None, offset=None):
        # Access the variable object by name from the calculation field.
        lhs = self.field[lhs]
        rhs = self.field[rhs]

        # Dimensions similar to netCDF dimensions are available on the variables.
        assert len(lhs.dimensions) > 0
        # The get_value() call returns a numpy array. Mask is retrieved by get_mask(). You can get a masked array
        # by using get_masked_value(). These return references.
        value = (rhs.get_value() - lhs.get_value()) ** the_exponent + offset
        # Recommended that this method is used to create the output variables. Adds appropriate calculations attributes,
        # extra record information for tabular output, etc. At the very least, it is import to reuse the dimensions
        # appropriately as they contain global/local bounds for parallel IO. You can pass a masked array to
        # "variable_value".
        variable = self.get_fill_variable(lhs, self.alias, lhs.dimensions, variable_value=value)
        # Add the output variable to calculations variable collection. This is what is returned by the execute() call.
        self.vc.add_variable(variable)


class TestMockMultiParamFunction(TestBase):
    desired_value = [30.5, 37.5, 57.5]

    @property
    def field_for_test(self):
        field = OcgField(variables=[self.variable_lhs_for_test, self.variable_rhs_for_test])
        return field

    @property
    def fields_for_ops_test(self):
        field1 = OcgField(variables=self.variable_lhs_for_test)
        field2 = OcgField(variables=self.variable_rhs_for_test)
        return [field1, field2]

    @property
    def parms_for_test(self):
        return {'lhs': 'left', 'rhs': 'right', 'the_exponent': 2, 'offset': 21.5}

    @property
    def variable_lhs_for_test(self):
        return Variable(name='left', value=[4, 5, 6], dimensions='three', dtype=float)

    @property
    def variable_rhs_for_test(self):
        return Variable(name='right', value=[7, 9, 12], dimensions='three', dtype=float)

    def setUp(self):
        super(TestMockMultiParamFunction, self).setUp()
        FunctionRegistry.append(MockMultiParamFunction)

    def tearDown(self):
        super(TestMockMultiParamFunction, self).tearDown()
        FunctionRegistry.reg.pop(0)

    def test_execute(self):
        ff = MockMultiParamFunction(field=self.field_for_test, parms=self.parms_for_test)
        res = ff.execute()
        self.assertEqual(res[MockMultiParamFunction.key].get_value().tolist(), self.desired_value)

    def test_system_through_operations(self):
        calc = [{'func': MockMultiParamFunction.key, 'name': 'my_mvp', 'kwds': self.parms_for_test}]
        ops = OcgOperations(dataset=self.fields_for_ops_test, calc=calc)
        ret = ops.execute()

        actual_variable = ret.get_element(variable_name='my_mvp')
        self.assertEqual(actual_variable.get_value().tolist(), self.desired_value)

        ops = OcgOperations(dataset=self.fields_for_ops_test, calc=calc, output_format='nc')
        ret = ops.execute()
        actual = RequestDataset(ret).get()['my_mvp']
        self.assertEqual(actual.get_value().tolist(), self.desired_value)

    def test_real_dataset(self):
        indices = ['meantemp', 'totalpr']
        calc = [{'func': MockMultiParamFunction.key, 'name': 'my_mvp',
                 'kwds': {'lhs': indices[0], 'rhs': indices[1], 'the_exponent':
                     2, 'offset': 21.5}}]

        ocgis.env.DIR_DATA = '/home/david/projects/PAVICS/birdhouse/flyingpigeon/flyingpigeon/tests/testdata/spatial_analog/'
        rfn = 'reference_indicators.nc'  # TESTDATA['reference_indicators']
        crd = ocgis.RequestDataset(rfn, variable=indices)

        ops = OcgOperations(dataset=crd, calc=calc, \
                            time_range=[dt.datetime(1960, 1, 1),
                                        dt.datetime(2000, 1, 1)]
                            )
        ret = ops.execute()



#@pytest.mark.skip()
def test_dissimilarity_op():
    import json, os
    import datetime as dt

    ocgis.FunctionRegistry.append(sa.Dissimilarity)

    ocgis.env.DIR_DATA = '/home/david/projects/PAVICS/birdhouse/flyingpigeon/flyingpigeon/tests/testdata/spatial_analog/'
    rfn = 'reference_indicators.nc'  # TESTDATA['reference_indicators']
    tfn = 'target_indicators.nc'
    tfjson = 'target_indicators.json'

    indices = ['meantemp', 'totalpr']
    # Candidate fields
    crd = ocgis.RequestDataset(rfn,
                variable=indices,
                time_range=[dt.datetime(1960, 1, 1), dt.datetime(2000, 1, 1)],
                )

    # Reference fields
    rrd = ocgis.RequestDataset(tfn,
                variable=indices,
                time_range=[dt.datetime(1970, 1, 1), dt.datetime(2000, 1, 1)],
                )
    reference = rrd.get()
    #tarr = json.load(open(os.path.join(ocgis.env.DIR_DATA, tfjson)))
    #reference = np.array([tarr[ind] for ind in indices]).T

    ops = ocgis.OcgOperations(
        calc=[{'func': 'dissimilarity', 'name': 'spatial_analog',
               'kwds': {'algo': 'seuclidean', 'reference': reference,
                        'candidate': indices}}],
        geom=(-72, 46),
        time_range=[dt.datetime(1960, 1, 1), dt.datetime(2000, 1, 1)],
        dataset=crd)

    res = ops.execute()


@pytest.mark.skip()
def test_wps_spatial_analog():

    wps = WpsTestClient()

    datainputs = "[reference_nc={0};target_json={1};indices=meantemp;indices=totalpr]".format(TESTDATA['reference_indicators'], TESTDATA['target_indicators'])

    resp = wps.get(service='wps', request='execute', version='1.0.0', identifier='spatial_analog',
                   datainputs=datainputs)
    assert_response_success(resp)