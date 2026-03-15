"""
Filter Chain — Multi-Stage Filter Pipeline
============================================
Chain multiple filter modules sequentially for complex filter responses.
"""

import numpy as np


class FilterChain:
    """
    Chain multiple filters in series.

    Parameters
    ----------
    filters : list
        Ordered list of filter instances (FIR, IIR, MovingAverage, etc.).

    Example
    -------
    >>> chain = FilterChain([
    ...     MovingAverageFilter(data_width=16, window_log2=3),
    ...     FIRFilter(data_width=16, num_taps=8, coefficients=coeffs),
    ... ])
    >>> result = chain.simulate(num_samples=512)
    """

    def __init__(self, filters=None):
        self.filters = filters or []

    def add(self, filter_instance):
        """Add a filter stage to the chain."""
        self.filters.append(filter_instance)
        return self

    def simulate(self, input_signal=None, num_samples=256):
        """
        Simulate the entire filter chain.

        Each filter's output becomes the next filter's input.
        """
        if not self.filters:
            raise ValueError("Filter chain is empty. Add filters with .add()")

        # Get initial signal from first filter's simulation
        result = self.filters[0].simulate(
            input_signal=input_signal, num_samples=num_samples
        )
        original_input = result['input']
        intermediate_outputs = [result['output']]

        # Chain through remaining filters
        for filt in self.filters[1:]:
            prev_output = intermediate_outputs[-1]
            result = filt.simulate(
                input_signal=prev_output, num_samples=len(prev_output)
            )
            intermediate_outputs.append(result['output'])

        return {
            'input': original_input,
            'output': intermediate_outputs[-1],
            'intermediate': intermediate_outputs,
            'time': np.arange(len(intermediate_outputs[-1])),
            'stages': len(self.filters)
        }

    def describe(self):
        """Print a summary of the filter chain."""
        print(f"Filter Chain — {len(self.filters)} stages")
        print("=" * 50)
        for i, f in enumerate(self.filters):
            print(f"  Stage {i + 1}: {repr(f)}")
        print("=" * 50)

    def __repr__(self):
        return f"FilterChain(stages={len(self.filters)})"

    def __len__(self):
        return len(self.filters)
