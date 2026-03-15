"""
Test Suite — CIC Filter
=========================
"""

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cic_filter import CICFilter
from src.utils import generate_sine


class TestCICFilter:

    def test_creation(self):
        cic = CICFilter(num_stages=3, decimation=8)
        assert cic.num_stages == 3
        assert cic.decimation == 8

    def test_decimation_ratio(self):
        """Output length should be ~input_length / decimation."""
        cic = CICFilter(decimation=8, num_stages=3)
        signal = generate_sine(freq=0.01, num_samples=1024)
        result = cic.simulate(input_signal=signal, num_samples=1024)
        expected_len = 1024 // 8
        assert len(result['output']) == expected_len

    def test_different_stages(self):
        for stages in [1, 2, 4]:
            cic = CICFilter(num_stages=stages, decimation=4)
            result = cic.simulate(num_samples=512)
            assert result['output'] is not None

    def test_repr(self):
        cic = CICFilter(num_stages=3, decimation=16)
        assert "16" in repr(cic)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
