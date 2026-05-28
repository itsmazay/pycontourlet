# Contributing to pycontourlet

Thanks for considering a contribution! This doc covers the dev setup,
the test suite, and how to validate the port against the MATLAB
toolbox.

## Development environment

Use a virtual environment so the project's dependencies stay isolated
from the rest of your system Python. We use the standard library
[`venv`](https://docs.python.org/3/library/venv.html) — no extra tools
required.

```sh
git clone https://github.com/itsmazay/pycontourlet.git
cd pycontourlet
python3 -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .[dev]
```

Day-to-day: `source .venv/bin/activate` when you start working,
`deactivate` when you're done. The `.venv/` directory is git-ignored.

To start fresh (e.g. after a Python upgrade):

```sh
deactivate                   # if currently active
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

`pyproject.toml` declares `requires-python = ">=3.9"`. CI runs against
3.9, 3.10, 3.11, and 3.12.

## Running the test suite

```sh
pytest tests/
```

That should produce 94 passing smoke tests. The 234 Octave-parity
tests are skipped automatically if `tests/fixtures/` is empty (the
default for fresh clones). See the next section to enable them.

## Running the demo

```sh
python -m pycontourlet
```

Outputs three PNGs to the current directory:

- `reconstruction.png` — input vs perfect reconstruction
- `coefficients.png` — the contourlet coefficient pyramid
- `nla_comparison.png` — input vs NLA reconstructions at 5%/2.5%/1%

Pass `--show` for interactive matplotlib windows, or
`--out-dir <PATH>` to save elsewhere.

## Running the full test suite (with MATLAB parity)

The parity tests compare every public function's output to the
original MATLAB Contourlet Toolbox running under Octave. To enable
them:

1. **Install Octave** (`brew install octave` on macOS,
   `apt install octave` on Debian-based Linux).

2. **Download the upstream MATLAB toolbox**:

   ```sh
   curl -O https://minhdo.ece.illinois.edu/software/contourlet_toolbox.tar
   mkdir -p ~/contourlet_toolbox
   tar -xf contourlet_toolbox.tar -C ~/contourlet_toolbox
   ```

3. **Rebuild `resampc.mex`** for your platform (the bundled `.mex*`
   binaries don't include Apple Silicon):

   ```sh
   cp ~/contourlet_toolbox/resampc.c /tmp/resampc.c
   sed -i '' 's|#include "mex.h"|#include "mex.h"\n#include <string.h>|' /tmp/resampc.c
   mkoctfile --mex /tmp/resampc.c -o ~/contourlet_toolbox/resampc
   ```

   On Linux drop the `''` argument to `sed -i`.

4. **Generate the fixtures**:

   ```sh
   octave --no-gui --eval \
     "addpath('$HOME/contourlet_toolbox'); \
      addpath('tests/octave'); \
      generate_fixtures('tests/fixtures')"
   ```

5. **Run the full suite**:

   ```sh
   pytest tests/
   ```

You should see 328 tests pass. See `tests/octave/README.md` for the
detailed validation guide.

## Code style

We use [`ruff`](https://docs.astral.sh/ruff/) for linting and
formatting. To check before committing:

```sh
pip install ruff
ruff check pycontourlet/ tests/
ruff format pycontourlet/ tests/
```

Most rules follow PEP 8 with a relaxed line-length to accommodate
math-heavy code. Keep MATLAB-faithful code as faithful as possible
(don't over-Pythonize numerical code where it would obscure the
upstream algorithm).

## Adding a new function or behavior

1. Write the function in `pycontourlet/PyContourlet.py`. Mirror the
   MATLAB version closely if there is one.
2. Add a smoke test in `tests/test_smoke.py` (no Octave needed). At
   minimum cover any dispatch branches and the basic call path.
3. If the function exists in the MATLAB toolbox, add it to
   `tests/octave/generate_fixtures.m` and a parity test in
   `tests/test_octave_parity.py`. Regenerate fixtures and confirm
   bit-exactness.
4. Update `tests/octave/AUDIT.md` and `tests/octave/AUDIT_CONTENTS.md`
   with a per-function entry.
5. Update `CHANGELOG.md` under `## [Unreleased]`.

## Reporting bugs

If you find a numerical mismatch with MATLAB:

1. Reduce the input to the smallest reproducer.
2. Open an issue with the MATLAB call, the Python call, and the diff.
3. If you can run Octave, attach a `.mat` fixture; we'll add it to the
   parity suite.

If you find a Python error (NameError, type error, etc.):

1. Run `pytest tests/test_smoke.py -k <function-name> -v` to confirm
   it isn't already covered.
2. Open an issue with the traceback and the input that reproduced it.

## Releases

See [`tools/release.md`](tools/release.md) for the release process.
