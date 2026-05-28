# pycontourlet

Python 3 port of Minh Do and Duncan Po's MATLAB **Contourlet Toolbox**
(v2.0, November 2003). The contourlet transform is a multiscale,
multi-direction image representation built from a Laplacian pyramid plus
a directional filter bank.

Upstream MATLAB toolbox (the reference implementation this port is
validated against):
<https://minhdo.ece.illinois.edu/software/contourlet_toolbox.tar>

## Install

```sh
pip install -e .
```

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

- `tests/test_smoke.py` -- 94 invariant + dispatch tests; no Octave.
- `tests/test_octave_parity.py` -- 103 numerical-equivalence tests
  against the original MATLAB toolbox via Octave. See
  [tests/octave/README.md](tests/octave/README.md) for how to regenerate
  fixtures.

## License

GPL-2.0, matching the upstream MATLAB toolbox.
