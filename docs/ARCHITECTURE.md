# Architecture Guide

## Overview

This library provides synthesizable digital filter implementations using Python and MyHDL. Each filter is designed as a self-contained module that can be simulated in Python and exported to Verilog or VHDL for FPGA deployment.

## Design Philosophy

```
  Python Design Space              FPGA Hardware
  ─────────────────               ─────────────
  ┌─────────────────┐             ┌──────────────┐
  │ CoefficientGen  │────────────▶│  ROM / LUT   │
  │ (scipy/numpy)   │             │              │
  └─────────────────┘             └──────┬───────┘
                                         │
  ┌─────────────────┐             ┌──────▼───────┐
  │ Filter Module   │────MyHDL───▶│  Verilog /   │
  │ (MyHDL @block)  │  convert    │  VHDL RTL    │
  └─────────────────┘             └──────┬───────┘
                                         │
  ┌─────────────────┐             ┌──────▼───────┐
  │ Testbench       │────verify──▶│  Synthesis   │
  │ (pytest/cocotb) │             │  & Place     │
  └─────────────────┘             └──────────────┘
```

## Fixed-Point Arithmetic

All filters use signed fixed-point arithmetic (Q-format):

- **Q15** for 16-bit: 1 sign bit + 15 fractional bits → range [-1.0, +0.99997]
- **Q11** for 12-bit: 1 sign bit + 11 fractional bits → range [-1.0, +0.99951]

### Multiplication and Accumulation

```
  Input (16-bit)  ×  Coefficient (16-bit)  =  Product (32-bit)
  ───────────────    ────────────────────     ─────────────────
  Q15             ×  Q15                    =  Q30

  Accumulation adds log2(N) bits for N taps.
  Output is truncated back to 16-bit with rounding.
```

## Module Architecture

### FIR Filter (Transposed Form)

```
  x[n] ──┬──[×h0]──[+]──[z⁻¹]──[+]──[z⁻¹]──...──[+]── y[n]
          │                │                │
          ├──[×h1]─────────┘                │
          │                                 │
          └──[×hN-1]────────────────────────┘
```

- **Resources**: N multipliers, N-1 adders, N-1 registers
- **Latency**: 3 clock cycles (pipeline: multiply → accumulate → output)
- **Throughput**: 1 sample per clock

### IIR Filter (Direct Form I)

```
  x[n] ──[×b0]──[+]──────────────────── y[n]
          │      ↑                        │
  x[n-1]─[×b1]──┘  ┌──[×(-a1)]──────────┤
          │         │                     │
  x[n-2]─[×b2]─────┤  ┌──[×(-a2)]───────┘
                    │  │
                y[n-1] y[n-2]
```

- **Resources**: 5 multipliers, 4 adders, 4 registers
- **Latency**: 1 clock cycle
- **Caution**: Feedback path requires careful coefficient design for stability

### Moving Average Filter

```
  x[n] ──[+]──────────────────[>>log2(N)]── y[n]
          ↑           │
          │     ┌─────┴─────┐
          │     │ Circular   │
          └─────┤ Buffer [N] ├── x[n-N] ──[-]
                └───────────┘
```

- **Resources**: 0 multipliers, 1 adder, 1 subtractor, N registers
- **Latency**: 1 clock cycle
- **Advantage**: No multipliers needed (power-of-2 division via shift)

### CIC Filter

```
  Integrators (Fs)          Decimator        Combs (Fs/R)
  ┌────┐ ┌────┐ ┌────┐    ┌────┐    ┌────┐ ┌────┐ ┌────┐
  │ Σ  │→│ Σ  │→│ Σ  │───▶│ ↓R │───▶│ Δ  │→│ Δ  │→│ Δ  │── y[n]
  └────┘ └────┘ └────┘    └────┘    └────┘ └────┘ └────┘
  ←── N stages ──▶                  ←── N stages ──▶
```

- **Resources**: 0 multipliers, 2N adders, minimal registers
- **Ideal for**: High sample rate decimation (SDR, ADC front-ends)

## Signal Flow

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  valid_in │───▶│  Filter  │───▶│ valid_out│
  │  data_in  │───▶│  Core    │───▶│ data_out │
  │  clk      │───▶│          │    │          │
  │  rst      │───▶│          │    │          │
  └──────────┘    └──────────┘    └──────────┘
```

Every filter module uses the same port interface:
- `clk` — System clock
- `rst` — Synchronous reset (active high)
- `data_in` — Signed input sample
- `data_out` — Signed filtered output
- `valid_in` — Input strobe
- `valid_out` — Output strobe (accounts for pipeline latency)

## Resource Estimation

| Filter | Multipliers | Adders | Registers | Latency |
|--------|------------|--------|-----------|---------|
| FIR-16 | 16 (DSP48) | 15 | 19 | 3 clk |
| IIR Biquad | 5 (DSP48) | 4 | 6 | 1 clk |
| MovAvg-16 | 0 | 2 | 18 | 1 clk |
| CIC-3-8 | 0 | 6 | 9 | 1 clk |
