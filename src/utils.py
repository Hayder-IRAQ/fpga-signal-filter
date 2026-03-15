"""
Utilities — Fixed-Point Math & Signal Helpers
==============================================
Common utilities for FPGA signal processing.
"""

import numpy as np
from typing import Tuple


def float_to_fixed(value: float, bit_width: int = 16) -> int:
    """Convert a float in [-1, 1) to signed fixed-point integer."""
    scale = (1 << (bit_width - 1)) - 1
    return int(np.clip(round(value * scale), -(1 << (bit_width - 1)), scale))


def fixed_to_float(value: int, bit_width: int = 16) -> float:
    """Convert a signed fixed-point integer back to float."""
    scale = (1 << (bit_width - 1)) - 1
    return value / scale


def generate_sine(freq: float, num_samples: int = 256,
                  amplitude: float = 0.8, bit_width: int = 16) -> np.ndarray:
    """
    Generate a quantized sine wave.

    Parameters
    ----------
    freq : float
        Normalized frequency (0 to 0.5, where 0.5 = Nyquist).
    """
    t = np.arange(num_samples)
    sig = amplitude * np.sin(2 * np.pi * freq * t)
    scale = (1 << (bit_width - 1)) - 1
    return np.clip(np.round(sig * scale), -(1 << (bit_width - 1)), scale).astype(int)


def generate_chirp(f_start: float, f_end: float, num_samples: int = 512,
                   amplitude: float = 0.8, bit_width: int = 16) -> np.ndarray:
    """Generate a linear frequency chirp signal."""
    t = np.linspace(0, 1, num_samples)
    phase = 2 * np.pi * (f_start * t + (f_end - f_start) * t**2 / 2)
    sig = amplitude * np.sin(phase)
    scale = (1 << (bit_width - 1)) - 1
    return np.clip(np.round(sig * scale), -(1 << (bit_width - 1)), scale).astype(int)


def generate_noise(num_samples: int = 256, amplitude: float = 0.5,
                   bit_width: int = 16) -> np.ndarray:
    """Generate quantized white noise."""
    sig = amplitude * np.random.randn(num_samples)
    scale = (1 << (bit_width - 1)) - 1
    return np.clip(np.round(sig * scale), -(1 << (bit_width - 1)), scale).astype(int)


def generate_mixed_signal(freqs: list, amplitudes: list = None,
                          num_samples: int = 256, noise_level: float = 0.1,
                          bit_width: int = 16) -> np.ndarray:
    """
    Generate a signal with multiple frequency components + noise.

    Parameters
    ----------
    freqs : list of float
        Normalized frequencies.
    amplitudes : list of float or None
        Amplitude per component. Defaults to equal amplitudes.
    """
    if amplitudes is None:
        amplitudes = [0.5 / len(freqs)] * len(freqs)

    t = np.arange(num_samples)
    sig = np.zeros(num_samples)
    for f, a in zip(freqs, amplitudes):
        sig += a * np.sin(2 * np.pi * f * t)
    sig += noise_level * np.random.randn(num_samples)

    scale = (1 << (bit_width - 1)) - 1
    return np.clip(np.round(sig * scale), -(1 << (bit_width - 1)), scale).astype(int)


def snr_db(original: np.ndarray, filtered: np.ndarray) -> float:
    """Compute Signal-to-Noise Ratio in dB."""
    noise = original.astype(float) - filtered.astype(float)
    sig_power = np.mean(original.astype(float) ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return float('inf')
    return 10 * np.log10(sig_power / noise_power)


def compute_fft(signal: np.ndarray, bit_width: int = 16) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the FFT magnitude spectrum.

    Returns
    -------
    (frequencies, magnitude_db) : tuple of np.ndarray
        Normalized frequencies [0, 0.5] and magnitude in dB.
    """
    scale = (1 << (bit_width - 1)) - 1
    sig_float = signal.astype(float) / scale
    N = len(sig_float)
    fft_result = np.fft.rfft(sig_float)
    magnitude = np.abs(fft_result) / N
    magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-10))
    frequencies = np.linspace(0, 0.5, len(magnitude))
    return frequencies, magnitude_db
