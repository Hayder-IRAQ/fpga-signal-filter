"""
CIC (Cascaded Integrator-Comb) Filter — Synthesizable MyHDL Module
===================================================================
Multi-stage CIC decimation filter for efficient sample rate conversion.

No multipliers required — uses only adders and subtractors.
Ideal for high-rate input data decimation on FPGAs.
"""

from myhdl import (
    block, Signal, intbv, always_seq, always_comb,
    ResetSignal, instances
)
import numpy as np


class CICFilter:
    """
    CIC decimation filter.

    Parameters
    ----------
    data_width : int
        Input data bit width (signed).
    num_stages : int
        Number of integrator-comb stages (1-6 typical).
    decimation : int
        Decimation ratio R.
    diff_delay : int
        Differential delay M (typically 1 or 2).
    """

    def __init__(self, data_width=16, num_stages=3, decimation=8, diff_delay=1):
        self.data_width = data_width
        self.num_stages = num_stages
        self.decimation = decimation
        self.diff_delay = diff_delay
        # CIC output growth: N * log2(R * M) bits
        self.growth = num_stages * int(np.ceil(np.log2(decimation * diff_delay)))
        self.internal_width = data_width + self.growth

    @block
    def rtl(self, clk, rst, data_in, data_out, valid_in, valid_out):
        """
        Synthesizable RTL.

        Architecture:
          [Integrators] → [Decimator] → [Comb stages]
        """
        iw = self.internal_width
        N = self.num_stages
        R = self.decimation
        M = self.diff_delay

        # -- Integrator section --
        integ = [Signal(intbv(0, min=-(1 << (iw-1)), max=(1 << (iw-1))))
                 for _ in range(N)]

        # -- Decimation counter --
        dec_count = Signal(intbv(0, min=0, max=R))
        dec_valid = Signal(bool(0))
        dec_data = Signal(intbv(0, min=-(1 << (iw-1)), max=(1 << (iw-1))))

        # -- Comb section --
        comb_in = [Signal(intbv(0, min=-(1 << (iw-1)), max=(1 << (iw-1))))
                   for _ in range(N)]
        comb_delay = [Signal(intbv(0, min=-(1 << (iw-1)), max=(1 << (iw-1))))
                      for _ in range(N)]
        comb_out = [Signal(intbv(0, min=-(1 << (iw-1)), max=(1 << (iw-1))))
                    for _ in range(N)]

        valid_reg = Signal(bool(0))

        @always_seq(clk.posedge, reset=rst)
        def integrators():
            """Cascade of integrators (running sums)."""
            if valid_in:
                # First integrator takes input directly
                integ[0].next = integ[0] + data_in
                # Subsequent integrators chain
                for i in range(1, N):
                    integ[i].next = integ[i] + integ[i - 1]

        @always_seq(clk.posedge, reset=rst)
        def decimator():
            """Downsample by factor R."""
            if valid_in:
                if dec_count == R - 1:
                    dec_count.next = 0
                    dec_valid.next = 1
                    dec_data.next = integ[N - 1]
                else:
                    dec_count.next = dec_count + 1
                    dec_valid.next = 0
            else:
                dec_valid.next = 0

        @always_seq(clk.posedge, reset=rst)
        def combs():
            """Cascade of comb (differentiator) stages."""
            if dec_valid:
                # First comb
                comb_out[0].next = dec_data - comb_delay[0]
                comb_delay[0].next = dec_data
                # Subsequent combs
                for i in range(1, N):
                    comb_out[i].next = comb_out[i - 1] - comb_delay[i]
                    comb_delay[i].next = comb_out[i - 1]

                valid_reg.next = 1
            else:
                valid_reg.next = 0

        @always_seq(clk.posedge, reset=rst)
        def output_truncate():
            """Truncate internal width to output width with bit pruning."""
            shift = self.growth
            truncated = comb_out[N - 1] >> shift
            dw = self.data_width
            max_out = (1 << (dw - 1)) - 1
            min_out = -(1 << (dw - 1))
            if truncated > max_out:
                data_out.next = max_out
            elif truncated < min_out:
                data_out.next = min_out
            else:
                data_out.next = truncated

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

    def to_verilog(self, filepath="cic_filter.v"):
        clk, rst, data_in, data_out, valid_in, valid_out = self.create_signals()
        inst = self.rtl(clk, rst, data_in, data_out, valid_in, valid_out)
        inst.convert(hdl='Verilog', path=filepath)
        print(f"[✓] Verilog exported: {filepath}")

    def simulate(self, input_signal=None, num_samples=1024):
        """Behavioral CIC simulation using NumPy."""
        if input_signal is None:
            t = np.arange(num_samples)
            max_val = (1 << (self.data_width - 1)) - 1
            sig = 0.5 * np.sin(2 * np.pi * 0.01 * t) + 0.3 * np.sin(2 * np.pi * 0.45 * t)
            input_signal = np.clip(sig * max_val * 0.4, -max_val, max_val).astype(int)

        N = self.num_stages
        R = self.decimation

        # Integrators (running cumulative sums)
        data = input_signal.astype(float)
        for _ in range(N):
            data = np.cumsum(data)

        # Decimate
        data = data[::R]

        # Comb stages (differentiators)
        for _ in range(N):
            delayed = np.concatenate(([0], data[:-1]))
            data = data - delayed

        # Normalize
        gain = (R * self.diff_delay) ** N
        output = (data / gain).astype(int)

        return {
            'input': input_signal,
            'output': output,
            'time_in': np.arange(len(input_signal)),
            'time_out': np.arange(len(output))
        }

    def __repr__(self):
        return (f"CICFilter(stages={self.num_stages}, "
                f"decimation={self.decimation}, "
                f"data_width={self.data_width})")
