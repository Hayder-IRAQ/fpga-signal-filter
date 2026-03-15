# 🔧 FPGA Signal Filter — Python HDL

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![MyHDL](https://img.shields.io/badge/MyHDL-0.11-green.svg)](http://www.myhdl.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A complete, synthesizable **FPGA digital signal filter** library written in Python using [MyHDL](http://www.myhdl.org). Design, simulate, and generate Verilog/VHDL for FIR and IIR filters — all from Python.

<p align="center">
  <img src="docs/block_diagram.png" alt="Filter Block Diagram" width="600">
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **FIR Filter** | Configurable-order Finite Impulse Response filter |
| **IIR Filter** | First & second-order Infinite Impulse Response filter |
| **Moving Average** | Efficient power-of-2 moving average filter |
| **CIC Filter** | Cascaded Integrator-Comb decimation filter |
| **Filter Chain** | Chain multiple filters in a pipeline |
| **Verilog/VHDL Export** | One-command HDL generation for FPGA synthesis |
| **Cocotb Testbenches** | Full simulation & verification suite |
| **Coefficient Generator** | Design filter coefficients from specs |

## 📁 Project Structure

```
fpga-signal-filter/
├── src/
│   ├── __init__.py
│   ├── fir_filter.py          # FIR filter HDL module
│   ├── iir_filter.py          # IIR filter HDL module
│   ├── moving_average.py      # Moving average filter
│   ├── cic_filter.py          # CIC decimation filter
│   ├── filter_chain.py        # Multi-stage filter pipeline
│   ├── coefficient_gen.py     # Filter coefficient generator
│   └── utils.py               # Fixed-point & signal utilities
├── tests/
│   ├── test_fir.py            # FIR filter testbench
│   ├── test_iir.py            # IIR filter testbench
│   ├── test_moving_avg.py     # Moving average testbench
│   ├── test_cic.py            # CIC filter testbench
│   └── test_integration.py    # End-to-end tests
├── examples/
│   ├── lowpass_demo.py        # Low-pass filter demo
│   ├── bandpass_demo.py       # Band-pass filter demo
│   └── noise_removal.py       # Noise removal example
├── scripts/
│   ├── generate_hdl.py        # Export Verilog/VHDL
│   └── plot_response.py       # Plot frequency response
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Hayder-IRAQ/fpga-signal-filter.git
cd fpga-signal-filter
pip install -r requirements.txt
pip install -e .
```

### Design a Low-Pass FIR Filter

```python
from src.fir_filter import FIRFilter
from src.coefficient_gen import CoefficientGenerator

# Generate coefficients for a 16-tap low-pass filter
coeffs = CoefficientGenerator.lowpass(
    num_taps=16,
    cutoff_freq=0.2,    # Normalized frequency (0 to 1)
    bit_width=16         # Fixed-point bit width
)

# Create the synthesizable filter
fir = FIRFilter(
    data_width=16,
    coeff_width=16,
    num_taps=16,
    coefficients=coeffs
)

# Simulate
fir.simulate(num_samples=1000)

# Export to Verilog
fir.to_verilog("output/fir_lowpass.v")
```

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Generate HDL

```bash
python scripts/generate_hdl.py --filter fir --taps 16 --cutoff 0.2 --output output/
```

## 📊 Simulation Results

After running a simulation, you can visualize results:

```bash
python scripts/plot_response.py --filter fir --taps 16 --cutoff 0.2
```

## 🎯 Supported FPGA Targets

- Xilinx (Vivado / ISE)
- Intel / Altera (Quartus)
- Lattice (iCEcube2 / Radiant)
- Any tool supporting standard Verilog or VHDL

## 📖 Documentation

See the [docs/](docs/) folder for:
- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Coefficient Design Guide](docs/COEFFICIENTS.md)

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.
