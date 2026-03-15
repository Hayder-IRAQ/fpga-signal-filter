"""
Test Suite — Moving Average Filter
====================================
"""

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.moving_average import MovingAverageFilter
from src.utils import generate_sine, generate_noise


class TestMovingAverage:

    def test_creation(self):
        ma = MovingAverageFilter(window_log2=4)
        assert ma.window_size == 16
        assert ma.data_width == 16

    def test_noise_reduction(self):
        """Moving average should reduce noise variance."""
        ma = MovingAverageFilter(window_log2=4)
        noisy = generate_sine(freq=0.02, num_samples=512)
        noisy = noisy + generate_noise(num_samples=512, amplitude=0.3)

        result = ma.simulate(input_signal=noisy, num_samples=512)
        input_var = np.var(result['input'].astype(float))
        output_var = np.var(result['output'].astype(float))
        # Output variance should be lower
        assert output_var <= input_var

    def test_zero_input(self):
        ma = MovingAverageFilter(window_log2=3)
        zeros = np.zeros(64, dtype=int)
        result = ma.simulate(input_signal=zeros, num_samples=64)
        assert np.all(result['output'] == 0)

    def test_repr(self):
        ma = MovingAverageFilter(window_log2=5)
        assert "32" in repr(ma)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
