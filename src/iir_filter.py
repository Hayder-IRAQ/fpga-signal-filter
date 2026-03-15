"""
IIR (Infinite Impulse Response) Filter — Synthesizable MyHDL Module
===================================================================
Implements a second-order (biquad) IIR filter with fixed-point arithmetic.

Transfer function:
    H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 + a1*z^-1 + a2*z^-2)

Direct Form I implementation for numerical stability.
"""

from myhdl import (
    block, Signal, intbv, always_seq, always_comb,
    ResetSignal, instances
)
import numpy as np


class IIRFilter:
    """
    Synthesizable second-order IIR (biquad) filter.

    Parameters
    ----------
    data_width : int
        Bit width of input/output data (signed).
    coeff_width : int
        Bit width of filter coefficients (signed, Q-format fractional).
    b_coeffs : tuple(int, int, int)
        Numerator coefficients (b0, b1, b2) in fixed-point.
    a_coeffs : tuple(int, int)
        Denominator coefficients (a1, a2) in fixed-point.
        Note: a0 is normalized to 1 and not included.
    """

    def __init__(self, data_width=16, coeff_width=16,
                 b_coeffs=(4096, 8192, 4096), a_coeffs=(-7168, 3072)):
        self.data_width = data_width
        self.coeff_width = coeff_width
        self.b_coeffs = b_coeffs
        self.a_coeffs = a_coeffs
        # Extra bits for accumulation to prevent overflow
        self.acc_width = data_width + coeff_width + 4

    @block
    def rtl(self, clk, rst, data_in, data_out, valid_in, valid_out):
        """
        Synthesizable RTL block for the IIR biquad filter.

        Ports
        -----
        clk       : input  — System clock
        rst       : input  — Synchronous reset
        data_in   : input  — Signed input sample
        data_out  : output — Signed filtered output
        valid_in  : input  — Input valid strobe
        valid_out : output — Output valid strobe
        """
        dw = self.data_width
        cw = self.coeff_width
        aw = self.acc_width

        # Coefficient signals — use wider range to hold all coefficient values
        cmax = max(
            abs(self.b_coeffs[0]), abs(self.b_coeffs[1]), abs(self.b_coeffs[2]),
            abs(self.a_coeffs[0]), abs(self.a_coeffs[1])
        ) + 1
        crange = max(cmax, (1 << (cw - 1)))
        b0 = Signal(intbv(self.b_coeffs[0], min=-crange - 1, max=crange + 1))
        b1 = Signal(intbv(self.b_coeffs[1], min=-crange - 1, max=crange + 1))
        b2 = Signal(intbv(self.b_coeffs[2], min=-crange - 1, max=crange + 1))
        a1 = Signal(intbv(self.a_coeffs[0], min=-crange - 1, max=crange + 1))
        a2 = Signal(intbv(self.a_coeffs[1], min=-crange - 1, max=crange + 1))

        # State registers (delayed inputs and outputs)
        x_d1 = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        x_d2 = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        y_d1 = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        y_d2 = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))

        # Accumulator
        acc = Signal(intbv(0, min=-(1 << (aw-1)), max=(1 << (aw-1))))

        # Pipeline valid
        valid_reg = Signal(bool(0))

        @always_seq(clk.posedge, reset=rst)
        def iir_process():
            """Main IIR computation — Direct Form I."""
            if valid_in:
                # y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
                feedforward = (b0 * data_in) + (b1 * x_d1) + (b2 * x_d2)
                feedback = (a1 * y_d1) + (a2 * y_d2)
                result = feedforward - feedback

                # Scale back (remove fractional bits)
                shift = cw - 1
                scaled = (result + (1 << (shift - 1))) >> shift

                # Saturate
                max_out = (1 << (dw - 1)) - 1
                min_out = -(1 << (dw - 1))
                if scaled > max_out:
                    y_out = max_out
                elif scaled < min_out:
                    y_out = min_out
                else:
                    y_out = scaled

                data_out.next = y_out
                valid_reg.next = 1

                # Update delay line
                x_d2.next = x_d1
                x_d1.next = data_in
                y_d2.next = y_d1
                y_d1.next = y_out
            else:
                valid_reg.next = 0

        @always_comb
        def valid_output():
            valid_out.next = valid_reg

        return instances()

    def create_signals(self):
        """Create default signal set for simulation/conversion."""
        dw = self.data_width
        clk = Signal(bool(0))
        rst = ResetSignal(0, active=1, isasync=False)
        data_in = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        data_out = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        valid_in = Signal(bool(0))
        valid_out = Signal(bool(0))
        return clk, rst, data_in, data_out, valid_in, valid_out

    def to_verilog(self, filepath="iir_filter.v"):
        """Convert to Verilog."""
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='Verilog', path=filepath)
        print(f"[✓] Verilog exported: {filepath}")

    def to_vhdl(self, filepath="iir_filter.vhd"):
        """Convert to VHDL."""
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='VHDL', path=filepath)
        print(f"[✓] VHDL exported: {filepath}")

    def simulate(self, input_signal=None, num_samples=256):
        """Run behavioral simulation using NumPy (matches RTL behavior)."""
        if input_signal is None:
            t = np.arange(num_samples)
            max_val = (1 << (self.data_width - 1)) - 1
            sig = 0.5 * np.sin(2 * np.pi * 0.05 * t) + 0.3 * np.sin(2 * np.pi * 0.4 * t)
            input_signal = np.clip(sig * max_val * 0.5, -max_val, max_val).astype(int)

        inputs = input_signal[:num_samples].astype(float)
        b0, b1, b2 = [float(c) for c in self.b_coeffs]
        a1, a2 = [float(c) for c in self.a_coeffs]
        scale = float(1 << (self.coeff_width - 1))
        max_out = (1 << (self.data_width - 1)) - 1
        min_out = -(1 << (self.data_width - 1))

        outputs = np.zeros(len(inputs), dtype=int)
        x_d1, x_d2, y_d1, y_d2 = 0.0, 0.0, 0.0, 0.0

        for n in range(len(inputs)):
            x = inputs[n]
            ff = b0 * x + b1 * x_d1 + b2 * x_d2
            fb = a1 * y_d1 + a2 * y_d2
            result = (ff - fb) / scale
            y = int(np.clip(np.round(result), min_out, max_out))
            outputs[n] = y
            x_d2, x_d1 = x_d1, x
            y_d2, y_d1 = y_d1, float(y)

        return {
            'input': input_signal[:num_samples],
            'output': outputs,
            'time': np.arange(num_samples)
        }

    def __repr__(self):
        return (f"IIRFilter(data_width={self.data_width}, "
                f"b={self.b_coeffs}, a={self.a_coeffs})")
