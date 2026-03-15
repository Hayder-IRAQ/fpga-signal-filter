#!/usr/bin/env python3
"""
Plot Filter Frequency Response
================================
Visualize magnitude and phase response of designed filters.

Usage:
    python scripts/plot_response.py --filter fir --taps 16 --cutoff 0.2
    python scripts/plot_response.py --filter fir --taps 32 --cutoff 0.1 --save response.png
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.coefficient_gen import CoefficientGenerator


def main():
    parser = argparse.ArgumentParser(description="Plot filter frequency response")
    parser.add_argument('--filter', choices=['lowpass', 'highpass', 'bandpass', 'bandstop'],
                        default='lowpass')
    parser.add_argument('--taps', type=int, default=16)
    parser.add_argument('--cutoff', type=float, default=0.25)
    parser.add_argument('--low-freq', type=float, default=0.2)
    parser.add_argument('--high-freq', type=float, default=0.4)
    parser.add_argument('--bit-width', type=int, default=16)
    parser.add_argument('--save', type=str, default=None,
                        help='Save plot to file (requires matplotlib)')
    args = parser.parse_args()

    # Generate coefficients
    if args.filter == 'lowpass':
        coeffs = CoefficientGenerator.lowpass(args.taps, args.cutoff, args.bit_width)
        title = f"Low-Pass FIR ({args.taps} taps, fc={args.cutoff})"
    elif args.filter == 'highpass':
        coeffs = CoefficientGenerator.highpass(args.taps, args.cutoff, args.bit_width)
        title = f"High-Pass FIR ({args.taps} taps, fc={args.cutoff})"
    elif args.filter == 'bandpass':
        coeffs = CoefficientGenerator.bandpass(args.taps, args.low_freq, args.high_freq, args.bit_width)
        title = f"Band-Pass FIR ({args.taps} taps, {args.low_freq}-{args.high_freq})"
    else:
        coeffs = CoefficientGenerator.bandstop(args.taps, args.low_freq, args.high_freq, args.bit_width)
        title = f"Band-Stop FIR ({args.taps} taps, {args.low_freq}-{args.high_freq})"

    # Compute response
    resp = CoefficientGenerator.frequency_response(coeffs, args.bit_width)

    print(f"\n{title}")
    print("=" * 50)
    print(f"  Coefficients: {coeffs}")
    print(f"  Peak magnitude:    {np.max(resp['magnitude_db']):.1f} dB")
    print(f"  Min magnitude:     {np.min(resp['magnitude_db']):.1f} dB")

    # Find -3dB point
    peak = np.max(resp['magnitude_db'])
    threshold = peak - 3
    above = resp['magnitude_db'] >= threshold
    if np.any(above):
        cutoff_idx = np.where(above)[0][-1]
        print(f"  -3dB frequency:    {resp['frequency'][cutoff_idx]:.3f} × Nyquist")

    # Try to plot with matplotlib
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.plot(resp['frequency'], resp['magnitude_db'], 'b-', linewidth=1.5)
        ax1.set_title(f"{title} — Magnitude Response")
        ax1.set_xlabel("Normalized Frequency (× Nyquist)")
        ax1.set_ylabel("Magnitude (dB)")
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 1)
        ax1.axhline(y=-3, color='r', linestyle='--', alpha=0.5, label='-3 dB')
        ax1.legend()

        ax2.plot(resp['frequency'], np.degrees(resp['phase_rad']), 'r-', linewidth=1.5)
        ax2.set_title("Phase Response")
        ax2.set_xlabel("Normalized Frequency (× Nyquist)")
        ax2.set_ylabel("Phase (degrees)")
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 1)

        plt.tight_layout()

        save_path = args.save or 'filter_response.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n  Plot saved to: {save_path}")

    except ImportError:
        print("\n  [!] matplotlib not installed — skipping plot generation")
        print("      Install with: pip install matplotlib")


if __name__ == '__main__':
    main()
