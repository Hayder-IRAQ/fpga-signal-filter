# API Reference

## FIRFilter

```python
from src import FIRFilter
```

### Constructor

```python
FIRFilter(data_width=16, coeff_width=16, num_taps=8, coefficients=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_width` | int | 16 | Input/output bit width (signed) |
| `coeff_width` | int | 16 | Coefficient bit width (signed) |
| `num_taps` | int | 8 | Number of filter taps |
| `coefficients` | list[int] | None | Fixed-point coefficients (auto-generated if None) |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `rtl(clk, rst, data_in, data_out, valid_in, valid_out)` | MyHDL block | Synthesizable RTL |
| `simulate(input_signal=None, num_samples=256)` | dict | Run behavioral simulation |
| `to_verilog(filepath)` | None | Export Verilog file |
| `to_vhdl(filepath)` | None | Export VHDL file |
| `create_signals()` | tuple | Create default signal set |

### Simulation Output

```python
result = fir.simulate(num_samples=512)
result['input']   # np.ndarray — input samples
result['output']  # np.ndarray — filtered output
result['time']    # np.ndarray — sample indices
```

---

## IIRFilter

```python
from src import IIRFilter
```

### Constructor

```python
IIRFilter(data_width=16, coeff_width=16, b_coeffs=(4096, 8192, 4096), a_coeffs=(-7168, 3072))
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_width` | int | 16 | Input/output bit width |
| `coeff_width` | int | 16 | Coefficient bit width |
| `b_coeffs` | tuple(int,int,int) | — | Numerator coefficients (b0, b1, b2) |
| `a_coeffs` | tuple(int,int) | — | Denominator coefficients (a1, a2) |

### Methods

Same interface as FIRFilter: `rtl()`, `simulate()`, `to_verilog()`, `to_vhdl()`.

---

## MovingAverageFilter

```python
from src import MovingAverageFilter
```

### Constructor

```python
MovingAverageFilter(data_width=16, window_log2=4)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_width` | int | 16 | Input/output bit width |
| `window_log2` | int | 4 | Log2 of window size (4 → 16 samples) |

---

## CICFilter

```python
from src import CICFilter
```

### Constructor

```python
CICFilter(data_width=16, num_stages=3, decimation=8, diff_delay=1)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_width` | int | 16 | Input data bit width |
| `num_stages` | int | 3 | Number of integrator-comb stages |
| `decimation` | int | 8 | Decimation ratio R |
| `diff_delay` | int | 1 | Differential delay M |

---

## FilterChain

```python
from src import FilterChain
```

### Constructor

```python
FilterChain(filters=None)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add(filter_instance)` | self | Add a filter stage |
| `simulate(input_signal=None, num_samples=256)` | dict | Simulate entire chain |
| `describe()` | None | Print chain summary |

### Chain Simulation Output

```python
result = chain.simulate(num_samples=512)
result['input']         # Original input
result['output']        # Final output
result['intermediate']  # List of outputs per stage
result['stages']        # Number of stages
```

---

## CoefficientGenerator

```python
from src import CoefficientGenerator
```

All methods are static — no instantiation needed.

### FIR Coefficient Design

```python
# Low-pass
coeffs = CoefficientGenerator.lowpass(num_taps=16, cutoff_freq=0.25, bit_width=16, window='hamming')

# High-pass
coeffs = CoefficientGenerator.highpass(num_taps=16, cutoff_freq=0.25, bit_width=16)

# Band-pass
coeffs = CoefficientGenerator.bandpass(num_taps=32, low_freq=0.2, high_freq=0.4, bit_width=16)

# Band-stop
coeffs = CoefficientGenerator.bandstop(num_taps=32, low_freq=0.2, high_freq=0.4, bit_width=16)
```

### IIR Coefficient Design

```python
# Low-pass biquad
b_coeffs, a_coeffs = CoefficientGenerator.iir_lowpass(cutoff_freq=0.2, q_factor=0.707, bit_width=16)

# High-pass biquad
b_coeffs, a_coeffs = CoefficientGenerator.iir_highpass(cutoff_freq=0.3, q_factor=0.707, bit_width=16)
```

### Analysis

```python
resp = CoefficientGenerator.frequency_response(coefficients, bit_width=16, num_points=512)
resp['frequency']     # Normalized frequency [0, 1]
resp['magnitude_db']  # Magnitude in dB
resp['phase_rad']     # Phase in radians
```

---

## Utility Functions

```python
from src.utils import *
```

| Function | Description |
|----------|-------------|
| `float_to_fixed(value, bit_width)` | Float [-1,1) → fixed-point int |
| `fixed_to_float(value, bit_width)` | Fixed-point int → float |
| `generate_sine(freq, num_samples, amplitude, bit_width)` | Quantized sine wave |
| `generate_chirp(f_start, f_end, num_samples, ...)` | Linear chirp signal |
| `generate_noise(num_samples, amplitude, bit_width)` | White noise |
| `generate_mixed_signal(freqs, amplitudes, ...)` | Multi-tone + noise |
| `snr_db(original, filtered)` | Signal-to-noise ratio in dB |
| `compute_fft(signal, bit_width)` | FFT magnitude spectrum |
