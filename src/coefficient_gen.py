"""
Coefficient Generator — Design Filter Coefficients from Specs
==============================================================
Generate fixed-point filter coefficients for FPGA implementation.
Supports low-pass, high-pass, band-pass, and band-stop designs.
"""

import numpy as np
from typing import List, Tuple


class CoefficientGenerator:
    """
    Static methods to generate fixed-point filter coefficients.

    All methods return integer coefficients scaled for the target bit width
    using Q-format fixed-point representation.
    """

    @staticmethod
    def _quantize(coeffs: np.ndarray, bit_width: int) -> List[int]:
        """
        Quantize floating-point coefficients to fixed-point integers.

        Parameters
        ----------
        coeffs : np.ndarray
            Floating-point coefficients (max absolute value ≤ 1.0).
        bit_width : int
            Target bit width (signed).

        Returns
        -------
        List[int] of fixed-point coefficients.
        """
        scale = (1 << (bit_width - 1)) - 1
        quantized = np.round(coeffs * scale).astype(int)
        max_val = (1 << (bit_width - 1)) - 1
        min_val = -(1 << (bit_width - 1))
        quantized = np.clip(quantized, min_val, max_val)
        return quantized.tolist()

    @staticmethod
    def lowpass(num_taps: int = 16, cutoff_freq: float = 0.25,
                bit_width: int = 16, window: str = 'hamming') -> List[int]:
        """
        Design a low-pass FIR filter using the window method.

        Parameters
        ----------
        num_taps : int
            Number of filter taps (odd recommended for Type I).
        cutoff_freq : float
            Normalized cutoff frequency (0 to 1, where 1 = Nyquist).
        bit_width : int
            Coefficient bit width.
        window : str
            Window function: 'hamming', 'hann', 'blackman', 'rectangular'.

        Returns
        -------
        List[int] of quantized coefficients.
        """
        n = np.arange(num_taps)
        mid = (num_taps - 1) / 2.0
        wc = cutoff_freq * np.pi

        # Ideal sinc filter
        with np.errstate(divide='ignore', invalid='ignore'):
            h = np.where(
                n == mid,
                wc / np.pi,
                np.sin(wc * (n - mid)) / (np.pi * (n - mid))
            )

        # Apply window
        h *= CoefficientGenerator._get_window(window, num_taps)

        # Normalize
        h /= np.max(np.abs(h)) if np.max(np.abs(h)) > 0 else 1.0

        return CoefficientGenerator._quantize(h, bit_width)

    @staticmethod
    def highpass(num_taps: int = 16, cutoff_freq: float = 0.25,
                 bit_width: int = 16, window: str = 'hamming') -> List[int]:
        """
        Design a high-pass FIR filter.

        Uses spectral inversion of the equivalent low-pass filter.
        """
        lp_coeffs = CoefficientGenerator.lowpass(
            num_taps, cutoff_freq, bit_width, window
        )
        # Spectral inversion
        scale = (1 << (bit_width - 1)) - 1
        hp = [-c for c in lp_coeffs]
        mid = num_taps // 2
        hp[mid] += scale
        return hp

    @staticmethod
    def bandpass(num_taps: int = 32, low_freq: float = 0.2,
                 high_freq: float = 0.4, bit_width: int = 16,
                 window: str = 'hamming') -> List[int]:
        """
        Design a band-pass FIR filter.

        Combines a low-pass at high_freq with a high-pass at low_freq.
        """
        n = np.arange(num_taps)
        mid = (num_taps - 1) / 2.0
        wl = low_freq * np.pi
        wh = high_freq * np.pi

        with np.errstate(divide='ignore', invalid='ignore'):
            h = np.where(
                n == mid,
                (wh - wl) / np.pi,
                (np.sin(wh * (n - mid)) - np.sin(wl * (n - mid))) / (np.pi * (n - mid))
            )

        h *= CoefficientGenerator._get_window(window, num_taps)
        h /= np.max(np.abs(h)) if np.max(np.abs(h)) > 0 else 1.0

        return CoefficientGenerator._quantize(h, bit_width)

    @staticmethod
    def bandstop(num_taps: int = 32, low_freq: float = 0.2,
                 high_freq: float = 0.4, bit_width: int = 16,
                 window: str = 'hamming') -> List[int]:
        """
        Design a band-stop (notch) FIR filter.

        Spectral inversion of the equivalent band-pass filter.
        """
        bp = CoefficientGenerator.bandpass(
            num_taps, low_freq, high_freq, bit_width, window
        )
        scale = (1 << (bit_width - 1)) - 1
        bs = [-c for c in bp]
        mid = num_taps // 2
        bs[mid] += scale
        return bs

    @staticmethod
    def iir_lowpass(cutoff_freq: float = 0.2,
                    q_factor: float = 0.707,
                    bit_width: int = 16) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        """
        Design a second-order IIR low-pass filter (biquad).

        Parameters
        ----------
        cutoff_freq : float
            Normalized cutoff frequency (0 to 1).
        q_factor : float
            Quality factor (0.707 = Butterworth).
        bit_width : int
            Coefficient bit width.

        Returns
        -------
        (b_coeffs, a_coeffs) : tuple of int tuples
            b = (b0, b1, b2), a = (a1, a2)
        """
        w0 = cutoff_freq * np.pi
        alpha = np.sin(w0) / (2 * q_factor)

        b0 = (1 - np.cos(w0)) / 2
        b1 = 1 - np.cos(w0)
        b2 = (1 - np.cos(w0)) / 2
        a0 = 1 + alpha
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha

        # Normalize by a0
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a1, a2]) / a0

        scale = (1 << (bit_width - 1)) - 1
        b_int = tuple(int(round(x * scale)) for x in b)
        a_int = tuple(int(round(x * scale)) for x in a)

        return b_int, a_int

    @staticmethod
    def iir_highpass(cutoff_freq: float = 0.2,
                     q_factor: float = 0.707,
                     bit_width: int = 16) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        """Design a second-order IIR high-pass biquad filter."""
        w0 = cutoff_freq * np.pi
        alpha = np.sin(w0) / (2 * q_factor)

        b0 = (1 + np.cos(w0)) / 2
        b1 = -(1 + np.cos(w0))
        b2 = (1 + np.cos(w0)) / 2
        a0 = 1 + alpha
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha

        b = np.array([b0, b1, b2]) / a0
        a = np.array([a1, a2]) / a0

        scale = (1 << (bit_width - 1)) - 1
        b_int = tuple(int(round(x * scale)) for x in b)
        a_int = tuple(int(round(x * scale)) for x in a)

        return b_int, a_int

    @staticmethod
    def _get_window(window_type: str, length: int) -> np.ndarray:
        """Get a window function by name."""
        windows = {
            'hamming': np.hamming,
            'hann': np.hanning,
            'blackman': np.blackman,
            'rectangular': np.ones,
        }
        func = windows.get(window_type.lower(), np.hamming)
        return func(length)

    @staticmethod
    def frequency_response(coefficients: List[int], bit_width: int = 16,
                           num_points: int = 512) -> dict:
        """
        Compute the frequency response of FIR coefficients.

        Returns
        -------
        dict with 'frequency' (0..π normalized), 'magnitude_db', 'phase_rad'
        """
        scale = (1 << (bit_width - 1)) - 1
        h = np.array(coefficients, dtype=float) / scale

        w = np.linspace(0, np.pi, num_points)
        H = np.zeros(num_points, dtype=complex)
        for k, freq in enumerate(w):
            for n, coeff in enumerate(h):
                H[k] += coeff * np.exp(-1j * freq * n)

        mag = np.abs(H)
        mag_db = 20 * np.log10(np.maximum(mag, 1e-10))
        phase = np.angle(H)

        return {
            'frequency': w / np.pi,  # Normalized 0 to 1
            'magnitude_db': mag_db,
            'phase_rad': phase,
        }
