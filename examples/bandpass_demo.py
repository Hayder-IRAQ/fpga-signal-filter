#!/usr/bin/env python3
"""
Example: Band-Pass FIR Filter
===============================
Extracts a specific frequency band from a multi-tone signal.

Usage:
    python examples/bandpass_demo.py
"""

import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fir_filter import FIRFilter
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_mixed_signal, compute_fft


def main():
    print("=" * 60)
    print("  FPGA Band-Pass FIR Filter Demo")
    print("=" * 60)

    # Design band-pass filter: pass 0.15–0.30 × Nyquist
    print("\n[1] Designing 32-tap band-pass filter")
    print("    Passband: 0.15 to 0.30 × Nyquist")
    coeffs = CoefficientGenerator.bandpass(
        num_taps=32, low_freq=0.15, high_freq=0.30, bit_width=16
    )

    fir = FIRFilter(data_width=16, num_taps=32, coefficients=coeffs)

    # Signal with components at 0.05, 0.20, 0.45
    print("\n[2] Test signal: tones at 0.05, 0.20, 0.45 × Fs")
    signal = generate_mixed_signal(
        freqs=[0.05, 0.20, 0.45],
        amplitudes=[0.3, 0.3, 0.3],
        num_samples=512
    )

    print("\n[3] Simulating...")
    result = fir.simulate(input_signal=signal, num_samples=512)

    # FFT analysis
    freq_in, mag_in = compute_fft(signal)
    freq_out, mag_out = compute_fft(result['output'])

    # Check that 0.20 component is preserved
    target_idx = np.argmin(np.abs(freq_out - 0.20))
    reject_idx_low = np.argmin(np.abs(freq_out - 0.05))
    reject_idx_high = np.argmin(np.abs(freq_out - 0.45))

    print(f"\n[4] Spectral analysis:")
    print(f"    0.05 Fs: {mag_out[reject_idx_low]:.1f} dB (should be low)")
    print(f"    0.20 Fs: {mag_out[target_idx]:.1f} dB (should be preserved)")
    print(f"    0.45 Fs: {mag_out[reject_idx_high]:.1f} dB (should be low)")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
