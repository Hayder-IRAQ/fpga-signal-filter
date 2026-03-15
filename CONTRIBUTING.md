# Contributing to FPGA Signal Filter

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fpga-signal-filter.git
   cd fpga-signal-filter
   ```
3. **Install** dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```
4. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_fir.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Code Style

- Follow PEP 8 conventions
- Use type hints where practical
- Write docstrings for all public classes and methods (NumPy style)
- Keep lines under 100 characters

### Adding a New Filter

1. Create `src/your_filter.py` with:
   - A class with `rtl()`, `simulate()`, `to_verilog()`, and `to_vhdl()` methods
   - Proper docstrings and type hints
2. Add tests in `tests/test_your_filter.py`
3. Add an example in `examples/`
4. Update `src/__init__.py` to export the new class
5. Update README.md

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add Butterworth IIR filter design
fix: correct FIR coefficient quantization overflow
docs: update API reference for CIC filter
test: add edge case tests for moving average
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add a clear description of what your PR does
4. Reference any related issues

## Reporting Issues

When reporting bugs, please include:
- Python version
- MyHDL version
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
