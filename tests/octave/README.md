# Octave parity validation

This directory contains a one-shot script that runs the original MATLAB
Contourlet Toolbox under Octave and saves the outputs to `tests/fixtures/`.
The pytest parity suite (`tests/test_octave_parity.py`) then loads each
fixture and asserts that the Python implementation produces the same
numerical output.

Octave is not a runtime dependency of `pycontourlet`. It's only used here
to validate the port against the MATLAB reference.

## Prerequisites

1. **Octave** (tested with 11.x). On macOS: `brew install octave`.
2. **A copy of Minh Do's MATLAB Contourlet Toolbox** (v2.0, GPL).
   Download the original tarball from the author's page:

   <https://minhdo.ece.illinois.edu/software/contourlet_toolbox.tar>

   ```sh
   curl -O https://minhdo.ece.illinois.edu/software/contourlet_toolbox.tar
   mkdir -p ~/contourlet_toolbox
   tar -xf contourlet_toolbox.tar -C ~/contourlet_toolbox
   ```

   The only piece that needs to be built locally is the `resampc` MEX
   file -- the bundled binaries don't include Apple Silicon. Build with:

   ```sh
   cp ~/contourlet_toolbox/resampc.c /tmp/resampc.c
   sed -i '' 's|#include "mex.h"|#include "mex.h"\n#include <string.h>|' /tmp/resampc.c
   mkoctfile --mex /tmp/resampc.c -o ~/contourlet_toolbox/resampc
   ```

## Generating fixtures

From the repo root:

```sh
octave --no-gui --eval \
  "addpath('<TOOLBOX_PATH>'); \
   addpath('tests/octave'); \
   generate_fixtures('tests/fixtures')"
```

Replace `<TOOLBOX_PATH>` with the path to your MATLAB toolbox checkout
(e.g. `~/contourlet_toolbox`). The script writes ~100 `.mat` files
totaling ~3 MB into `tests/fixtures/`. The directory is `.gitignore`d.

## Running the parity tests

```sh
pip install -e .[dev]
pytest tests/test_octave_parity.py
```

If `tests/fixtures/` is empty, the parity module is skipped with a clear
message. The smoke tests (`tests/test_smoke.py`) don't need fixtures.

## What's tested

103 numerical-equivalence assertions covering every public function in
the MATLAB toolbox: filter generators (`pfilters`, `dfilters`,
`ldfilter`, `ld2quin`, `mctrans`, `modulate2`, `reverse2`, `ffilters`),
sampling primitives (`resamp`, `resampc`, `resampz`, `qupz`, `dup`,
`qdown`/`qup`, `pdown`/`pup`), polyphase decomposition/reconstruction
(`qpdec`/`qprec`, `ppdec`/`pprec`), extension/filtering primitives
(`extend2`, `sefilter2`, `efilter2`), the Laplacian pyramid
(`lpdec`/`lprec`), the wavelet filter bank (`wfb2dec`/`wfb2rec`), the
DFB driver in both ladder and general modes (`dfbdec`/`dfbrec`,
`dfbdec_l`/`dfbrec_l`), the top-level PDFB pair, the
vector-form converter, and `snr`.

## Functions not validated via Octave

- **`pfilters('maxflat')`** -- MATLAB's `pfilters` falls through to
  `wfilters` from the Wavelet Toolbox, which Octave doesn't ship.
  Python's `maxflat` is implemented directly and is covered by the smoke
  suite (LP perfect-reconstruction at 1e-16).
- **`dmaxflat`** -- not in the v2.0 toolbox we audit against; appears in
  later toolbox versions. Covered by smoke tests via DFB filters that
  use it.
- **Display helpers** (`showpdfb`, `dfbimage`, `computescale`) --
  exercised by `pycontourlet/demo.py`; bit-exact MATLAB equivalence isn't
  meaningful for plots.
