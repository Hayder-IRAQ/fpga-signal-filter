"""
FPGA Signal Filter Library
===========================
A Python-based HDL library for designing, simulating, and synthesizing
digital signal filters on FPGAs using MyHDL.
"""

__version__ = "1.0.0"
__author__ = "FPGA Signal Filter Contributors"

from .fir_filter import FIRFilter
from .iir_filter import IIRFilter
from .moving_average import MovingAverageFilter
from .cic_filter import CICFilter
from .filter_chain import FilterChain
from .coefficient_gen import CoefficientGenerator

__all__ = [
    "FIRFilter",
    "IIRFilter",
    "MovingAverageFilter",
    "CICFilter",
    "FilterChain",
    "CoefficientGenerator",
]
