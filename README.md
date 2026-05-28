# pycontourlet

[![CI](https://github.com/itsmazay/pycontourlet/actions/workflows/ci.yml/badge.svg)](https://github.com/itsmazay/pycontourlet/actions/workflows/ci.yml)

Python 3 port of the **Contourlet Transform**, originally implemented
by Minh Do and Duncan Po as the MATLAB Contourlet Toolbox v2.0
(November 2003). The contourlet transform is a multiscale,
multi-direction image representation built from a Laplacian pyramid plus
a directional filter bank.

Upstream MATLAB toolbox (the reference implementation this port is
validated against):
<https://minhdo.ece.illinois.edu/software/contourlet_toolbox.tar>

## Install

We recommend installing into a virtual environment so the dependencies
don't clash with anything else on your system:

```sh
python3 -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -e .
```

Run `deactivate` to leave the venv. To recreate it later, delete
`.venv/` and re-run the three commands above.

## Quick start

```python
import numpy as np
import pycontourlet as pc

x = np.random.default_rng(0).standard_normal((64, 64))

# Forward + inverse PDFB
coeffs = pc.pdfbdec(x, pfilt='9-7', dfilt='pkva', nlevs=[2, 3])
xrec = pc.pdfbrec(coeffs, pfilt='9-7', dfilt='pkva')
print(pc.snr(x, xrec))   # > 250 dB (perfect reconstruction)
```

## Demo

```sh
python -m pycontourlet                       # save plots to cwd
pycontourlet-demo --out-dir /tmp/demo --show # interactive
```

The demo runs forward PDFB, inverse PDFB, and nonlinear approximation
(retain 5 / 2.5 / 1 % of coefficients) on `barbara.png`.

## Tests

```sh
pip install -e .[dev]
pytest tests/
```

Two suites:

- `tests/test_smoke.py` — 94 invariant + dispatch tests; no Octave.
- `tests/test_octave_parity.py` — 234 numerical-equivalence tests
  against the original MATLAB toolbox via Octave. See
  [tests/octave/README.md](tests/octave/README.md) for how to regenerate
  fixtures.

## Documentation

- [`CHANGELOG.md`](CHANGELOG.md) — version history.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev setup and how to run the
  full test suite (including MATLAB parity).
- [`tests/octave/AUDIT.md`](tests/octave/AUDIT.md) — function-by-function
  audit, organized bottom-up by dependency.
- [`tests/octave/AUDIT_CONTENTS.md`](tests/octave/AUDIT_CONTENTS.md) —
  same audit reorganized by the upstream MATLAB `Contents.m` grouping.

## License

GPL-2.0, matching the upstream MATLAB toolbox.
