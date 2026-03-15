"""
FPGA Signal Filter — Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fpga-signal-filter",
    version="1.0.0",
    author="FPGA Signal Filter Contributors",
    description="Python HDL library for FPGA digital signal filters using MyHDL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/fpga-signal-filter",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "myhdl>=0.11",
        "numpy>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "matplotlib>=3.5.0",
            "scipy>=1.7.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="fpga hdl filter fir iir myhdl verilog vhdl dsp signal-processing",
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/fpga-signal-filter/issues",
        "Source": "https://github.com/YOUR_USERNAME/fpga-signal-filter",
        "Documentation": "https://github.com/YOUR_USERNAME/fpga-signal-filter/tree/main/docs",
    },
)
