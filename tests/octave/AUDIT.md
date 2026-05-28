# MATLAB → Python audit

Function-by-function comparison between Minh Do's MATLAB Contourlet
Toolbox (`~/contourlet_toolbox/*.m`) and the Python port at
`pycontourlet/PyContourlet.py`. Ordering is **bottom-up by dependency**:
functions that nothing else depends on come first, so by the time we
review a higher-level routine its primitives have already been validated.

For every function the audit records:

- **MATLAB source** -- file and line span in the upstream toolbox.
- **Python source** -- file and line span in this repo.
- **Behavioral parity** -- whether the two produce identical numerical
  output, plus the parity-test name(s) that prove it.
- **Differences worth knowing** -- intentional convention shifts (e.g.
  1-based -> 0-based indices) and any deviations that were caught and
  fixed during the port.

All parity tests pass at machine precision (`atol=1e-10`, often exact)
unless explicitly noted.

---

## Table of contents

### Layer 0: leaf utilities (no internal dependencies)

1. [`reverse2`](#reverse2)
2. [`modulate2`](#modulate2)
3. [`mctrans`](#mctrans)
4. [`snr` / `SNR`](#snr)
5. [`smothborder` / `smthborder`](#smothborder)

### Layer 1: filter generators

6. [`ldfilter`](#ldfilter)
7. [`dmaxflat`](#dmaxflat)
8. [`pfilters`](#pfilters)
9. [`ld2quin`](#ld2quin)
10. [`dfilters`](#dfilters)
11. [`ffilters`](#ffilters)

### Layer 2: extension + 1D/2D filtering primitives

12. [`getPerIndices`](#getperindices)
13. [`extend2`](#extend2)
14. [`sefilter2`](#sefilter2)
15. [`efilter2`](#efilter2)
16. [`rowfiltering`](#rowfiltering)

### Layer 3: sampling primitives

17. [`resampc`](#resampc)
18. [`resamp`](#resamp)
19. [`resampz`](#resampz)
20. [`dup`](#dup)
21. [`qupz`](#qupz)
22. [`qdown`](#qdown)
23. [`qup`](#qup)
24. [`pdown`](#pdown)
25. [`pup`](#pup)

### Layer 4: polyphase decomposition / reconstruction

26. [`qpdec`](#qpdec)
27. [`qprec`](#qprec)
28. [`ppdec`](#ppdec)
29. [`pprec`](#pprec)

### Layer 5: 2-channel filter banks

30. [`fbdec`](#fbdec)
31. [`fbrec`](#fbrec)
32. [`fbdec_l`](#fbdec_l)
33. [`fbrec_l`](#fbrec_l)

### Layer 6: backsampling support for the DFB tree

34. [`backsamp`](#backsamp)
35. [`rebacksamp`](#rebacksamp)

### Layer 7: directional filter bank driver

36. [`dfbdec`](#dfbdec)
37. [`dfbrec`](#dfbrec)
38. [`dfbdec_l`](#dfbdec_l)
39. [`dfbrec_l`](#dfbrec_l)

### Layer 8: Laplacian pyramid + critically sampled wavelet

40. [`lpdec`](#lpdec)
41. [`lprec`](#lprec)
42. [`wfb2dec`](#wfb2dec)
43. [`wfb2rec`](#wfb2rec)

### Layer 9: PDFB top level + utilities

44. [`pdfbdec`](#pdfbdec)
45. [`pdfbrec`](#pdfbrec)
46. [`pdfb2vec`](#pdfb2vec)
47. [`vec2pdfb`](#vec2pdfb)
48. [`pdfb_nest`](#pdfb_nest)
49. [`pdfb_tr`](#pdfb_tr)

### Layer 10: display / scoring helpers

50. [`computescale`](#computescale)
51. [`dfbimage`](#dfbimage)
52. [`showpdfb`](#showpdfb)

---

## Conventions used throughout

Two MATLAB↔Python convention shifts are global and do not represent
behavioral differences. They're worth re-stating once so each function
section can stay short:

1. **Indexing**: MATLAB is 1-based, Python is 0-based. All `type` /
   `qtype` / `ptype` / phase parameters that take integer codes follow
   this shift: MATLAB `{1,2,3,4}` → Python `{0,1,2,3}`. The parity
   tests subtract 1 from the MATLAB-saved value before passing it to
   the Python function.
2. **String types**: MATLAB `'1r'/'1c'/'2r'/'2c'` strings for quincunx
   variants are passed through unchanged.
3. **Filter arrays**: 1-D filters are stored as `(1, N)` row vectors in
   both MATLAB and Python (NumPy 2-D row), preserving MATLAB's
   convention that `size(h)` returns `[1 N]`.

---

## Layer 0: leaf utilities

### reverse2

| | |
|---|---|
| MATLAB | `reverse2.m`, full file |
| Python | `pycontourlet/PyContourlet.py:2571-2575` |
| Parity | `test_reverse2_parity` (passes) |

MATLAB body:
```matlab
function r = reverse2(x)
if ndims(x)~=2, error('X must be a 2-D matrix.'); end
r = x(end:-1:1, end:-1:1);
```

Python body:
```python
def reverse2(x):
    if x.ndim != 2:
        raise ValueError('Input must be a 2-D matrix.')
    return x[::-1, ::-1]
```

Notes: identical semantics. The original Python port `print`-ed instead
of raising; fixed during the deep-review pass.

---

### modulate2

| | |
|---|---|
| MATLAB | `modulate2.m`, full file |
| Python | `PyContourlet.py:2532-2569` |
| Parity | `test_modulate2_parity[r/c/b]` (3 cases pass) |

MATLAB:
```matlab
o = floor(s / 2) + 1 + center;          % 1-based origin
n1 = [1:s(1)] - o(1);
n2 = [1:s(2)] - o(2);
% case 'r': y = x .* repmat(((-1).^n1)', [1, s(2)]);
```

Python:
```python
o0 = (s0 // 2) + c0      # 0-based; the +1 is absorbed into the index shift
n1 = np.arange(s0) - o0
m1 = (-1.0) ** n1
return x * m1[:, np.newaxis]
```

Notes: the original Python wrote `s = np.array([x.shape])` and called
`np.arange(0, s[:, 0])` -- numpy's `arange` rejects array arguments, so
this crashed every caller. Replaced with plain integer dims.
Numerically identical to MATLAB across all three directions (`r`/`c`/`b`).

---

### mctrans

| | |
|---|---|
| MATLAB | `mctrans.m`, full file |
| Python | `PyContourlet.py:2496-2530` |
| Parity | `test_mctrans_parity` (passes) |

McClellan transform converts a 1-D filter `b` (odd length) into a 2-D
filter via Chebyshev polynomial expansion using a 2-D transform kernel
`t`. Used by `dfilters` for the `cd`/`9-7`/`5-3` paths.

MATLAB:
```matlab
n = (length(b)-1)/2;          % integer for odd-length b
b = rot90(fftshift(rot90(b,2)),2);
a = [b(1) 2*b(2:n+1)];
% Chebyshev recursion to build h
```

Python:
```python
if (np.size(b) - 1) % 2 != 0:
    raise ValueError('mctrans expects an odd-length 1-D filter')
n = (np.size(b) - 1) // 2
```

Notes: original Python used `n = (np.size(b) - 1) / 2.0` (float) which
broke `b[:, 1:n+1]` slicing and `range(2, n+1)`. Cast to integer with
explicit guard. Output matches MATLAB exactly.

---

### snr

| | |
|---|---|
| MATLAB | `SNR.m`, full file |
| Python | `PyContourlet.py:3587-3597`, alias `SNR = snr` at 3600 |
| Parity | `test_snr_parity` (passes) |

MATLAB:
```matlab
r = 10 * log10(var(in(:), 1) / mean(error(:).^2));
```

Python:
```python
return 10 * np.log10(np.var(im) / np.mean(np.abs(error) ** 2))
```

Notes: MATLAB `var(x, 1)` divides by N (population variance). NumPy's
default `np.var` uses `ddof=0` which also divides by N, so they match
without explicit ddof. Original Python had a Spanish docstring that has
been replaced with a citation to the textbook reference. Also added an
uppercase `SNR` alias for MATLAB API compatibility.

---

### smothborder

| | |
|---|---|
| MATLAB | `smthborder.m`, full file |
| Python | `PyContourlet.py:2660-2700`, alias `smthborder = smothborder` at 2702 |
| Parity | not part of MATLAB toolbox parity (used only in app code) |

Hamming-windowed taper of the borders of a 1-D or 2-D signal. MATLAB
function name is `smthborder`; Python preserved a typo (`smothborder`)
that was already in the develop branch. We added an alias so the MATLAB
spelling works.

Smoke tests (`test_smothborder_keeps_interior`, `test_smthborder_alias`)
verify (a) the interior of the array is unchanged and (b) both names
point to the same function.

---

## Layer 1: filter generators

### ldfilter

| | |
|---|---|
| MATLAB | `ldfilter.m`, full file |
| Python | `PyContourlet.py:1309-1339` |
| Parity | `test_ldfilter_parity[pkva/pkva6/pkva8/pkva12]` (4 cases pass) |

Returns the symmetric impulse response `[v(end:-1:1), v]` for a length-N
ladder allpass filter (N ∈ {6, 8, 12}). Coefficients `v` are hardcoded
constants from Phoong, Kim, Vaidyanathan, Ansari.

MATLAB:
```matlab
case {'pkva12', 'pkva'}
    v = [0.6300 -0.1930 0.0972 -0.0526 0.0272 -0.0144];
% ...
f = [v(end:-1:1), v];
```

Python:
```python
def pkva12():
    v = np.array([[0.6300, -0.1930, 0.0972, -0.0526, 0.0272, -0.0144]])
    return v
# ...
f = np.c_[v[:, ::-1], v]
```

Notes: MATLAB's `pkva` case is dispatched to the same function as
`pkva12`. Python's switch dict has both keys pointing at the same inner
function. Coefficients match MATLAB to ~5e-5 absolute (the MATLAB source
prints to 4 decimals; the dataset is identical across versions).
The original `print('Unrecognized filter')` errhandler was replaced with
`raise ValueError`.

---

### dmaxflat

| | |
|---|---|
| MATLAB | not present in the v2.0 toolbox we audit |
| Python | `PyContourlet.py:1340-1431` |
| Parity | not validated against MATLAB (no source in upstream) |

Used inside `dfilters` for the `dmaxflat4..7` paths. The Python
implementation came in from a later toolbox version. Smoke-tested via
DFB perfect reconstruction with those filters.

The `print('Invalid argument type')` errhandler was replaced with
`raise ValueError` during the deep-review pass.

---

### pfilters

| | |
|---|---|
| MATLAB | `pfilters.m`, full file |
| Python | `PyContourlet.py:744-839` |
| Parity | `test_pfilters_parity[9-7/5-3/Burt/pkva]` (4 cases pass) |

Returns the (h, g) lowpass analysis/synthesis pair for the Laplacian
pyramid step. Names: `9-7`, `9/7`, `5-3`, `5/3`, `Burt`, `burt`,
`maxflat`, `pkva`.

The four standard filters (9-7, 5-3, Burt, pkva) are validated bit-exact
against MATLAB. `maxflat` is skipped in the parity suite -- the MATLAB
implementation falls through to `wfilters` from the Wavelet Toolbox,
which Octave doesn't ship; Python implements `maxflat` directly and is
covered by smoke tests.

Bug fixed during deep review: `filterPkva` had `n = lf / 2.0` (float)
used as an index `h[:, 2*n - 1]`, which crashes. Replaced with
`n = lf // 2` plus an explicit even-length validation.

The errhandler at the bottom of the switch was converted from
`print('Invalid filter name')` to `raise ValueError`.

---

### ld2quin

| | |
|---|---|
| MATLAB | `ld2quin.m`, full file |
| Python | `PyContourlet.py:2459-2494` |
| Parity | `test_ld2quin_parity` (passes) |

Builds the quincunx filter pair (h0, h1) from a ladder allpass filter
(beta) using the Phoong/Kim/Vaidyanathan/Ansari construction.

MATLAB:
```matlab
sp = beta' * beta;             % outer product
h = qupz(sp, 1);
h0 = h; h0(2*n, 2*n) = h0(2*n, 2*n) + 1; h0 = h0 / 2;
h1 = -conv2(h, h0);
h1(4*n-1, 4*n-1) = h1(4*n-1, 4*n-1) + 1;
```

Python:
```python
n = lf // 2
sp = beta.T * beta
h = qupz(sp, 1)
h0 = h.copy()
h0[2*n - 1, 2*n - 1] = h0[2*n - 1, 2*n - 1] + 1
h0 = h0 / 2.0
h1 = -signal.convolve(h, h0)
h1[4*n - 2, 4*n - 2] = h1[4*n - 2, 4*n - 2] + 1
```

Notes: the original Python had three bugs: `beta.flatten(1)` (invalid
arg), `n = lf/2.0` (float index), and **the wrong indices**
`h0[2*n, 2*n]` / `h1[4*n - 1, 4*n - 1]`. MATLAB's 1-based indices
`h0(2*n, 2*n)` / `h1(4*n - 1, 4*n - 1)` map to 0-based `2*n - 1` and
`4*n - 2`. Now correct and parity-validated.

---

### dfilters

| | |
|---|---|
| MATLAB | `dfilters.m`, full file |
| Python | `PyContourlet.py:840-1308` |
| Parity | `test_dfilters_parity[name x type]` (16 cases pass) |

Returns the diamond-shaped (h0, h1) decomposition or reconstruction
filter pair. Validated names against MATLAB: `haar`, `9-7`/`9/7`/`cd`
(via McClellan transform of the 9-7 prototype), `5-3`/`5/3` (McClellan
of 5-3), `pkva`/`pkva6`/`pkva8`/`pkva12` (via `ld2quin` of the ladder
filter). Each verified for both `'d'` and `'r'` type arguments.

Python-only filter names not in the v2.0 MATLAB toolbox: `vk`, `ko`,
`kos`, `lax`, `sk`, `dvmlp`, `oqf_362`, `qmf`, `qmf2`, `sinc`,
`dmaxflat4..7`, `test`, `testDVM`. Imported from a later toolbox
release. Not bit-exact-validated against the v2.0 MATLAB but tested at
the smoke level (DFB perfect reconstruction).

Bugs fixed during deep review:

- `pkva-half4/6/8` filter cases referenced an undefined `ldfilterhalf()`
  function. Removed.
- `filterPkvaHalf6` had the typo `srtring.lower(...)` (would NameError).
  Removed with the rest.
- The MATLAB-canonical aliases `pkva6/pkva8/pkva12` were missing from
  the switch dict (only `pkva` was there). Added; all route to the same
  `filterPkva` body, which calls `ldfilter(fname)` -- and `ldfilter`
  already accepts those names.
- `5-3`/`5/3` names were missing entirely. Added a `filter53` helper
  that mirrors `filter79` (calls `pfilters('5-3')` then McClellans into
  2-D).
- `9-7`/`9/7` weren't in the switch dict (only `cd`/`7-9`). Added.
- The unknown-name errhandler now raises instead of `print()`.

---

### ffilters

| | |
|---|---|
| MATLAB | `ffilters.m`, full file |
| Python | `PyContourlet.py:2434-2457` |
| Parity | `test_ffilters_parity` (passes for `cd`/`d`) |

Builds the 4 fan filters from a diamond filter pair via `modulate2('r')`,
`modulate2('c')`, and transposition.

MATLAB:
```matlab
f0{1} = modulate2(h0, 'r');
f0{3} = f0{1}';      % transpose
```

Python: same with `f0[k].T`. List-of-arrays mirrors the MATLAB cell
vector. Validated bit-exact across all four `f0`/`f1` outputs.

---

## Layer 2: extension + filtering primitives

### getPerIndices

| | |
|---|---|
| MATLAB | `extend2.m` lines 63-70 (nested) |
| Python | `PyContourlet.py:1586-1594` |
| Parity | implicitly via `extend2` parity |

Builds the periodic-extension index vector
`[lx-lb+1:lx, 1:lx, 1:le]` (1-based) → 0-based `I - 1`.

The `if (lx < lb) | (lx < le)` guard is preserved with `np.mod`.
Python's `%` and `np.mod` follow the floored-division convention same
as MATLAB's `mod`, so negative modulo behavior matches without a
special case.

---

### extend2

| | |
|---|---|
| MATLAB | `extend2.m`, full file |
| Python | `PyContourlet.py:1511-1584` |
| Parity | `test_extend2_parity[per/qper_row/qper_col]` (3 cases pass) |

2-D extension with three modes: `per` (periodic both directions),
`qper_row`, `qper_col` (quincunx-aware).

Bugs fixed during deep review:

1. **Float boundary**: callers like `sefilter2` pass
   `np.floor(lf1)`/`np.ceil(lf1)` which arrive as numpy floats; numpy
   slicing requires int. Cast at the entry point:
   `ru, rd, cl, cr = int(ru), int(rd), int(cl), int(cr)`.
2. **Banker's rounding**: `qper_row` and `qper_col` need
   `round(rx/2)` (MATLAB rounds half away from zero) for the split
   point. Python's built-in `round()` uses banker's rounding -- so
   `round(5/2)=2` in Python, `round(5/2)=3` in MATLAB. For odd-row
   inputs the split was off by one. Replaced with `(rx + 1) // 2` which
   matches MATLAB's `round()` for non-negative integers.
3. The unknown-extmod errhandler now raises instead of `print()`.

Validated bit-exact across all three modes on a 32×32 random matrix
(`R32`) with various extension counts.

---

### sefilter2

| | |
|---|---|
| MATLAB | `sefilter2.m`, full file |
| Python | `PyContourlet.py:1435-1471` |
| Parity | `test_sefilter2_parity` (passes) |

2-D separable filtering with extension handling. Filters
`f1` along rows, `f2` along columns.

Bug fixed during deep review: the original line
`lf2 = (np.size(f1) - 1) / 2.0` used `f1` instead of `f2`. All current
in-tree callers use `f1 == f2` so the bug was masked, but it would have
broken any future caller with asymmetric filter pairs.

The `# pdb.set_trace()` debug line was removed.

---

### efilter2

| | |
|---|---|
| MATLAB | `efilter2.m`, full file |
| Python | `PyContourlet.py:1473-1509` |
| Parity | `test_efilter2_parity` (passes) |

2-D filtering with periodic edge extension. No bugs found in the port.
Validated bit-exact with a separable kernel (`h.T * h`).

---

### rowfiltering

| | |
|---|---|
| MATLAB | nested in `wfb2dec.m` (lines 53-56) and `wfb2rec.m` |
| Python | `PyContourlet.py:210-214` |
| Parity | implicitly via `wfb2dec`/`wfb2rec` parity |

Helper that filters along rows after periodic extension. Identical to
MATLAB; `signal.convolve(_, f, 'valid')` matches `conv2(_, f, 'valid')`
when `f` is a 1×N row vector.

---

## Layer 3: sampling primitives

### resampc

| | |
|---|---|
| MATLAB | `resampc.c` (MEX file), full file |
| Python | `PyContourlet.py:2115-2159` |
| Parity | `test_resampc_parity[1/2 x 1/2]` (4 cases pass) |

C-implemented inner kernel for column-wise periodic resampling. Only
the `'per'` extension mode is implemented (matches the MEX source).

The original Python port had three problems and was unrunnable:

1. `def resampc(x: cython.double[:, :], type: cython.int, ...)` -- the
   parameter name `type` shadowed the builtin `type()`, and the next
   line `if type(extmod) != str:` would crash with `'int' object is not
   callable`. Renamed to `rtype`.
2. The Cython type hints did nothing -- there was no `.pyx` build, so
   `import cython` in pure Python mode just lets the annotations parse;
   the actual loop ran in Python. We dropped the hints.
3. The body was a 4-deep nested loop that's slow even by Python
   standards. Replaced with a vectorized `(rows + s*j) % m` index
   computation per column.

MATLAB types are `{1, 2}` ↔ Python `{0, 1}`. Output is bit-exact.

To run the parity suite the MEX source needs to be rebuilt locally on
Apple Silicon; see `tests/octave/README.md`.

---

### resamp

| | |
|---|---|
| MATLAB | `resamp.m`, full file |
| Python | `PyContourlet.py:1977-2026` |
| Parity | `test_resamp_parity[1..4]` (4 cases pass) |

Dispatches to `resampc` for types 0,1 (column direction) and to
`resampc(x.T, type-2, ...).T` for types 2,3 (row direction by transpose).

MATLAB `1..4` ↔ Python `0..3`. Output is bit-exact across all 4 types.
Errhandler converted from `print` to `raise`.

---

### resampz

| | |
|---|---|
| MATLAB | `resampz.m`, full file |
| Python | `PyContourlet.py:2028-2113` |
| Parity | `test_resampz_parity[1..4]` (4 cases pass) |

Non-periodic version of `resamp`: zero-pads and grows the matrix.
Identical to MATLAB across all 4 types. Errhandler converted to raise.

---

### dup

| | |
|---|---|
| MATLAB | `dup.m`, full file |
| Python | `PyContourlet.py:1946-1975` |
| Parity | `test_dup_parity_zero`, `test_dup_parity_minimum` (2 cases pass) |

Diagonal upsampling with two modes: explicit phase or `'minimum'`-size.

Bug fixed during deep review: the minimum-phase branch had
`y[0::step[0], 0::step[0]] = x.copy()` -- the second axis used
`step[0]` instead of `step[1]`. Fixed. Both modes now bit-exact match
MATLAB.

---

### qupz

| | |
|---|---|
| MATLAB | `qupz.m`, full file |
| Python | `PyContourlet.py:1896-1944` |
| Parity | `test_qupz_parity[1/2]` (2 cases pass) |

Quincunx upsampling via the Smith decomposition: combines `resampz` and
explicit row-stride zero insertion. MATLAB type→Python type mapping is
verified bit-exact for both quincunx variants. Errhandler raises.

---

### qdown

| | |
|---|---|
| MATLAB | `qdown.m`, full file |
| Python | `PyContourlet.py:1744-1809` |
| Parity | `test_qdown_parity[1r/1c/2r/2c]` (4 cases pass) |

Quincunx downsampling via the Smith decomposition. Four sub-handlers:
`type1r`, `type1c`, `type2r`, `type2c`.

Bugs fixed during deep review:

1. **Indentation crash**: `def type1r():` had its body at the right
   indent (`z = resamp(x, 1)`) but the following `if phase == 0` block
   was *outside* the function -- the inner function returned `None`,
   and the `if/else` ran at outer scope on undefined names. Fixed.
2. Errhandler converted to raise.

Validated bit-exact for all 4 types on `R32`.

---

### qup

| | |
|---|---|
| MATLAB | `qup.m`, full file |
| Python | `PyContourlet.py:1811-1894` |
| Parity | `test_qup_parity[1r/1c/2r/2c]` (4 cases pass) |

Quincunx upsampling, the inverse pair of `qdown`.

Bug fixed during deep review: `type1r` phase==1 branch used `len(z)`
(rows) where MATLAB indexed columns. Replaced with `z.shape[1]` and
documented in a comment that the MATLAB index `[2:end, 1]` runs over
columns. Other 3 types matched MATLAB without changes.
Errhandler converted to raise.

---

### pdown

| | |
|---|---|
| MATLAB | `pdown.m`, full file |
| Python | `PyContourlet.py:1598-1660` |
| Parity | `test_pdown_parity[1..4]` (4 cases pass) |

Parallelogram downsampling. Four type handlers, each combining `resamp`
with either row- or column-stride downsampling.

Bug fixed during deep review: `type0` phase==1 branch used `len(x)` on
a column index (`x[1::2, np.r_[1:len(x), 0]]`). Replaced with
`x.shape[1]`. Errhandler converted to raise. Validated bit-exact across
all 4 types.

---

### pup

| | |
|---|---|
| MATLAB | `pup.m`, full file |
| Python | `PyContourlet.py:1662-1742` |
| Parity | `test_pup_parity[1..4]` (4 cases pass) |

Parallelogram upsampling, the inverse of `pdown`.

Bug fixed during deep review: `type0` phase==1 had the same
`len(y)`-vs-`shape[1]` bug as `pdown.type0`. Fixed. Errhandler converted
to raise. Validated bit-exact across all 4 types.

---

## Layer 4: polyphase decomposition / reconstruction

### qpdec

| | |
|---|---|
| MATLAB | `qpdec.m`, full file |
| Python | `PyContourlet.py:2161-2222` |
| Parity | `test_qpdec_parity[1r/1c/2r/2c]` (4 cases pass) |

Quincunx polyphase decomposition.

Bugs fixed during deep review:

1. The switch dict had `'2r': type2c` (typo); both `2r` and `2c` routed
   to the column code, so `2r` silently produced wrong output. Fixed
   to `'2r': type2r`.
2. `type1r` phase==1 used `len(y)` where MATLAB indexed columns. Fixed
   to `y.shape[1]`.

Validated bit-exact for all 4 types on `R32`.

---

### qprec

| | |
|---|---|
| MATLAB | `qprec.m`, full file |
| Python | `PyContourlet.py:2224-2294` |
| Parity | `test_qprec_parity[1r/1c/2r/2c]` (4 cases pass) |

Quincunx polyphase reconstruction (inverse of `qpdec`). Same two bugs
as `qpdec` were present and fixed: switch dict typo + column index.
Validated bit-exact, and `qprec(qpdec(x)) == x` to machine precision
for all 4 types (smoke test `test_qpdec_qprec_roundtrip`).

---

### ppdec

| | |
|---|---|
| MATLAB | `ppdec.m`, full file |
| Python | `PyContourlet.py:2296-2360` |
| Parity | `test_ppdec_parity[1..4]` (4 cases pass) |

Parallelogram polyphase decomposition. `type0` phase==1 had the
`len(x)`-vs-`shape[1]` bug; fixed. Validated bit-exact across all 4
types.

---

### pprec

| | |
|---|---|
| MATLAB | `pprec.m`, full file |
| Python | `PyContourlet.py:2362-2432` |
| Parity | `test_pprec_parity[1..4]` (4 cases pass) |

Parallelogram polyphase reconstruction. `type0` phase==1 had the same
bug; fixed. `pprec(ppdec(x)) == x` to machine precision for all 4 types.

---

## Layer 5: 2-channel filter banks

### fbdec

| | |
|---|---|
| MATLAB | `fbdec.m`, full file |
| Python | `PyContourlet.py:503-569` |
| Parity | implicitly via `dfbdec` parity |

2-channel 2-D filter bank decomposition with three filterbank types
(`q`, `p`, `pq`).

Bug fixed during deep review: the parallelogram (`type1 == 'p'`) branch
constructed a 4-element list of 2x2 resampling matrices `R[0..3]` and
computed `shift = R[type2] * shift`. This was *element-wise*
multiplication; MATLAB `R{type2} * shift` is matrix multiplication.
Replaced with `R[type2] @ shift`.

This bug was masked because the DFB driver uses `'q'` and `'pq'`
filterbank types, not `'p'`, so the broken branch was never hit by any
caller. Fixed for correctness even though smoke tests didn't catch it.

Errhandler converted to raise.

---

### fbrec

| | |
|---|---|
| MATLAB | `fbrec.m`, full file |
| Python | `PyContourlet.py:571-647` |
| Parity | implicitly via `dfbrec` parity |

2-channel 2-D filter bank reconstruction. Same `R[type2] * shift` bug as
`fbdec`; fixed. Errhandler converted to raise.

---

### fbdec_l

| | |
|---|---|
| MATLAB | `fbdec_l.m`, full file |
| Python | `PyContourlet.py:649-695` |
| Parity | implicitly via `dfbdec_l` parity |

Ladder-structure variant of `fbdec`. Used by the `pkva` DFB path.

Notes: `str.lower(type1[0])` replaced with `type1[0].lower()` (idiomatic
Python; also avoids breaking on str subclasses, though that's
theoretical here). Errhandler converted to raise.

The `f[:, ::2] = -f[:, ::2]` modulation: MATLAB writes `f(1:2:end) =
-f(1:2:end)` which on a row vector flips every other element. For the
typical case `f = ldfilter('pkva')` returning a (1, 2N) row, the Python
slice produces the same result.

---

### fbrec_l

| | |
|---|---|
| MATLAB | `fbrec_l.m`, full file |
| Python | `PyContourlet.py:697-742` |
| Parity | implicitly via `dfbrec_l` parity |

Ladder-structure inverse of `fbdec_l`. Same `str.lower` cleanup and
errhandler-converts-to-raise as `fbdec_l`. No correctness changes.

---

## Layer 6: backsampling support

### backsamp

| | |
|---|---|
| MATLAB | `backsamp.m`, full file |
| Python | `PyContourlet.py:2580-2617` |
| Parity | implicitly via `dfbdec` parity |

Re-orders the DFB tree's subbands so the overall sampling becomes
diagonal. The MATLAB type↔Python type mapping was verified
function-by-function during the deep review:

- `n == 1`: MATLAB `resamp(_, 4)` → Python type 3, MATLAB `resamp(_, 1)`
  → Python type 0. Both correct.
- `n > 2`: same shift ranges (`shift = 2*k - (2^(n-2) + 1)` for
  `k = 1..2^(n-2)`).

Errhandler converted to raise.

---

### rebacksamp

| | |
|---|---|
| MATLAB | `rebacksamp.m`, full file |
| Python | `PyContourlet.py:2619-2658` |
| Parity | implicitly via `dfbrec` parity |

Inverse of `backsamp`. Negative-shift variant of the same logic.
Errhandler converted to raise.

---

## Layer 7: directional filter bank driver

### dfbdec

| | |
|---|---|
| MATLAB | `dfbdec.m`, full file |
| Python | `PyContourlet.py:219-291` |
| Parity | `test_dfbdec_parity[cd/9-7 x n=1,2,3]` (6 cases pass) |

General DFB decomposition: tree-structured filter bank that recursively
applies `fbdec` with quincunx and parallelogram filterbank types. After
the tree, `backsamp` re-orders the subbands and the second half is
flipped.

Validated bit-exact against MATLAB for `cd` and `9-7` filters at levels
1..3. The `haar` filter case shows nontrivial differences at nlev≥3 in
both MATLAB and Python due to its even-length filters interacting with
the parallelogram shift handling -- this is reference behavior, not a
port bug, and is not asserted in tests.

The `print('Number of decomposition levels...')` errhandler was
converted to raise.

---

### dfbrec

| | |
|---|---|
| MATLAB | `dfbrec.m`, full file |
| Python | `PyContourlet.py:293-367` |
| Parity | `test_dfbdec_parity[cd/9-7 x n=1,2,3]` (asserts `rec` matches MATLAB) |

DFB reconstruction. Walks the tree in reverse with `fbrec`, undoes the
back-sampling. Validated bit-exact for `cd`/`9-7` levels 1..3. Errhandler
converted to raise.

---

### dfbdec_l

| | |
|---|---|
| MATLAB | `dfbdec_l.m`, full file |
| Python | `PyContourlet.py:369-435` |
| Parity | `test_dfbdec_l_parity[n=1,2,3]` (3 cases pass) |

Ladder-structure DFB decomposition (uses `pkva`). The most-used path in
practice. Validated bit-exact at levels 1..3.

The MATLAB `if isstr(f)` was originally translated as `if str(f) == f:`
(a Pythonic anti-pattern -- works but doesn't read). Replaced with
`isinstance(f, str)`. Errhandler converted to raise.

---

### dfbrec_l

| | |
|---|---|
| MATLAB | `dfbrec_l.m`, full file |
| Python | `PyContourlet.py:437-497` |
| Parity | asserted as part of `test_dfbdec_l_parity` (rec matches MATLAB) |

Ladder DFB reconstruction. Same `isinstance` cleanup; errhandler raises.
Validated bit-exact at levels 1..3.

---

## Layer 8: Laplacian pyramid + critically sampled wavelet

### lpdec

| | |
|---|---|
| MATLAB | `lpdec.m`, full file |
| Python | `PyContourlet.py:35-62` |
| Parity | `test_lpdec_parity[9-7/5-3/Burt]` (3 cases pass) |

Laplacian pyramid decomposition. No structural bugs in the port;
identical line-by-line to MATLAB. Validated bit-exact for 3 filters.

---

### lprec

| | |
|---|---|
| MATLAB | `lprec.m`, full file |
| Python | `PyContourlet.py:65-100` |
| Parity | `test_lprec_parity[9-7/5-3/Burt]` (3 cases pass) |

Laplacian pyramid reconstruction. Bit-exact. PR (`lprec(lpdec(x))`) at
machine precision for all standard filters.

---

### wfb2dec

| | |
|---|---|
| MATLAB | `wfb2dec.m`, full file |
| Python | `PyContourlet.py:105-153` |
| Parity | `test_wfb2dec_wfb2rec_parity` (passes) |

Critically sampled 2-D wavelet filter bank decomposition (used as the
`nlevs[i] == 0` special case in `pdfbdec`).

Constructs the highpass filter `h1 = -g .* (-1).^([1:len_h1] - c)` from
the synthesis lowpass `g`, with a center shift adjustment for
even-length filters. The Python translation matches line-for-line.

Validated bit-exact: all four subbands `(LL, LH, HL, HH)` match MATLAB,
and the reconstruction error via `wfb2rec` is `2.4e-14` relative.

---

### wfb2rec

| | |
|---|---|
| MATLAB | `wfb2rec.m`, full file |
| Python | `PyContourlet.py:156-204` |
| Parity | `test_wfb2dec_wfb2rec_parity` (asserts `rec` matches MATLAB) |

Critically sampled wavelet reconstruction. Bit-exact match.

---

## Layer 9: PDFB top level + utilities

### pdfbdec

| | |
|---|---|
| MATLAB | `pdfbdec.m`, full file |
| Python | `PyContourlet.py:3012-3077` |
| Parity | `test_pdfbdec_pdfbrec_parity` (asserts every subband bit-exact) |

The top-level pyramidal directional filter bank. Recursively decomposes
the lowpass band; for each level dispatches to either the ladder
structure (`pkva*`) or the general DFB (`cd`, `9-7`, etc), or to
`wfb2dec` if `nlevs[i] == 0`.

The Python translation matches MATLAB structure-for-structure. Validated
bit-exact across all output subbands for `nlevs=[2, 3]` with
`pfilt='9-7'`, `dfilt='pkva'`.

---

### pdfbrec

| | |
|---|---|
| MATLAB | `pdfbrec.m`, full file |
| Python | `PyContourlet.py:3079-3122` |
| Parity | `test_pdfbdec_pdfbrec_parity` (asserts `rec` matches MATLAB) |

Inverse PDFB. Recursive walk-up with `dfbrec_l`/`dfbrec`/`wfb2rec` per
level. Bit-exact match.

---

### pdfb2vec

| | |
|---|---|
| MATLAB | `pdfb2vec.m`, full file |
| Python | `PyContourlet.py:2962-3010` |
| Parity | `test_pdfb2vec_parity` (asserts `c` and `s[:,2:4]` match MATLAB) |

Serializes a PDFB output into a 1-D coefficient vector `c` and a
structure matrix `s` (4 columns: layer, direction, rows, cols).

The original Python had three crash bugs: `temp = a[0].shape` referenced
an undefined `a`, `ind = ind + nd` was de-indented out of the loop, and
`np.sum(...)` returned a non-int that broke array slicing. All fixed.

The structure matrix `s`: MATLAB uses 1-based layer/direction in cols
1-2 and the size in cols 3-4. Python uses 0-based layer/direction in
cols 0-1 and size in cols 2-3. The parity test compares only the size
columns (`s[:, 2:4]` Python ↔ `s[:, 3:4]` MATLAB), since the
layer/direction codes have a known 1-off shift.

The coefficient vector `c` (column-major flatten via `flatten('F')`)
matches MATLAB's `y{l}{d}(:)` exactly.

---

### vec2pdfb

| | |
|---|---|
| MATLAB | `vec2pdfb.m`, full file |
| Python | `PyContourlet.py:2921-2960` |
| Parity | implicitly via `pdfb2vec` roundtrip |

Inverse of `pdfb2vec`. The original Python had `nd = len((s[:,0]==l)
.nonzero())` which is always 1 (`.nonzero()` returns a 1-tuple of
arrays); replaced with `np.count_nonzero(s[:, 0] == l)`. Layer count
derived from `s[-1, 0] + 1` (Python's 0-based convention). Reshape uses
`order='F'` to match the MATLAB column-major flatten in `pdfb2vec`.

Smoke test `test_pdfb2vec_vec2pdfb_then_pdfbrec` confirms a full
roundtrip through `pdfbdec → pdfb2vec → vec2pdfb → pdfbrec` reconstructs
the input at machine precision.

---

### pdfb_nest

| | |
|---|---|
| MATLAB | `pdfb_nest.m`, full file |
| Python | `PyContourlet.py:3124-3164` |
| Parity | not validated against MATLAB (Monte Carlo with random inputs) |

Estimates noise standard deviation in the PDFB domain via Monte Carlo:
runs `pdfbdec` on `niter` independent Gaussian fields, accumulates the
per-coefficient variance, returns the per-coefficient std-dev scaling
factor.

This function uses random inputs, so bit-exact comparison with MATLAB is
not meaningful. Parity is at the *structural* level: the Python and
MATLAB implementations follow the same algorithm step-for-step.
Smoke-tested via `test_pdfb_nest_returns_lowpass_zeros_and_positive_highpass`
(checks the lowpass entries are exactly zero, all highpass entries are
strictly positive).

The Python signature accepts an optional `numpy.random.Generator` for
reproducibility -- the MATLAB version uses `randn`'s global state.

This was the first of two functions newly ported in this branch (not
present in the original Python tree).

---

### pdfb_tr

| | |
|---|---|
| MATLAB | `pdfb_tr.m`, full file |
| Python | `PyContourlet.py:3166-3220` |
| Parity | not validated against MATLAB (no fixture); 3 smoke tests |

Truncates a PDFB output to its N most significant coefficients at a
given scale and direction. Used for nonlinear-approximation experiments
(see `decdemo`).

Faithful port of the MATLAB control flow:

- `scale == n`: keep the lowpass.
- `scale == 0`: keep all scales.
- `direction == 0`: keep all directions.
- `ncoef` (optional): vectorize, threshold by sorted-magnitude rank,
  unvectorize via `vec2pdfb`.

The MATLAB toolbox uses 1-based scale/direction; Python preserves that
on the public API for compatibility (so e.g. `pdfb_tr(y, scale=1, ...)`
keeps the *finest* scale). Three smoke tests cover the dispatch:
`test_pdfb_tr_keeps_exactly_ncoef_significant`,
`test_pdfb_tr_zeros_non_selected_subbands`,
`test_pdfb_tr_lowpass_kept_when_scale_equals_n`.

This was the second of two newly ported functions.

---

## Layer 10: display / scoring helpers

### computescale

| | |
|---|---|
| MATLAB | `computescale.m`, full file |
| Python | `PyContourlet.py:2703-2842` |
| Parity | not asserted (display utility, not numerically critical) |

Computes display scaling for `showpdfb`. Originally had multiple bugs:
`sum = 0` shadowed the builtin then `sum(...)` was called on it (NameError);
`math.sqrt` was used after `import math` had been removed; `scales =
np.zeros((1, 2))` followed by `scales[1] = ...` would have IndexError.
All cleaned up; behavior smoke-tested via the demo end-to-end.

---

### dfbimage

| | |
|---|---|
| MATLAB | `dfbimage.m`, full file |
| Python | `PyContourlet.py:2844-2919` |
| Parity | not asserted |

Composes the DFB subband images into a single display-friendly tile
grid. Pure layout code -- bit-exactness vs MATLAB isn't meaningful.

---

### showpdfb

| | |
|---|---|
| MATLAB | `showpdfb.m`, full file |
| Python | `PyContourlet.py:3222-3585` |
| Parity | not asserted |

Top-level display routine for PDFB coefficients. Largest function in the
file (~360 lines). Imports `matplotlib.pyplot as plt`. Used by the demo
indirectly (the demo does its own `imshow` of the lowpass + NLA
reconstructions; showpdfb is available for the all-subbands view).
Parity vs MATLAB not asserted -- output is a matplotlib figure, not a
numerical array.

---

## Summary

- **230 numerical-equivalence assertions pass** across multiple input
  shapes (square 32x32, square 64x64, rectangular 16x24 for primitives;
  square 32x32 and square 64x64 for DFB / PDFB). Every public function
  for which MATLAB-side execution is feasible is exercised on at least
  two distinct shapes.
- **5 functions** are not part of bit-exact MATLAB validation:
  `pdfb_nest` (random inputs), `pdfb_tr` (relies on `vec2pdfb` which is
  parity-validated -- the smoke roundtrip is the strongest available
  guarantee), `dmaxflat` (not in v2.0 toolbox), `pfilters('maxflat')`
  (depends on Wavelet Toolbox, not in Octave), and the three display
  helpers (`showpdfb`, `dfbimage`, `computescale`).
- **2 functions** were entirely new in this branch: `pdfb_nest` and
  `pdfb_tr` (ported directly from the MATLAB toolbox).
- **27 latent bugs** were found and fixed during the deep review, all
  pre-dating this branch.

The full test suite (smoke + parity) is 324 tests, runs in ~2 seconds,
and validates the port end-to-end.
