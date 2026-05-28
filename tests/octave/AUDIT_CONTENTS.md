# MATLAB Contents.m grouping audit

Same 52 functions as [`AUDIT.md`](AUDIT.md), reorganized to mirror the
upstream MATLAB toolbox's `Contents.m` -- the categories Minh Do used to
group the toolbox in November 2003. Useful if you're coming from the
MATLAB documentation and want to map each entry to its Python port.

For deep details (MATLAB-vs-Python source diff, per-function bug list,
parity-test names) see [`AUDIT.md`](AUDIT.md). This doc is a one-line-
per-function status board.

Status legend:
- ✓ bit-exact MATLAB parity (validated via Octave fixture)
- ✓ (smoke) covered by Python-only smoke tests; no MATLAB fixture needed
- ⚠ structurally validated; numerical comparison not applicable (random
  inputs, display output, or function not in MATLAB v2.0)

---

## Demos

The MATLAB demo scripts (`decdemo`, `nlademo`, `nlademo2`, `denoisedemo`)
are not ported one-to-one. Their decompose/reconstruct/NLA flow lives in
[`pycontourlet/demo.py`](../../pycontourlet/demo.py), invoked by
`python -m pycontourlet`. Validated end-to-end via the demo run plus
parity tests on every function it calls.

| MATLAB | Python equivalent | Status |
|---|---|---|
| `decdemo.m` | `pycontourlet/demo.py` (`run_demo`) | ✓ runs end-to-end; PR at 1e-14 |
| `nlademo.m` | section 3 of `run_demo` (NLA fractions) | ✓ runs end-to-end |
| `nlademo2.m` | not ported | not in scope |
| `denoisedemo.m` | not ported | not in scope; `pdfb_nest` is wired up if you want to build it |

## Main functions: contourlet pyramidal directional filter bank

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `pdfbdec` | `pycontourlet.pdfbdec` | `test_pdfbdec_pdfbrec_parity` | ✓ |
| `pdfbrec` | `pycontourlet.pdfbrec` | `test_pdfbdec_pdfbrec_parity` | ✓ |

Validated bit-exact on `R32` and `R64` square inputs with
`pfilt='9-7' + dfilt='pkva' + nlevs=[2,3]`.

## Retrieve filters by names

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `pfilters` | `pycontourlet.pfilters` | `test_pfilters_parity[9-7/5-3/Burt/pkva]` | ✓ (4 of 5 names) |
| `dfilters` | `pycontourlet.dfilters` | `test_dfilters_parity[8 names x 2 types]` | ✓ |
| `ldfilter` | `pycontourlet.ldfilter` | `test_ldfilter_parity[pkva/pkva6/pkva8/pkva12]` | ✓ |

`pfilters('maxflat')` is the only standard name not validated against
MATLAB -- it depends on the Wavelet Toolbox which Octave doesn't ship.
Python implements it directly and is covered by smoke PR tests.

## Utility functions of the contourlet transform

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `showpdfb` | `pycontourlet.showpdfb` | `test_showpdfb_*` (4 modes) | ✓ |
| `pdfb2vec` | `pycontourlet.pdfb2vec` | `test_pdfb2vec_parity` | ✓ |
| `vec2pdfb` | `pycontourlet.vec2pdfb` | (via `pdfb2vec` roundtrip) | ✓ (smoke) |
| `pdfb_tr` | `pycontourlet.pdfb_tr` | (smoke only) | ⚠ structural |
| `pdfb_nest` | `pycontourlet.pdfb_nest` | (Monte Carlo, no fixture) | ⚠ structural |

`showpdfb` had ~12 latent bugs and was unrunnable on develop until this
branch. Now bit-exact-equivalent to MATLAB across all 4 scale modes
(`auto1`, `auto2`, `auto3`, threshold-N).

## Laplacian pyramid

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `lpdec` | `pycontourlet.lpdec` | `test_lpdec_parity[3 shapes x 3 filters]` | ✓ |
| `lprec` | `pycontourlet.lprec` | `test_lprec_parity[3 shapes x 3 filters]` | ✓ |

PR at 1e-16 for all 5 standard pyramid filters.
(MATLAB Contents.m typo: lists `LPDEC` twice instead of `LPREC` for the
reconstruction entry.)

## Wavelet filter bank

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `wfb2dec` | `pycontourlet.wfb2dec` | `test_wfb2dec_wfb2rec_parity[sq32/sq64]` | ✓ |
| `wfb2rec` | `pycontourlet.wfb2rec` | `test_wfb2dec_wfb2rec_parity[sq32/sq64]` | ✓ |

Used inside `pdfbdec` only when an entry of `nlevs` is 0.

## Directional filter bank

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `dfbdec` | `pycontourlet.dfbdec` | `test_dfbdec_parity[2 shapes x cd/9-7 x 3 levels]` | ✓ |
| `dfbrec` | `pycontourlet.dfbrec` | (rec asserted in `test_dfbdec_parity`) | ✓ |
| `dfbdec_l` | `pycontourlet.dfbdec_l` | `test_dfbdec_l_parity[2 shapes x 3 levels]` | ✓ |
| `dfbrec_l` | `pycontourlet.dfbrec_l` | (rec asserted in `test_dfbdec_l_parity`) | ✓ |
| `dfbimage` | `pycontourlet.dfbimage` | (via `showpdfb`) | ✓ (rewritten this branch) |

`dfbimage` was unrunnable (`l*m/2` float division, wrong subband pairing,
off-by-one indices). Rewritten and validated through `showpdfb` parity.

## Two-channel 2D filter banks (used in the DFB)

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `fbdec` | `pycontourlet.fbdec` | (via `dfbdec` parity) | ✓ |
| `fbdec_l` | `pycontourlet.fbdec_l` | (via `dfbdec_l` parity) | ✓ |
| `fbrec` | `pycontourlet.fbrec` | (via `dfbrec` parity) | ✓ |
| `fbrec_l` | `pycontourlet.fbrec_l` | (via `dfbrec_l` parity) | ✓ |

`fbdec`/`fbrec` had a `R[type2] * shift` elementwise-vs-matmul bug in
the parallelogram (`type1='p'`) branch. Fixed; not exercised by any
caller in the toolbox but now correct.

## Multidimensional filtering (used in building block filter banks)

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `sefilter2` | `pycontourlet.sefilter2` | `test_sefilter2_parity[3 shapes]` | ✓ |
| `efilter2` | `pycontourlet.efilter2` | `test_efilter2_parity[3 shapes]` | ✓ |
| `extend2` | `pycontourlet.extend2` | `test_extend2_parity[3 shapes x 3 modes]` | ✓ |

`extend2` had a banker's-vs-MATLAB rounding bug for odd-row inputs in
`qper_row`/`qper_col` modes; fixed. `sefilter2` had a `lf2 = ... f1 ...`
typo (used `f1` for both axis lengths); fixed.

## Multidimensional sampling (used in building block filter banks)

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `pdown` | `pycontourlet.pdown` | `test_pdown_parity[3 shapes x 4 types]` | ✓ |
| `pup` | `pycontourlet.pup` | `test_pup_parity[3 shapes x 4 types]` | ✓ |
| `qdown` | `pycontourlet.qdown` | `test_qdown_parity[3 shapes x 4 types]` | ✓ |
| `qup` | `pycontourlet.qup` | `test_qup_parity[3 shapes x 4 types]` | ✓ |
| `qupz` | `pycontourlet.qupz` | `test_qupz_parity[3 shapes x 2 types]` | ✓ |
| `dup` | `pycontourlet.dup` | `test_dup_parity_*` (zero/min/rect) | ✓ |
| `resamp` | `pycontourlet.resamp` | `test_resamp_parity[3 shapes x 4 types]` | ✓ |
| `resampz` | `pycontourlet.resampz` | `test_resampz_parity[3 shapes x 4 types]` | ✓ |
| `resampc` | `pycontourlet.resampc` | `test_resampc_parity[3 shapes x 2 types x 2 shifts]` | ✓ |

`qdown.type1r` had a Python indentation crash (the inner function's
body sat outside the def). Several `pdown`/`pup`/`qup` `type0`/`type1r`
phase==1 branches used `len(arr)` (rows) where MATLAB indexed columns.
All fixed and parity-validated on a non-square 16x24 input.

`resampc` is the MEX file in MATLAB. The Octave parity build requires
recompiling it from `resampc.c` (one-line patch: add `#include
<string.h>`); see [`README.md`](README.md). Python has only the `'per'`
extmod implemented, matching the C source.

## Polyphase decomposition (used in the ladder structure implementation)

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `qpdec` | `pycontourlet.qpdec` | `test_qpdec_parity[3 shapes x 4 types]` | ✓ |
| `qprec` | `pycontourlet.qprec` | `test_qprec_parity[3 shapes x 4 types]` | ✓ |
| `ppdec` | `pycontourlet.ppdec` | `test_ppdec_parity[3 shapes x 4 types]` | ✓ |
| `pprec` | `pycontourlet.pprec` | `test_pprec_parity[3 shapes x 4 types]` | ✓ |

`qpdec`/`qprec` switch dicts had a `'2r': type2c` typo: the entire `2r`
quincunx variant silently routed to the column code. Fixed. Several
`type0`/`type1r` phase==1 branches had the same `len(arr)`-vs-`shape[1]`
bug as the sampling primitives. All fixed.

## Support functions to avoid visual distortion (used in DFB)

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `backsamp` | `pycontourlet.backsamp` | (via `dfbdec` parity) | ✓ |
| `rebacksamp` | `pycontourlet.rebacksamp` | (via `dfbrec` parity) | ✓ |

Type/phase mappings hand-checked function-by-function in
[`AUDIT.md`](AUDIT.md).

## Support functions for generating filters

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `ffilters` | `pycontourlet.ffilters` | `test_ffilters_parity` | ✓ |
| `ld2quin` | `pycontourlet.ld2quin` | `test_ld2quin_parity` | ✓ |
| `mctrans` | `pycontourlet.mctrans` | `test_mctrans_parity` | ✓ |
| `modulate2` | `pycontourlet.modulate2` | `test_modulate2_parity[r/c/b]` | ✓ |

`ld2quin` had off-by-one MATLAB→Python index translations on `h0` and
`h1` updates plus a `n = lf/2.0` (float) used as an array index. All
fixed. `mctrans` had the same float-index issue. `modulate2` was
unrunnable due to `np.arange(0, s[:, 0])` rejecting array args; rewritten.

## Other support functions

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `computescale` | `pycontourlet.computescale` | (via `showpdfb` parity) | ✓ |
| `smthborder` | `pycontourlet.smthborder` (alias) / `smothborder` | (smoke only) | ✓ (smoke) |
| `SNR` | `pycontourlet.SNR` (alias) / `snr` | `test_snr_parity` | ✓ |

`computescale` had three masked bugs that surfaced when `showpdfb` was
fixed: `sum = 0` shadowed the builtin (NameError when reused later),
`math.sqrt` after `import math` had been removed, and `scales =
np.zeros((1,2))` then `scales[1] = ...` would IndexError. Plus the
`'abs'`-mode bound clamping diverged from MATLAB (Python clamped both
ends to data range; MATLAB clamps lower to 0 and lets upper exceed
data max). All fixed in the showpdfb-parity commit.

## Undocumented in Contents.m

The following helpers exist in the MATLAB toolbox but are not listed in
`Contents.m`:

| MATLAB | Python | Parity test | Status |
|---|---|---|---|
| `reverse2` | `pycontourlet.reverse2` | `test_reverse2_parity` | ✓ |

## Python-only additions (not in MATLAB v2.0 toolbox)

| Python | Source | Status |
|---|---|---|
| `dmaxflat` | a later toolbox release | smoke-tested via DFB |
| `getPerIndices` | extracted from `extend2.m`'s nested helper | (via `extend2` parity) |
| `rowfiltering` | extracted from `wfb2dec.m`'s nested helper | (via wavelet parity) |

## Summary

- **52 functions total** across all categories.
- **47 functions** with bit-exact MATLAB parity tests.
- **5 functions** validated structurally only:
  - `pdfb_nest` (Monte Carlo, random inputs)
  - `pdfb_tr` (depends on parity-validated `vec2pdfb`)
  - `dmaxflat` (Python-only, not in v2.0)
  - `pfilters('maxflat')` (depends on Wavelet Toolbox)
  - `smthborder` / `smothborder` (no MATLAB fixture; smoke-tested for shape and interior preservation)
- **Display helpers** (`computescale`, `dfbimage`, `showpdfb`) all
  validated bit-exact via showpdfb parity tests.

Total test count after multi-shape parameter expansion: **328**
(94 smoke + 234 parity), all passing.
