# Coefficient Design Guide

## Understanding Normalized Frequency

All frequencies in this library are **normalized** to the Nyquist rate:

```
f_normalized = f_actual / (Fs / 2)
```

| Normalized | Meaning |
|-----------|---------|
| 0.0 | DC (0 Hz) |
| 0.25 | Quarter of Nyquist |
| 0.5 | Half of Nyquist (Fs/4) |
| 1.0 | Nyquist frequency (Fs/2) |

**Example:** For a 100 MHz sample rate, a 10 MHz cutoff:
```
f_norm = 10e6 / (100e6 / 2) = 0.2
```

## Choosing Filter Type

| Need | Recommended Filter |
|------|--------------------|
| Remove high-freq noise | FIR Low-pass |
| Remove DC offset | FIR High-pass |
| Extract specific band | FIR Band-pass |
| Remove specific frequency | FIR Band-stop (Notch) |
| Sharp cutoff, few resources | IIR Biquad |
| Simple smoothing, no multipliers | Moving Average |
| High-rate decimation | CIC |

## FIR Design Tips

### Number of Taps

More taps = sharper transition, better stopband rejection, but more FPGA resources.

| Taps | Transition Width | Stopband | DSP Slices |
|------|-----------------|----------|------------|
| 8 | ~0.25 × Fs | -20 dB | 8 |
| 16 | ~0.12 × Fs | -40 dB | 16 |
| 32 | ~0.06 × Fs | -60 dB | 32 |
| 64 | ~0.03 × Fs | -80 dB | 64 |

### Window Functions

| Window | Main Lobe | Sidelobe | Best For |
|--------|-----------|----------|----------|
| Rectangular | Narrowest | -13 dB | Analysis only |
| Hamming | Medium | -43 dB | General purpose ✓ |
| Hann | Medium | -31 dB | Spectral analysis |
| Blackman | Widest | -58 dB | High stopband rejection |

### Example: Audio Low-Pass at 4 kHz (Fs = 48 kHz)

```python
from src.coefficient_gen import CoefficientGenerator

f_norm = 4000 / (48000 / 2)  # = 0.167

coeffs = CoefficientGenerator.lowpass(
    num_taps=32,
    cutoff_freq=f_norm,
    bit_width=16,
    window='hamming'
)
```

## IIR Design Tips

### Q Factor

The Q factor controls the resonance peak at the cutoff frequency:

| Q | Behavior |
|---|----------|
| 0.5 | Overdamped — gentle rolloff |
| 0.707 | Butterworth — maximally flat passband ✓ |
| 1.0 | Slight peak at cutoff |
| 2.0+ | Strong resonance — use with caution |

### Stability

IIR filters can become unstable with improper coefficients. Always verify:

```python
b, a = CoefficientGenerator.iir_lowpass(cutoff_freq=0.2, q_factor=0.707)
iir = IIRFilter(b_coeffs=b, a_coeffs=a)

# Test with impulse — output should decay, not grow
result = iir.simulate(num_samples=256)
assert np.all(np.abs(result['output']) < 32768), "Filter may be unstable!"
```

## Fixed-Point Precision

### Bit Width Selection

| Application | Data Width | Coeff Width | Notes |
|-------------|-----------|-------------|-------|
| Audio (16-bit) | 16 | 16 | Standard quality |
| Audio (24-bit) | 24 | 16 | High quality |
| RF / SDR | 12-14 | 16 | ADC-matched |
| Control systems | 16-32 | 16-24 | Precision critical |

### Overflow Prevention

The accumulator width is automatically sized:

```
acc_width = data_width + coeff_width + ceil(log2(num_taps))
```

For a 16-bit data, 16-bit coefficients, 16-tap FIR:
```
acc_width = 16 + 16 + 4 = 36 bits
```

## Quick Recipes

### Anti-Aliasing Filter (Before Downsampling)
```python
# Decimate by 4 → cutoff at 0.25 × original Nyquist
coeffs = CoefficientGenerator.lowpass(num_taps=32, cutoff_freq=0.25)
```

### DC Removal
```python
coeffs = CoefficientGenerator.highpass(num_taps=16, cutoff_freq=0.02)
```

### 50/60 Hz Hum Removal (Fs = 1 kHz)
```python
f_notch = 50 / (1000 / 2)  # = 0.1
bw = 5 / (1000 / 2)         # 5 Hz bandwidth = 0.01
coeffs = CoefficientGenerator.bandstop(
    num_taps=64,
    low_freq=f_notch - bw,
    high_freq=f_notch + bw
)
```

### Matched Filter (Template Matching)
```python
# Use the time-reversed template as coefficients
template = [100, 500, 1000, 500, 100]  # Your expected pulse shape
coeffs = template[::-1]  # Reverse for matched filter
fir = FIRFilter(num_taps=len(coeffs), coefficients=coeffs)
```
