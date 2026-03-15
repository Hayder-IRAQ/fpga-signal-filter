"""
FIR (Finite Impulse Response) Filter — Synthesizable MyHDL Module
=================================================================
Implements a configurable-order FIR filter with fixed-point arithmetic.

    y[n] = Σ (h[k] * x[n-k])  for k = 0..N-1

Architecture: Transposed-form FIR for optimal FPGA pipelining.
"""

from myhdl import (
    block, Signal, intbv, always_seq, always_comb,
    ResetSignal, modbv, instances, concat
)
import numpy as np


class FIRFilter:
    """
    Synthesizable FIR filter with configurable taps and bit widths.

    Parameters
    ----------
    data_width : int
        Bit width of input/output data (signed).
    coeff_width : int
        Bit width of filter coefficients (signed).
    num_taps : int
        Number of filter taps (filter order + 1).
    coefficients : list[int]
        Fixed-point filter coefficients.
    """

    def __init__(self, data_width=16, coeff_width=16, num_taps=8, coefficients=None):
        self.data_width = data_width
        self.coeff_width = coeff_width
        self.num_taps = num_taps
        self.acc_width = data_width + coeff_width + (num_taps - 1).bit_length()

        if coefficients is None:
            # Default: simple averaging coefficients
            max_val = (1 << (coeff_width - 1)) // num_taps
            self.coefficients = [max_val] * num_taps
        else:
            assert len(coefficients) == num_taps, \
                f"Expected {num_taps} coefficients, got {len(coefficients)}"
            self.coefficients = list(coefficients)

    @block
    def rtl(self, clk, rst, data_in, data_out, valid_in, valid_out):
        """
        Synthesizable RTL block for the FIR filter.

        Ports
        -----
        clk       : input  — System clock
        rst       : input  — Synchronous reset (active high)
        data_in   : input  — Signed input sample [data_width bits]
        data_out  : output — Signed filtered output [data_width bits]
        valid_in  : input  — Input data valid strobe
        valid_out : output — Output data valid strobe
        """
        dw = self.data_width
        cw = self.coeff_width
        aw = self.acc_width
        N = self.num_taps

        # Coefficient ROM
        coeff_rom = [Signal(intbv(c, min=-(1 << (cw - 1)), max=(1 << (cw - 1))))
                     for c in self.coefficients]

        # Delay line (shift register)
        delay_line = [Signal(intbv(0, min=-(1 << (dw - 1)), max=(1 << (dw - 1))))
                      for _ in range(N)]

        # Accumulator pipeline
        acc = [Signal(intbv(0, min=-(1 << (aw - 1)), max=(1 << (aw - 1))))
               for _ in range(N)]

        # Product signals
        products = [Signal(intbv(0, min=-(1 << (dw + cw - 1)), max=(1 << (dw + cw - 1))))
                    for _ in range(N)]

        # Internal valid pipeline
        valid_pipe = Signal(intbv(0)[4:])

        @always_seq(clk.posedge, reset=rst)
        def shift_register():
            """Shift input samples through the delay line."""
            if valid_in:
                delay_line[0].next = data_in
                for i in range(1, N):
                    delay_line[i].next = delay_line[i - 1]

        @always_comb
        def multiply():
            """Multiply each delayed sample by its coefficient."""
            for i in range(N):
                products[i].next = delay_line[i] * coeff_rom[i]

        @always_seq(clk.posedge, reset=rst)
        def accumulate():
            """Sum all products to produce the filter output."""
            total = intbv(0, min=-(1 << (aw - 1)), max=(1 << (aw - 1)))
            for i in range(N):
                total = total + products[i]
            acc[0].next = total

        @always_seq(clk.posedge, reset=rst)
        def output_stage():
            """Truncate accumulator to output width with rounding."""
            shift = cw - 1  # Remove coefficient fractional bits
            rounded = (acc[0] + (1 << (shift - 1))) >> shift
            # Saturate to output range
            max_out = (1 << (dw - 1)) - 1
            min_out = -(1 << (dw - 1))
            if rounded > max_out:
                data_out.next = max_out
            elif rounded < min_out:
                data_out.next = min_out
            else:
                data_out.next = rounded

        @always_seq(clk.posedge, reset=rst)
        def valid_pipeline():
            """Propagate valid signal through the pipeline."""
            valid_pipe.next = concat(valid_pipe[3:0], valid_in)
            valid_out.next = valid_pipe[2]

        return instances()

    def create_signals(self):
        """Create default signal set for simulation/conversion."""
        dw = self.data_width
        clk = Signal(bool(0))
        rst = ResetSignal(0, active=1, isasync=False)
        data_in = Signal(intbv(0, min=-(1 << (dw - 1)), max=(1 << (dw - 1))))
        data_out = Signal(intbv(0, min=-(1 << (dw - 1)), max=(1 << (dw - 1))))
        valid_in = Signal(bool(0))
        valid_out = Signal(bool(0))
        return clk, rst, data_in, data_out, valid_in, valid_out

    def to_verilog(self, filepath="fir_filter.v"):
        """Convert the filter to a Verilog file."""
        from myhdl import toVerilog
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='Verilog', path=filepath)
        print(f"[✓] Verilog exported: {filepath}")

    def to_vhdl(self, filepath="fir_filter.vhd"):
        """Convert the filter to a VHDL file."""
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='VHDL', path=filepath)
        print(f"[✓] VHDL exported: {filepath}")

    def simulate(self, input_signal=None, num_samples=256):
        """
        Run a behavioral simulation of the FIR filter (NumPy model).

        Parameters
        ----------
        input_signal : np.ndarray or None
            Input signal samples (int). If None, generates a test signal.
        num_samples : int
            Number of samples to simulate.

        Returns
        -------
        dict with keys: 'input', 'output', 'time'
        """
        if input_signal is None:
            t = np.arange(num_samples)
            max_val = (1 << (self.data_width - 1)) - 1
            sig = 0.5 * np.sin(2 * np.pi * 0.05 * t) + 0.3 * np.sin(2 * np.pi * 0.4 * t)
            sig += 0.1 * np.random.randn(num_samples)
            input_signal = np.clip(sig * max_val * 0.5, -max_val, max_val).astype(int)

        inputs = input_signal[:num_samples].astype(float)
        coeffs = np.array(self.coefficients, dtype=float)
        scale = (1 << (self.coeff_width - 1))

        # FIR convolution (behavioral model matching RTL)
        raw = np.convolve(inputs, coeffs, mode='full')[:num_samples]
        # Scale and saturate
        scaled = np.round(raw / scale).astype(int)
        max_out = (1 << (self.data_width - 1)) - 1
        min_out = -(1 << (self.data_width - 1))
        output = np.clip(scaled, min_out, max_out)

        return {
            'input': input_signal[:num_samples],
            'output': output,
            'time': np.arange(num_samples)
        }

    def __repr__(self):
        return (f"FIRFilter(data_width={self.data_width}, "
                f"coeff_width={self.coeff_width}, "
                f"num_taps={self.num_taps})")
