# pySPINS

Interactive Stern-Gerlach quantum spin simulation — a Python/PySide6 port of the
[OSP SPINS](https://sites.science.oregonstate.edu/~mcintyre/ph425/spins/index_SPINS_OSP.html)
program by David McIntyre (Oregon State University).

Students build Stern-Gerlach apparatus by dragging and connecting components on a canvas, then
fire spin-1/2 or spin-1 particles and observe probabilistic quantum outcomes.

---

## Student Install

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell

# 2. Install pySPINS
pip install pyspins

# 3. Launch
pyspins
```

On Windows, `pyspins.exe` is placed in `.venv\Scripts\`. No other steps are needed.

---

## Developer Install

```bash
git clone https://github.com/rlongland/pySPINS.git
cd pySPINS
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pyspins
```

Run the test suite:

```bash
pytest
```

---

## License

pySPINS is released under the [MIT License](LICENSE) — an independent reimplementation
written from published descriptions of the OSP SPINS program, containing no code from
the original.

---

## Credits

Based on the SPINS Java applet originally written by D. V. Schroeder
(*Am. J. Phys.* **61**, 798, 1993) and extended by David McIntyre at Oregon State University
for the PH425 "Spin and Quantum Measurement" course.
