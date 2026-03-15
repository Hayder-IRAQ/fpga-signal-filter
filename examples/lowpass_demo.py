#!/usr/bin/env python3
"""
Example: Low-Pass FIR Filter
==============================
Demonstrates designing and simulating a 16-tap low-pass filter
that removes high-frequency noise from a signal.

Usage:
    python examples/lowpass_demo.py
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fir_filter import FIRFilter
from src.coefficient_gen import CoefficientGenerator
from src.utils import generate_mixed_signal, compute_fft, snr_db


def main():
    print("=" * 60)
    print("  FPGA Low-Pass FIR Filter Demo")
    print("=" * 60)

    # --- Step 1: Design filter coefficients ---
    print("\n[1] Designing 16-tap low-pass filter (cutoff = 0.2 × Nyquist)...")
    coeffs = CoefficientGenerator.lowpass(
        num_taps=16,
        cutoff_freq=0.2,
        bit_width=16,
        window='hamming'
    )
    print(f"    Coefficients: {coeffs}")

    # --- Step 2: Create filter instance ---
    fir = FIRFilter(
        data_width=16,
        coeff_width=16,
        num_taps=16,
        coefficients=coeffs
    )
    print(f"\n[2] Filter created: {fir}")

    # --- Step 3: Generate test signal ---
    print("\n[3] Generating test signal:")
    print("    - Low-freq component: 0.05 × Fs")
    print("    - High-freq noise:    0.40 × Fs")
    print("    - Gaussian noise:     10%")

    signal = generate_mixed_signal(
        freqs=[0.05, 0.40],
        amplitudes=[0.5, 0.3],
        num_samples=512,
        noise_level=0.1
    )

    # --- Step 4: Simulate ---
    print("\n[4] Running simulation (512 samples)...")
    result = fir.simulate(input_signal=signal, num_samples=512)

    # --- Step 5: Analyze results ---
    print("\n[5] Results:")
    input_rms = np.sqrt(np.mean(result['input'].astype(float) ** 2))
    output_rms = np.sqrt(np.mean(result['output'].astype(float) ** 2))
    print(f"    Input  RMS: {input_rms:.1f}")
    print(f"    Output RMS: {output_rms:.1f}")

    # Frequency response
    resp = CoefficientGenerator.frequency_response(coeffs)
    passband_ripple = np.max(resp['magnitude_db'][:50]) - np.min(resp['magnitude_db'][:50])
    stopband_atten = np.min(resp['magnitude_db'][150:])
    print(f"    Passband ripple:    {passband_ripple:.1f} dB")
    print(f"    Stopband attenuation: {stopband_atten:.1f} dB")

    # --- Step 6: HDL export info ---
    print("\n[6] To export Verilog/VHDL:")
    print("    fir.to_verilog('output/fir_lowpass.v')")
    print("    fir.to_vhdl('output/fir_lowpass.vhd')")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
