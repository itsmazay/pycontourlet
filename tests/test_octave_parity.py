"""Numerical parity tests against MATLAB toolbox outputs (via Octave).

Each test loads a .mat fixture saved by tests/octave/generate_fixtures.m and
asserts that the Python implementation produces the same numerical output.

Most tests are parametrized over multiple input shapes (square 32x32,
square 64x64, rectangular 16x24) so shape-dependent bugs surface.

Regenerating fixtures:

    octave --no-gui --eval \
      "addpath('/path/to/contourlet_toolbox'); \
       addpath('tests/octave'); \
       generate_fixtures('tests/fixtures')"

If the fixtures directory is missing, the whole module is skipped.
"""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy.io import loadmat

import pycontourlet as pc

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

if not os.path.isdir(FIXTURES) or not os.listdir(FIXTURES):
    pytest.skip(
        "Octave fixtures missing; regenerate with tests/octave/generate_fixtures.m",
        allow_module_level=True,
    )


# Shape parametrizations grouped by which functions they apply to.
PRIM_SHAPES = ["sq32", "sq64", "rect"]            # resamp/resampc/resampz/extend2/sefilter2/efilter2/qpdec/qprec/ppdec/pprec/qdown/qup/pdown/pup
QUPZ_SHAPES = ["sq16", "sq32", "rect"]            # qupz uses smaller input
LP_SHAPES = ["sq32", "sq64", "rect"]              # Laplacian pyramid
WFB_SHAPES = ["sq32", "sq64"]                     # wavelet FB needs even dims
DFB_SHAPES = ["sq32", "sq64"]                     # DFB needs square divisible by 2^nlev


def _load(name: str) -> dict:
    return loadmat(os.path.join(FIXTURES, name + ".mat"))


def _assert_close(py, mat, atol=1e-10, rtol=1e-10, name=""):
    """Compare Python output to MATLAB. MATLAB always returns 2-D; Python
    sometimes returns 1xN row vectors. Squeeze before comparing if shapes
    differ only in singleton dims."""
    py = np.asarray(py)
    mat = np.asarray(mat)
    if py.shape != mat.shape and py.squeeze().shape == mat.squeeze().shape:
        py = py.squeeze()
        mat = mat.squeeze()
    np.testing.assert_allclose(
        py, mat, atol=atol, rtol=rtol, err_msg=f"{name} mismatch"
    )


# -----------------------------------------------------------------------------
# Filter generators (shape-independent)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("name,slug", [
    ("9-7", "9_7"),
    ("5-3", "5_3"),
    ("Burt", "Burt"),
    ("pkva", "pkva"),
])
def test_pfilters_parity(name, slug):
    ref = _load(f"pfilters_{slug}")
    h, g = pc.pfilters(name)
    _assert_close(h, ref["h"], name=f"pfilters({name}) h")
    _assert_close(g, ref["g"], name=f"pfilters({name}) g")


@pytest.mark.parametrize("name,slug", [
    ("haar", "haar"),
    ("9-7", "9_7"),
    ("cd", "cd"),
    ("5-3", "5_3"),
    ("pkva", "pkva"),
    ("pkva6", "pkva6"),
    ("pkva8", "pkva8"),
    ("pkva12", "pkva12"),
])
@pytest.mark.parametrize("ftype", ["d", "r"])
def test_dfilters_parity(name, slug, ftype):
    ref = _load(f"dfilters_{slug}_{ftype}")
    h0, h1 = pc.dfilters(name, ftype)
    _assert_close(h0, ref["h0"], name=f"dfilters({name}, {ftype}) h0")
    _assert_close(h1, ref["h1"], name=f"dfilters({name}, {ftype}) h1")


@pytest.mark.parametrize("name", ["pkva", "pkva6", "pkva8", "pkva12"])
def test_ldfilter_parity(name):
    ref = _load(f"ldfilter_{name}")
    f = pc.ldfilter(name)
    _assert_close(f, ref["f"], name=f"ldfilter({name})")


def test_ld2quin_parity():
    ref = _load("ld2quin_pkva")
    h0, h1 = pc.ld2quin(ref["beta"])
    _assert_close(h0, ref["h0"], name="ld2quin h0")
    _assert_close(h1, ref["h1"], name="ld2quin h1")


def test_mctrans_parity():
    ref = _load("mctrans_9_7")
    h2d = pc.mctrans(ref["h"], ref["t"])
    _assert_close(h2d, ref["h2d"], name="mctrans")


@pytest.mark.parametrize("direction", ["r", "c", "b"])
def test_modulate2_parity(direction):
    ref = _load(f"modulate2_{direction}")
    y = pc.modulate2(ref["M"], direction)
    _assert_close(y, ref["y"], name=f"modulate2({direction})")


def test_reverse2_parity():
    ref = _load("reverse2")
    y = pc.reverse2(ref["M"])
    _assert_close(y, ref["y"], name="reverse2")


def test_ffilters_parity():
    ref = _load("ffilters_cd_d")
    f0, f1 = pc.ffilters(ref["h0"], ref["h1"])
    for k in range(4):
        _assert_close(f0[k], ref[f"f0_{k+1}"], name=f"ffilters f0[{k}]")
        _assert_close(f1[k], ref[f"f1_{k+1}"], name=f"ffilters f1[{k}]")


# -----------------------------------------------------------------------------
# Sampling primitives (parametrized over shape)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("rt", [1, 2])
@pytest.mark.parametrize("sh", [1, 2])
def test_resampc_parity(shape, rt, sh):
    ref = _load(f"resampc_{shape}_t{rt}_s{sh}")
    y = pc.resampc(ref["x"], rt - 1, sh, "per")
    _assert_close(y, ref["y"], name=f"resampc({shape}, t={rt}, s={sh})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("rt", [1, 2, 3, 4])
def test_resamp_parity(shape, rt):
    ref = _load(f"resamp_{shape}_t{rt}")
    y = pc.resamp(ref["x"], rt - 1)
    _assert_close(y, ref["y"], name=f"resamp({shape}, t={rt})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("rt", [1, 2, 3, 4])
def test_resampz_parity(shape, rt):
    ref = _load(f"resampz_{shape}_t{rt}")
    y = pc.resampz(ref["x"], rt - 1)
    _assert_close(y, ref["y"], name=f"resampz({shape}, t={rt})")


@pytest.mark.parametrize("shape", QUPZ_SHAPES)
@pytest.mark.parametrize("tp", [1, 2])
def test_qupz_parity(shape, tp):
    ref = _load(f"qupz_{shape}_t{tp}")
    y = pc.qupz(ref["x"], tp)
    _assert_close(y, ref["y"], name=f"qupz({shape}, t={tp})")


def test_dup_parity_zero():
    ref = _load("dup_2x2_zero")
    y = pc.dup(ref["x"], np.array([2, 2]), np.array([0, 0]))
    _assert_close(y, ref["y"], name="dup zero-phase")


def test_dup_parity_minimum():
    ref = _load("dup_minimum")
    y = pc.dup(ref["x"], np.array([2, 2]), phase=np.array(["m", 0]))
    _assert_close(y, ref["y"], name="dup minimum-phase")


def test_dup_parity_rect():
    ref = _load("dup_rect_zero")
    y = pc.dup(ref["x"], np.array([2, 2]), np.array([0, 0]))
    _assert_close(y, ref["y"], name="dup rect zero-phase")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qdown_parity(shape, qt):
    ref = _load(f"qdown_{shape}_{qt}")
    y = pc.qdown(ref["x"], qt)
    _assert_close(y, ref["y"], name=f"qdown({shape}, {qt})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qup_parity(shape, qt):
    ref = _load(f"qup_{shape}_{qt}")
    rec = pc.qup(ref["y"], qt)
    _assert_close(rec, ref["rec"], name=f"qup({shape}, {qt})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pdown_parity(shape, pt):
    ref = _load(f"pdown_{shape}_t{pt}")
    y = pc.pdown(ref["x"], pt - 1)
    _assert_close(y, ref["y"], name=f"pdown({shape}, t={pt})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pup_parity(shape, pt):
    ref = _load(f"pup_{shape}_t{pt}")
    rec = pc.pup(ref["y"], pt - 1)
    _assert_close(rec, ref["rec"], name=f"pup({shape}, t={pt})")


# -----------------------------------------------------------------------------
# Polyphase decomposition / reconstruction (parametrized over shape)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qpdec_parity(shape, qt):
    ref = _load(f"qpdec_{shape}_{qt}")
    p0, p1 = pc.qpdec(ref["x"], qt)
    _assert_close(p0, ref["p0"], name=f"qpdec({shape}, {qt}) p0")
    _assert_close(p1, ref["p1"], name=f"qpdec({shape}, {qt}) p1")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qprec_parity(shape, qt):
    ref = _load(f"qprec_{shape}_{qt}")
    x = pc.qprec(ref["p0"], ref["p1"], qt)
    _assert_close(x, ref["x_rec"], name=f"qprec({shape}, {qt})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_ppdec_parity(shape, pt):
    ref = _load(f"ppdec_{shape}_t{pt}")
    p0, p1 = pc.ppdec(ref["x"], pt - 1)
    _assert_close(p0, ref["p0"], name=f"ppdec({shape}, t={pt}) p0")
    _assert_close(p1, ref["p1"], name=f"ppdec({shape}, t={pt}) p1")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pprec_parity(shape, pt):
    ref = _load(f"pprec_{shape}_t{pt}")
    x = pc.pprec(ref["p0"], ref["p1"], pt - 1)
    _assert_close(x, ref["x_rec"], name=f"pprec({shape}, t={pt})")


# -----------------------------------------------------------------------------
# Extension / filtering primitives (parametrized over shape)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", PRIM_SHAPES)
@pytest.mark.parametrize("mode", ["per", "qper_row", "qper_col"])
def test_extend2_parity(shape, mode):
    ref = _load(f"extend2_{shape}_{mode}")
    y = pc.extend2(
        ref["x"],
        int(ref["ru"].item()),
        int(ref["rd"].item()),
        int(ref["cl"].item()),
        int(ref["cr"].item()),
        ref["extmod"].item() if hasattr(ref["extmod"], "item") else ref["extmod"][0],
    )
    _assert_close(y, ref["y"], name=f"extend2({shape}, {mode})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
def test_sefilter2_parity(shape):
    ref = _load(f"sefilter2_{shape}_per")
    y = pc.sefilter2(ref["x"], ref["f1"], ref["f2"], "per")
    _assert_close(y, ref["y"], name=f"sefilter2({shape})")


@pytest.mark.parametrize("shape", PRIM_SHAPES)
def test_efilter2_parity(shape):
    ref = _load(f"efilter2_{shape}_per")
    y = pc.efilter2(ref["x"], ref["f"], "per")
    _assert_close(y, ref["y"], name=f"efilter2({shape})")


# -----------------------------------------------------------------------------
# Laplacian pyramid / wavelet (parametrized over shape)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", LP_SHAPES)
@pytest.mark.parametrize("name,slug", [
    ("9-7", "9_7"),
    ("5-3", "5_3"),
    ("Burt", "Burt"),
])
def test_lpdec_parity(shape, name, slug):
    ref = _load(f"lpdec_{shape}_{slug}")
    c, d = pc.lpdec(ref["x"], ref["h"], ref["g"])
    _assert_close(c, ref["c"], name=f"lpdec({shape}, {name}) c")
    _assert_close(d, ref["d"], name=f"lpdec({shape}, {name}) d")


@pytest.mark.parametrize("shape", LP_SHAPES)
@pytest.mark.parametrize("name,slug", [
    ("9-7", "9_7"),
    ("5-3", "5_3"),
    ("Burt", "Burt"),
])
def test_lprec_parity(shape, name, slug):
    ref = _load(f"lprec_{shape}_{slug}")
    rec = pc.lprec(ref["c"], ref["d"], ref["h"], ref["g"])
    _assert_close(rec, ref["rec"], name=f"lprec({shape}, {name})")


@pytest.mark.parametrize("shape", WFB_SHAPES)
def test_wfb2dec_wfb2rec_parity(shape):
    ref = _load(f"wfb2_{shape}_9_7")
    LL, LH, HL, HH = pc.wfb2dec(ref["x"], ref["h"], ref["g"])
    _assert_close(LL, ref["LL"], name=f"wfb2dec({shape}) LL")
    _assert_close(LH, ref["LH"], name=f"wfb2dec({shape}) LH")
    _assert_close(HL, ref["HL"], name=f"wfb2dec({shape}) HL")
    _assert_close(HH, ref["HH"], name=f"wfb2dec({shape}) HH")
    rec = pc.wfb2rec(LL, LH, HL, HH, ref["h"], ref["g"])
    _assert_close(rec, ref["rec"], name=f"wfb2rec({shape})")


# -----------------------------------------------------------------------------
# DFB ladder (pkva) and general (cd, 9-7)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", DFB_SHAPES)
@pytest.mark.parametrize("nlev", [1, 2, 3])
def test_dfbdec_l_parity(shape, nlev):
    ref = _load(f"dfb_l_pkva_{shape}_n{nlev}")
    y = pc.dfbdec_l(ref["x"], "pkva", nlev)
    assert len(y) == 2 ** nlev
    for k in range(2 ** nlev):
        _assert_close(y[k], ref[f"y_{k+1}"],
                      name=f"dfbdec_l({shape}, n={nlev}) y[{k}]")
    rec = pc.dfbrec_l(y, "pkva")
    _assert_close(rec, ref["rec"], name=f"dfbrec_l({shape}, n={nlev})")


@pytest.mark.parametrize("shape", DFB_SHAPES)
@pytest.mark.parametrize("nm,slug", [("cd", "cd"), ("9-7", "9_7")])
@pytest.mark.parametrize("nlev", [1, 2, 3])
def test_dfbdec_parity(shape, nm, slug, nlev):
    ref = _load(f"dfb_{slug}_{shape}_n{nlev}")
    y = pc.dfbdec(ref["x"], nm, nlev)
    assert len(y) == 2 ** nlev
    for k in range(2 ** nlev):
        _assert_close(
            y[k], ref[f"y_{k+1}"],
            atol=1e-9, rtol=1e-9,
            name=f"dfbdec({shape}, {nm}, n={nlev}) y[{k}]",
        )
    rec = pc.dfbrec(y, nm)
    _assert_close(rec, ref["rec"], atol=1e-9, rtol=1e-9,
                  name=f"dfbrec({shape}, {nm}, n={nlev})")


# -----------------------------------------------------------------------------
# PDFB end-to-end (parametrized over shape)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("shape", DFB_SHAPES)
def test_pdfbdec_pdfbrec_parity(shape):
    ref = _load(f"pdfb_{shape}_9_7_pkva_2_3")
    nlevs = [int(v) for v in ref["nlevs"].ravel()]
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", nlevs)
    _assert_close(y[0], ref["lowpass"], name=f"pdfbdec({shape}) lowpass")
    for L in range(1, len(y)):
        for k in range(len(y[L])):
            _assert_close(
                y[L][k],
                ref[f"layer_{L}_dir_{k+1}"],
                name=f"pdfbdec({shape}) layer={L} dir={k}",
            )
    rec = pc.pdfbrec(y, "9-7", "pkva")
    _assert_close(rec, ref["rec"], name=f"pdfbrec({shape})")


@pytest.mark.parametrize("shape", DFB_SHAPES)
def test_pdfb2vec_parity(shape):
    ref = _load(f"pdfb_{shape}_9_7_pkva_2_3")
    nlevs = [int(v) for v in ref["nlevs"].ravel()]
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", nlevs)
    c, s = pc.pdfb2vec(y)
    _assert_close(c, ref["c"], name=f"pdfb2vec({shape}) c")
    # MATLAB s uses 1-based layer/dir indices; Python uses 0-based.
    # Sizes (cols 3-4 in MATLAB, 2-4 in Python) should match exactly.
    np.testing.assert_array_equal(s[:, 2:], ref["s"][:, 2:].astype(int))


# -----------------------------------------------------------------------------
# SNR
# -----------------------------------------------------------------------------

def test_snr_parity():
    ref = _load("snr_demo")
    r = pc.snr(ref["in"], ref["est"])
    np.testing.assert_allclose(r, float(ref["r"].item()), atol=1e-10)


# -----------------------------------------------------------------------------
# showpdfb (full coefficient pyramid display)
# -----------------------------------------------------------------------------

def test_showpdfb_auto2_parity():
    ref = _load("showpdfb_auto2")
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", [2, 3])
    img = pc.showpdfb(y, scaleMode="auto2")
    _assert_close(img, ref["displayIm"], name="showpdfb auto2")


def test_showpdfb_auto1_parity():
    ref = _load("showpdfb_auto1")
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", [2, 3])
    img = pc.showpdfb(y, scaleMode="auto1")
    _assert_close(img, ref["displayIm"], name="showpdfb auto1")


def test_showpdfb_threshold_parity():
    ref = _load("showpdfb_thresh200")
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", [2, 3])
    img = pc.showpdfb(y, scaleMode=200)
    _assert_close(img, ref["displayIm"], name="showpdfb threshold=200")


def test_showpdfb_auto3_with_wavelet_parity():
    ref = _load("showpdfb_auto3_wavelet")
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", [0, 3])
    img = pc.showpdfb(y, scaleMode="auto3")
    _assert_close(img, ref["displayIm"], name="showpdfb auto3 with wavelet")
