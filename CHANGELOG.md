# Changelog

All notable changes to `pycontourlet` are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-05-28

First release of the audited Python 3 port. Validates bit-exact
equivalence to Minh Do and Duncan Po's MATLAB Contourlet Toolbox v2.0.

### Added
- Pip-installable package: `pip install -e .` with `pyproject.toml`,
  `pycontourlet/__init__.py` re-exporting the full public API, and a
  `pycontourlet-demo` console script entry point.
- `python -m pycontourlet` and `examples/decdemo.py` end-to-end demo
  combining decompose/reconstruct/NLA from MATLAB's `decdemo.m` and
  `nlademo.m`. Saves three PNGs by default.
- `pycontourlet.pdfb_nest`: Monte-Carlo noise std-dev estimator in the
  PDFB domain. Ported from MATLAB toolbox; new in this branch.
- `pycontourlet.pdfb_tr`: truncate a PDFB output to its N most
  significant coefficients. Ported from MATLAB toolbox; new in this
  branch.
- MATLAB-canonical aliases: `pycontourlet.SNR` (= `snr`) and
  `pycontourlet.smthborder` (= `smothborder`).
- `dfilters` filter names: `pkva6`, `pkva8`, `pkva12` (MATLAB-canonical
  aliases routing to the existing `filterPkva`), `5-3`, `5/3` (new
  `filter53` helper mirroring the existing `filter79`), `9-7`, `9/7`
  (aliases to `cd`).
- 94-test pytest smoke suite covering perfect reconstruction, dispatch
  branches, and roundtrips. Runs without Octave.
- 234-test Octave-based parity suite asserting bit-exact MATLAB
  equivalence across every public function. Multi-shape parametrization
  (square 32×32, square 64×64, rectangular 16×24) catches
  shape-dependent bugs. Validation script at
  `tests/octave/generate_fixtures.m`.
- Function-by-function audit docs: `tests/octave/AUDIT.md` (bottom-up
  by dependency) and `tests/octave/AUDIT_CONTENTS.md` (mirrors the
  upstream MATLAB `Contents.m` grouping).

### Fixed (44 latent bugs found during the deep review)
- Module wouldn't import or run at all: 22 bare numpy names referenced
  unqualified, plus crash bugs in `resampc` (parameter shadowing
  `type()`), `pdfb2vec` (undefined `a`), `qdown.type1r` (broken
  indentation), `vec2pdfb` (`.nonzero()` count, layer-count derivation),
  `modulate2` (`np.arange` rejecting array args), `dfbimage` (float
  division for shape, wrong subband pairing), `showpdfb` (NameError on
  `isnumeric`/`strcmp`/`double`).
- Wrong numerical output silently masked by callers that happened to
  not hit the buggy branch: `len(arr)` (rows) used as a column index in
  the phase==1 branch of `pdown.type0`, `pup.type0`, `qup.type1r`,
  `qpdec.type1r`, `qprec.type1r`, `ppdec.type0`, `pprec.type0`. The
  `dup` minimum-phase branch indexed both axes with `step[0]`. The
  `qpdec`/`qprec` switch dicts had `'2r': type2c` typos -- silent
  reconstruction failure for the `2r` quincunx variant.
- Off-by-one MATLAB-1-based to Python-0-based index translations in
  `ld2quin` (`h0`/`h1` updates) and `pfilters.filterPkva` (`h`/`g`
  midpoint).
- `extend2` `qper_row`/`qper_col` modes used Python's banker's
  rounding; MATLAB rounds half away from zero. Fixed to `(rx+1)//2`.
- `extend2` boundary cast: floor/ceil floats from `sefilter2` broke
  numpy slicing.
- `fbdec`/`fbrec`: `R[type2] * shift` was elementwise; MATLAB matrix-
  multiplies. Replaced with `@`.
- `sefilter2`: `lf2 = ... f1 ...` typo (used `f1` for both axes).
- `dfilters` cleanup: removed `pkva-half4`/`6`/`8` entries that
  referenced an undefined `ldfilterhalf()` and crashed on call. Fixed
  `srtring.lower(...)` typo.
- `mctrans`: `n = (size(b)-1)/2.0` float used as range bound and slice
  index.
- `computescale`: `sum = 0` shadowed builtin (NameError when reused),
  `math.sqrt` after `import math` had been removed,
  `np.zeros((1,2))[1]` IndexError. Plus the `'abs'`-mode bound clamping
  diverged from MATLAB (MATLAB clamps lower to 0 and lets upper exceed
  data max; Python clamped both ends to data range).
- `showpdfb`: rewritten end-to-end. Now bit-exact-equivalent to MATLAB
  across all four scale modes (`auto1`, `auto2`, `auto3`, threshold-N).

### Changed
- `develop` branch is now the canonical Python 3 implementation.
- Demo `DEFAULT_NLEVELS` changed to `(2, 3, 4)` from `(0, 0, 4, 5)` for
  sharper coefficient visualization (trade-off: 0.5 dB lower NLA SNR).

[Unreleased]: https://github.com/itsmazay/pycontourlet/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/itsmazay/pycontourlet/releases/tag/v0.2.0
