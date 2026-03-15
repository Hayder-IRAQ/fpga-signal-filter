#!/usr/bin/env python3
"""
Generate Verilog/VHDL from Filter Specifications
==================================================
Command-line tool to design and export synthesizable HDL.

Usage:
    python scripts/generate_hdl.py --filter fir --taps 16 --cutoff 0.2 --output output/
    python scripts/generate_hdl.py --filter iir --cutoff 0.15 --format vhdl
    python scripts/generate_hdl.py --filter cic --stages 3 --decimation 8
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fir_filter import FIRFilter
from src.iir_filter import IIRFilter
from src.moving_average import MovingAverageFilter
from src.cic_filter import CICFilter
from src.coefficient_gen import CoefficientGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Generate Verilog/VHDL for FPGA signal filters"
    )
    parser.add_argument('--filter', choices=['fir', 'iir', 'mavg', 'cic'],
                        required=True, help='Filter type')
    parser.add_argument('--taps', type=int, default=16,
                        help='Number of FIR taps (default: 16)')
    parser.add_argument('--cutoff', type=float, default=0.25,
                        help='Normalized cutoff frequency (default: 0.25)')
    parser.add_argument('--data-width', type=int, default=16,
                        help='Data bit width (default: 16)')
    parser.add_argument('--coeff-width', type=int, default=16,
                        help='Coefficient bit width (default: 16)')
    parser.add_argument('--stages', type=int, default=3,
                        help='CIC stages (default: 3)')
    parser.add_argument('--decimation', type=int, default=8,
                        help='CIC decimation ratio (default: 8)')
    parser.add_argument('--window-log2', type=int, default=4,
                        help='Moving average window log2 (default: 4)')
    parser.add_argument('--format', choices=['verilog', 'vhdl'], default='verilog',
                        help='Output HDL format (default: verilog)')
    parser.add_argument('--output', type=str, default='output/',
                        help='Output directory (default: output/)')
    parser.add_argument('--window', choices=['hamming', 'hann', 'blackman', 'rectangular'],
                        default='hamming', help='FIR window function')

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    print(f"Generating {args.format.upper()} for {args.filter.upper()} filter...")
    print(f"  Data width: {args.data_width} bits")

    if args.filter == 'fir':
        coeffs = CoefficientGenerator.lowpass(
            num_taps=args.taps,
            cutoff_freq=args.cutoff,
            bit_width=args.coeff_width,
            window=args.window
        )
        filt = FIRFilter(
            data_width=args.data_width,
            coeff_width=args.coeff_width,
            num_taps=args.taps,
            coefficients=coeffs
        )
        ext = '.v' if args.format == 'verilog' else '.vhd'
        filepath = os.path.join(args.output, f'fir_filter{ext}')
        if args.format == 'verilog':
            filt.to_verilog(filepath)
        else:
            filt.to_vhdl(filepath)

    elif args.filter == 'iir':
        b, a = CoefficientGenerator.iir_lowpass(
            cutoff_freq=args.cutoff,
            bit_width=args.coeff_width
        )
        filt = IIRFilter(
            data_width=args.data_width,
            coeff_width=args.coeff_width,
            b_coeffs=b, a_coeffs=a
        )
        ext = '.v' if args.format == 'verilog' else '.vhd'
        filepath = os.path.join(args.output, f'iir_filter{ext}')
        if args.format == 'verilog':
            filt.to_verilog(filepath)
        else:
            filt.to_vhdl(filepath)

    elif args.filter == 'mavg':
        filt = MovingAverageFilter(
            data_width=args.data_width,
            window_log2=args.window_log2
        )
        ext = '.v' if args.format == 'verilog' else '.vhd'
        filepath = os.path.join(args.output, f'moving_average{ext}')
        if args.format == 'verilog':
            filt.to_verilog(filepath)
        else:
            filt.to_vhdl(filepath)

    elif args.filter == 'cic':
        filt = CICFilter(
            data_width=args.data_width,
            num_stages=args.stages,
            decimation=args.decimation
        )
        filepath = os.path.join(args.output, 'cic_filter.v')
        filt.to_verilog(filepath)

    print(f"\nDone! Output saved to: {filepath}")


if __name__ == '__main__':
    main()
