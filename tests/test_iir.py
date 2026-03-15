"""
Test Suite — IIR Filter
========================
"""

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.iir_filter import IIRFilter
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_sine, generate_mixed_signal


class TestIIRFilterCreation:

    def test_default_creation(self):
        iir = IIRFilter()
        assert iir.data_width == 16
        assert len(iir.b_coeffs) == 3
        assert len(iir.a_coeffs) == 2

    def test_custom_creation(self):
        b, a = CoefficientGenerator.iir_lowpass(cutoff_freq=0.2)
        iir = IIRFilter(b_coeffs=b, a_coeffs=a)
        assert iir.b_coeffs == b
        assert iir.a_coeffs == a

    def test_repr(self):
        iir = IIRFilter()
        assert "IIRFilter" in repr(iir)


class TestIIRFilterBehavior:

    def test_zero_input(self):
        iir = IIRFilter()
        zeros = np.zeros(64, dtype=int)
        result = iir.simulate(input_signal=zeros, num_samples=64)
        assert np.all(result['output'] == 0)

    def test_lowpass_filtering(self):
        b, a = CoefficientGenerator.iir_lowpass(cutoff_freq=0.15, q_factor=0.707)
        iir = IIRFilter(b_coeffs=b, a_coeffs=a)

        signal = generate_mixed_signal(
            freqs=[0.03, 0.45], amplitudes=[0.4, 0.4], num_samples=512
        )
        result = iir.simulate(input_signal=signal, num_samples=512)
        assert result['output'] is not None
        assert len(result['output']) > 0

    def test_stability(self):
        """Filter should not produce unbounded output."""
        b, a = CoefficientGenerator.iir_lowpass(cutoff_freq=0.2)
        iir = IIRFilter(b_coeffs=b, a_coeffs=a)

        signal = generate_sine(freq=0.1, num_samples=1024)
        result = iir.simulate(input_signal=signal, num_samples=1024)

        max_val = (1 << (iir.data_width - 1)) - 1
        assert np.all(np.abs(result['output']) <= max_val), \
            "IIR filter output exceeded bounds — possible instability"


class TestIIRCoefficients:

    def test_lowpass_coefficients(self):
        b, a = CoefficientGenerator.iir_lowpass(cutoff_freq=0.2)
        assert len(b) == 3
        assert len(a) == 2

    def test_highpass_coefficients(self):
        b, a = CoefficientGenerator.iir_highpass(cutoff_freq=0.3)
        assert len(b) == 3
        assert len(a) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
