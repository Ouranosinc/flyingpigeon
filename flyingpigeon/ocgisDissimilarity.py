import dissimilarity as dd
import numpy as np
from ocgis.util.helpers import iter_array
from ocgis.calc.base import AbstractParameterizedFunction, AbstractFieldFunction
from ocgis.collection.field import OcgField
from ocgis.constants import TagNames, DimensionMapKeys, HeaderNames


# NOTE: This code builds on ocgis branch v-2.0.0.dev1
class Dissimilarity(AbstractFieldFunction, AbstractParameterizedFunction):
    """
    OCGIS class to compute a dissimilarity metric between two
    distributions.
    """
    key = 'dissimilarity'
    long_name = 'Dissimilarity metric comparing two samples'
    standard_name = 'dissimilarity_metric'
    description = 'Metric evaluating the dissimilarity between two ' \
                  'multivariate samples'
    parms_definition = {'algo': str, 'reference': OcgField, 'candidate':tuple}
    required_variables = ['candidate', 'reference']
    _potential_algo = dd.__all__

    def calculate(self, reference=None, candidate=None, algo='seuclidean'):
        """

        Parameters
        ----------
        reference : OgcField
            The reference distribution the different candidates are compared
            to.
        candidate : tuple
            Sequence of variable names identifying climate indices on which
            the comparison will be performed.
        algo : {'seuclidean', 'nearest_neighbor', 'zech_aslan',
           'kolmogorov_smirnov', 'friedman_rafsky', 'kldiv'}
            Name of the dissimilarity metric.
        """
        assert (algo in self._potential_algo)

        # Get the function from the module.
        metric = getattr(dd, algo)

        # Build the (n,d) array for the reference sample.
        ref = np.array([reference[c].get_value() for c in
                        candidate]).squeeze().T
        assert ref.ndim == 2

        # Create the fill variable based on the first candidate variable.
        variable = self.field[candidate[0]]
        crosswalk = self._get_dimension_crosswalk_(variable)
        time_axis = crosswalk.index(DimensionMapKeys.TIME)
        fill_dimensions = list(variable.dimensions)
        fill_dimensions.pop(time_axis)
        fill = self.get_fill_variable(variable,
                        'dissimilarity_' + algo, fill_dimensions,
                        self.file_only,
                        add_repeat_record_archetype_name=True)

        # ================== #
        # Metric computation #
        # ================== #

        # Iterator over every dimension except time
        itr = iter_array(fill)

        arr = self.get_variable_value(fill)
        for ind in itr:

            # Build reference array
            dind = list(ind)
            dind.insert(time_axis, slice(None))
            data = np.array([self.field[c][dind].get_value() for c in
                             candidate])
            p = np.ma.masked_invalid(data).squeeze().T

            # Compress masked values from reference array.
            pc = p.compress(~p.mask.any(1), 0)

            # Compute the actual metric value. The 5 value threshold is
            # arbitrary.
            if pc.shape[0] > 5:
                arr.data[ind] = metric(ref, pc)
            else:
                arr.data[ind] = np.nan

        # Add the output variable to calculations variable collection. This
        # is what is returned by the execute() call.
        self.vc.add_variable(fill)
