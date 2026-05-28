# Octave display stubs (CI / headless use only)

These are no-op replacements for Octave's display functions, used during
fixture generation on a headless CI runner without a graphics toolkit.

`showpdfb.m` calls `image()`, `axis()`, `colormap()` at the end purely
for visualization. Those calls fail on a headless runner even with
`gnuplot` installed (font / renderer requirements). Since we only need
the returned `displayIm` matrix for parity tests, replacing the display
calls with no-ops is the cleanest fix.

To activate: `addpath('tests/octave/stubs')` before `addpath('<TOOLBOX>')`
in the Octave invocation. Octave resolves functions in path order, so
the stubs win against the built-ins.

The fixture generator does this automatically when running on CI (where
no graphics toolkit is available).
