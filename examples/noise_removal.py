#!/usr/bin/env python3
"""
Example: Multi-Stage Noise Removal
=====================================
Chains a moving average pre-filter with an FIR low-pass for
aggressive noise suppression on a noisy sensor signal.

Usage:
    python examples/noise_removal.py
"""

import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.moving_average import MovingAverageFilter
from src.fir_filter import FIRFilter
from src.filter_chain import FilterChain
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_sine, generate_noise, snr_db


def main():
    print("=" * 60)
    print("  Multi-Stage Noise Removal Demo")
    print("=" * 60)

    # Create a clean signal + heavy noise
    clean = generate_sine(freq=0.03, num_samples=1024, amplitude=0.6)
    noise = generate_noise(num_samples=1024, amplitude=0.4)
    noisy = np.clip(clean + noise, -32767, 32767).astype(int)

    print(f"\n[1] Input SNR: {snr_db(clean, noisy):.1f} dB")

    # Stage 1: Moving average (window=8)
    ma = MovingAverageFilter(data_width=16, window_log2=3)

    # Stage 2: FIR low-pass (cutoff = 0.15)
    coeffs = CoefficientGenerator.lowpass(num_taps=16, cutoff_freq=0.15)
    fir = FIRFilter(data_width=16, num_taps=16, coefficients=coeffs)

    # Chain them
    chain = FilterChain([ma, fir])
    chain.describe()

    print("\n[2] Running filter chain simulation...")
    result = chain.simulate(input_signal=noisy, num_samples=1024)

    # Measure improvement
    output = result['output']
    min_len = min(len(clean), len(output))
    output_snr = snr_db(clean[:min_len], output[:min_len])
    print(f"\n[3] Output SNR: {output_snr:.1f} dB")
    print(f"    Improvement: {output_snr - snr_db(clean, noisy):.1f} dB")

    # Stage-by-stage analysis
    print("\n[4] Stage-by-stage analysis:")
    for i, intermediate in enumerate(result['intermediate']):
        min_l = min(len(clean), len(intermediate))
        stage_snr = snr_db(clean[:min_l], intermediate[:min_l])
        print(f"    After stage {i+1}: SNR = {stage_snr:.1f} dB")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
