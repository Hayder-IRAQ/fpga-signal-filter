"""
Integration Tests — Filter Chain & End-to-End
===============================================
"""

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fir_filter import FIRFilter
from src.iir_filter import IIRFilter
from src.moving_average import MovingAverageFilter
from src.filter_chain import FilterChain
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_mixed_signal


class TestFilterChain:

    def test_two_stage_chain(self):
        ma = MovingAverageFilter(window_log2=3)
        coeffs = CoefficientGenerator.lowpass(num_taps=8, cutoff_freq=0.3)
        fir = FIRFilter(num_taps=8, coefficients=coeffs)

        chain = FilterChain([ma, fir])
        result = chain.simulate(num_samples=256)

        assert result['output'] is not None
        assert result['stages'] == 2
        assert len(result['intermediate']) == 2

    def test_empty_chain_raises(self):
        chain = FilterChain()
        with pytest.raises(ValueError):
            chain.simulate()

    def test_add_method(self):
        chain = FilterChain()
        chain.add(MovingAverageFilter(window_log2=2))
        chain.add(MovingAverageFilter(window_log2=3))
        assert len(chain) == 2

    def test_chain_describe(self, capsys):
        chain = FilterChain([
            MovingAverageFilter(window_log2=3),
            FIRFilter(num_taps=8),
        ])
        chain.describe()
        captured = capsys.readouterr()
        assert "Stage 1" in captured.out
        assert "Stage 2" in captured.out


class TestEndToEnd:

    def test_full_workflow(self):
        """Test the complete design → simulate → analyze workflow."""
        # 1. Design coefficients
        coeffs = CoefficientGenerator.lowpass(
            num_taps=16, cutoff_freq=0.2, bit_width=16
        )

        # 2. Create filter
        fir = FIRFilter(data_width=16, num_taps=16, coefficients=coeffs)

        # 3. Generate test signal
        signal = generate_mixed_signal(
            freqs=[0.05, 0.15, 0.35, 0.45],
            amplitudes=[0.3, 0.2, 0.2, 0.3],
            num_samples=512
        )

        # 4. Simulate
        result = fir.simulate(input_signal=signal, num_samples=512)
        assert result['output'] is not None

        # 5. Verify frequency response
        resp = CoefficientGenerator.frequency_response(coeffs)
        assert resp['magnitude_db'] is not None

    def test_coefficient_types(self):
        """Ensure all coefficient generators return proper int lists."""
        lp = CoefficientGenerator.lowpass(num_taps=8)
        hp = CoefficientGenerator.highpass(num_taps=8)
        bp = CoefficientGenerator.bandpass(num_taps=16)
        bs = CoefficientGenerator.bandstop(num_taps=16)

        for coeffs in [lp, hp, bp, bs]:
            assert all(isinstance(c, (int, np.integer)) for c in coeffs)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
