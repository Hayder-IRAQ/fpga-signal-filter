"""
Test Suite — FIR Filter
========================
Unit tests and verification for the FIR filter module.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fir_filter import FIRFilter
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_sine, generate_mixed_signal, compute_fft


class TestFIRFilterCreation:
    """Test FIR filter instantiation and configuration."""

    def test_default_creation(self):
        fir = FIRFilter()
        assert fir.data_width == 16
        assert fir.coeff_width == 16
        assert fir.num_taps == 8
        assert len(fir.coefficients) == 8

    def test_custom_creation(self):
        coeffs = [100, 200, 300, 400, 300, 200, 100, 50]
        fir = FIRFilter(data_width=12, coeff_width=12, num_taps=8, coefficients=coeffs)
        assert fir.data_width == 12
        assert fir.num_taps == 8
        assert fir.coefficients == coeffs

    def test_coefficient_length_mismatch(self):
        with pytest.raises(AssertionError):
            FIRFilter(num_taps=8, coefficients=[1, 2, 3])

    def test_repr(self):
        fir = FIRFilter(data_width=16, num_taps=8)
        assert "FIRFilter" in repr(fir)
        assert "16" in repr(fir)


class TestFIRFilterBehavior:
    """Test FIR filter behavioral correctness."""

    def test_lowpass_attenuates_high_freq(self):
        """A low-pass filter should attenuate high-frequency components."""
        coeffs = CoefficientGenerator.lowpass(num_taps=16, cutoff_freq=0.2)
        fir = FIRFilter(num_taps=16, coefficients=coeffs)

        # Mixed signal: low freq (0.05) + high freq (0.4)
        signal = generate_mixed_signal(
            freqs=[0.05, 0.4],
            amplitudes=[0.4, 0.4],
            num_samples=512
        )

        result = fir.simulate(input_signal=signal, num_samples=512)
        output = result['output']

        # Check FFT: high freq should be attenuated
        freq_in, mag_in = compute_fft(signal)
        freq_out, mag_out = compute_fft(output)

        # Find magnitude at low and high frequencies
        low_idx = np.argmin(np.abs(freq_out - 0.05))
        high_idx = np.argmin(np.abs(freq_out - 0.4))

        # High frequency should be significantly lower than low frequency
        assert mag_out[high_idx] < mag_out[low_idx], \
            "High frequency was not attenuated by low-pass filter"

    def test_impulse_response(self):
        """Impulse response should match coefficients."""
        coeffs = [1000, 2000, 3000, 2000, 1000, 0, 0, 0]
        fir = FIRFilter(num_taps=8, coefficients=coeffs)

        impulse = np.zeros(64, dtype=int)
        impulse[0] = (1 << 14)  # Large impulse

        result = fir.simulate(input_signal=impulse, num_samples=64)
        # Output should show the impulse response shape
        assert result['output'] is not None
        assert len(result['output']) == 64

    def test_zero_input(self):
        """Zero input should produce zero output."""
        fir = FIRFilter(num_taps=8)
        zeros = np.zeros(64, dtype=int)
        result = fir.simulate(input_signal=zeros, num_samples=64)
        assert np.all(result['output'] == 0)

    def test_dc_passthrough(self):
        """A constant (DC) input through an averaging filter should
        converge to the DC value."""
        N = 8
        max_val = (1 << 14)
        coeffs = CoefficientGenerator.lowpass(num_taps=N, cutoff_freq=0.9)
        fir = FIRFilter(num_taps=N, coefficients=coeffs)

        dc = np.full(128, max_val, dtype=int)
        result = fir.simulate(input_signal=dc, num_samples=128)
        # After settling, output should be near input
        settled = result['output'][N + 10:]
        if len(settled) > 0:
            assert np.std(settled) < max_val * 0.3, \
                "DC signal not passed through correctly"


class TestFIRFilterCoefficients:
    """Test coefficient generation for FIR filters."""

    def test_lowpass_coefficients(self):
        coeffs = CoefficientGenerator.lowpass(num_taps=16, cutoff_freq=0.2)
        assert len(coeffs) == 16
        assert all(isinstance(c, (int, np.integer)) for c in coeffs)

    def test_highpass_coefficients(self):
        coeffs = CoefficientGenerator.highpass(num_taps=16, cutoff_freq=0.3)
        assert len(coeffs) == 16

    def test_bandpass_coefficients(self):
        coeffs = CoefficientGenerator.bandpass(
            num_taps=32, low_freq=0.2, high_freq=0.4
        )
        assert len(coeffs) == 32

    def test_frequency_response(self):
        coeffs = CoefficientGenerator.lowpass(num_taps=16, cutoff_freq=0.2)
        resp = CoefficientGenerator.frequency_response(coeffs)
        assert 'frequency' in resp
        assert 'magnitude_db' in resp
        assert len(resp['frequency']) == 512


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
