"""
Moving Average Filter — Synthesizable MyHDL Module
===================================================
Efficient power-of-2 window moving average using shift operations.
No multipliers needed — ideal for resource-constrained FPGAs.

    y[n] = (1/N) * Σ x[n-k]  for k = 0..N-1
"""

from myhdl import (
    block, Signal, intbv, always_seq, always_comb,
    ResetSignal, instances
)
import numpy as np


class MovingAverageFilter:
    """
    Moving average filter with power-of-2 window size.

    Parameters
    ----------
    data_width : int
        Bit width of input/output data (signed).
    window_log2 : int
        Log2 of the window size (e.g., 4 means window = 16).
    """

    def __init__(self, data_width=16, window_log2=4):
        self.data_width = data_width
        self.window_log2 = window_log2
        self.window_size = 1 << window_log2
        self.acc_width = data_width + window_log2

    @block
    def rtl(self, clk, rst, data_in, data_out, valid_in, valid_out):
        """
        Synthesizable RTL block.

        Uses a circular buffer and running sum for O(1) computation
        per sample — no multiply, just add/subtract/shift.
        """
        dw = self.data_width
        aw = self.acc_width
        N = self.window_size
        wlog = self.window_log2

        # Circular buffer
        buffer = [Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
                  for _ in range(N)]
        write_ptr = Signal(intbv(0, min=0, max=N))

        # Running accumulator
        acc = Signal(intbv(0, min=-(1 << (aw-1)), max=(1 << (aw-1))))

        valid_reg = Signal(bool(0))
        filled = Signal(bool(0))
        count = Signal(intbv(0, min=0, max=N + 1))

        @always_seq(clk.posedge, reset=rst)
        def process():
            if valid_in:
                oldest = buffer[write_ptr]
                # Update running sum: add new, subtract oldest
                acc.next = acc + data_in - oldest

                # Write new sample to circular buffer
                buffer[write_ptr].next = data_in

                # Advance write pointer
                if write_ptr == N - 1:
                    write_ptr.next = 0
                    filled.next = 1
                else:
                    write_ptr.next = write_ptr + 1

                # Output: divide by N using right shift
                data_out.next = (acc + data_in - oldest) >> wlog
                valid_reg.next = 1
            else:
                valid_reg.next = 0

        @always_comb
        def valid_output():
            valid_out.next = valid_reg

        return instances()

    def create_signals(self):
        dw = self.data_width
        clk = Signal(bool(0))
        rst = ResetSignal(0, active=1, isasync=False)
        data_in = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        data_out = Signal(intbv(0, min=-(1 << (dw-1)), max=(1 << (dw-1))))
        valid_in = Signal(bool(0))
        valid_out = Signal(bool(0))
        return clk, rst, data_in, data_out, valid_in, valid_out

    def to_verilog(self, filepath="moving_average.v"):
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='Verilog', path=filepath)
        print(f"[✓] Verilog exported: {filepath}")

    def to_vhdl(self, filepath="moving_average.vhd"):
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='VHDL', path=filepath)
        print(f"[✓] VHDL exported: {filepath}")

    def simulate(self, input_signal=None, num_samples=256):
        """Run behavioral simulation using pure NumPy for speed."""
        if input_signal is None:
            t = np.arange(num_samples)
            max_val = (1 << (self.data_width - 1)) - 1
            sig = 0.5 * np.sin(2 * np.pi * 0.05 * t) + 0.5 * np.random.randn(num_samples)
            input_signal = np.clip(sig * max_val * 0.3, -max_val, max_val).astype(int)

        # Behavioral model
        N = self.window_size
        output = np.convolve(input_signal, np.ones(N) / N, mode='full')[:num_samples]
        return {
            'input': input_signal[:num_samples],
            'output': output.astype(int),
            'time': np.arange(num_samples)
        }

    def __repr__(self):
        return (f"MovingAverageFilter(data_width={self.data_width}, "
                f"window_size={self.window_size})")
