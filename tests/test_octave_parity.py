"""Numerical parity tests against MATLAB toolbox outputs (via Octave).

Each test loads a .mat fixture saved by tests/octave/generate_fixtures.m and
asserts that the Python implementation produces the same numerical output.

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
# Filter generators
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
# Sampling primitives
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("rt", [1, 2])
@pytest.mark.parametrize("sh", [1, 2])
def test_resampc_parity(rt, sh):
    ref = _load(f"resampc_t{rt}_s{sh}")
    # MATLAB rtype 1/2 -> Python 0/1
    y = pc.resampc(ref["x"], rt - 1, sh, "per")
    _assert_close(y, ref["y"], name=f"resampc(t={rt}, s={sh})")


@pytest.mark.parametrize("rt", [1, 2, 3, 4])
def test_resamp_parity(rt):
    ref = _load(f"resamp_t{rt}")
    # MATLAB type 1..4 -> Python 0..3
    y = pc.resamp(ref["x"], rt - 1)
    _assert_close(y, ref["y"], name=f"resamp(t={rt})")


@pytest.mark.parametrize("rt", [1, 2, 3, 4])
def test_resampz_parity(rt):
    ref = _load(f"resampz_t{rt}")
    y = pc.resampz(ref["x"], rt - 1)
    _assert_close(y, ref["y"], name=f"resampz(t={rt})")


@pytest.mark.parametrize("tp", [1, 2])
def test_qupz_parity(tp):
    ref = _load(f"qupz_t{tp}")
    y = pc.qupz(ref["x"], tp)
    _assert_close(y, ref["y"], name=f"qupz(t={tp})")


def test_dup_parity_zero():
    ref = _load("dup_2x2_zero")
    y = pc.dup(ref["x"], np.array([2, 2]), np.array([0, 0]))
    _assert_close(y, ref["y"], name="dup zero-phase")


def test_dup_parity_minimum():
    ref = _load("dup_minimum")
    y = pc.dup(ref["x"], np.array([2, 2]), phase=np.array(["m", 0]))
    _assert_close(y, ref["y"], name="dup minimum-phase")


@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qdown_parity(qt):
    ref = _load(f"qdown_{qt}")
    y = pc.qdown(ref["x"], qt)
    _assert_close(y, ref["y"], name=f"qdown({qt})")


@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qup_parity(qt):
    ref = _load(f"qup_{qt}")
    rec = pc.qup(ref["y"], qt)
    _assert_close(rec, ref["rec"], name=f"qup({qt})")


@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pdown_parity(pt):
    ref = _load(f"pdown_t{pt}")
    y = pc.pdown(ref["x"], pt - 1)
    _assert_close(y, ref["y"], name=f"pdown(t={pt})")


@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pup_parity(pt):
    ref = _load(f"pup_t{pt}")
    rec = pc.pup(ref["y"], pt - 1)
    _assert_close(rec, ref["rec"], name=f"pup(t={pt})")


# -----------------------------------------------------------------------------
# Polyphase decomposition / reconstruction
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qpdec_parity(qt):
    ref = _load(f"qpdec_{qt}")
    p0, p1 = pc.qpdec(ref["x"], qt)
    _assert_close(p0, ref["p0"], name=f"qpdec({qt}) p0")
    _assert_close(p1, ref["p1"], name=f"qpdec({qt}) p1")


@pytest.mark.parametrize("qt", ["1r", "1c", "2r", "2c"])
def test_qprec_parity(qt):
    ref = _load(f"qprec_{qt}")
    x = pc.qprec(ref["p0"], ref["p1"], qt)
    _assert_close(x, ref["x_rec"], name=f"qprec({qt})")


@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_ppdec_parity(pt):
    ref = _load(f"ppdec_t{pt}")
    p0, p1 = pc.ppdec(ref["x"], pt - 1)
    _assert_close(p0, ref["p0"], name=f"ppdec({pt}) p0")
    _assert_close(p1, ref["p1"], name=f"ppdec({pt}) p1")


@pytest.mark.parametrize("pt", [1, 2, 3, 4])
def test_pprec_parity(pt):
    ref = _load(f"pprec_t{pt}")
    x = pc.pprec(ref["p0"], ref["p1"], pt - 1)
    _assert_close(x, ref["x_rec"], name=f"pprec({pt})")


# -----------------------------------------------------------------------------
# Extension / filtering primitives
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("mode,name", [
    ("per", "extend2_per"),
    ("qper_row", "extend2_qper_row"),
    ("qper_col", "extend2_qper_col"),
])
def test_extend2_parity(mode, name):
    ref = _load(name)
    y = pc.extend2(
        ref["x"],
        int(ref["ru"].item()),
        int(ref["rd"].item()),
        int(ref["cl"].item()),
        int(ref["cr"].item()),
        ref["extmod"].item() if hasattr(ref["extmod"], "item") else ref["extmod"][0],
    )
    _assert_close(y, ref["y"], name=f"extend2({mode})")


def test_sefilter2_parity():
    ref = _load("sefilter2_per")
    y = pc.sefilter2(ref["x"], ref["f1"], ref["f2"], "per")
    _assert_close(y, ref["y"], name="sefilter2")


def test_efilter2_parity():
    ref = _load("efilter2_per")
    y = pc.efilter2(ref["x"], ref["f"], "per")
    _assert_close(y, ref["y"], name="efilter2")


# -----------------------------------------------------------------------------
# Laplacian pyramid / wavelet
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("name,slug", [
    ("9-7", "9_7"),
    ("5-3", "5_3"),
    ("Burt", "Burt"),
])
def test_lpdec_parity(name, slug):
    ref = _load(f"lpdec_{slug}")
    c, d = pc.lpdec(ref["x"], ref["h"], ref["g"])
    _assert_close(c, ref["c"], name=f"lpdec({name}) c")
    _assert_close(d, ref["d"], name=f"lpdec({name}) d")


@pytest.mark.parametrize("name,slug", [
    ("9-7", "9_7"),
    ("5-3", "5_3"),
    ("Burt", "Burt"),
])
def test_lprec_parity(name, slug):
    ref = _load(f"lprec_{slug}")
    rec = pc.lprec(ref["c"], ref["d"], ref["h"], ref["g"])
    _assert_close(rec, ref["rec"], name=f"lprec({name})")


def test_wfb2dec_wfb2rec_parity():
    ref = _load("wfb2_9_7")
    LL, LH, HL, HH = pc.wfb2dec(ref["x"], ref["h"], ref["g"])
    _assert_close(LL, ref["LL"], name="wfb2dec LL")
    _assert_close(LH, ref["LH"], name="wfb2dec LH")
    _assert_close(HL, ref["HL"], name="wfb2dec HL")
    _assert_close(HH, ref["HH"], name="wfb2dec HH")
    rec = pc.wfb2rec(LL, LH, HL, HH, ref["h"], ref["g"])
    _assert_close(rec, ref["rec"], name="wfb2rec")


# -----------------------------------------------------------------------------
# DFB ladder (pkva) and general (cd, 9-7)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("nlev", [1, 2, 3])
def test_dfbdec_l_parity(nlev):
    ref = _load(f"dfb_l_pkva_n{nlev}")
    y = pc.dfbdec_l(ref["x"], "pkva", nlev)
    assert len(y) == 2 ** nlev
    for k in range(2 ** nlev):
        _assert_close(y[k], ref[f"y_{k+1}"], name=f"dfbdec_l n={nlev} y[{k}]")
    rec = pc.dfbrec_l(y, "pkva")
    _assert_close(rec, ref["rec"], name=f"dfbrec_l n={nlev}")


@pytest.mark.parametrize("nm,slug", [("cd", "cd"), ("9-7", "9_7")])
@pytest.mark.parametrize("nlev", [1, 2, 3])
def test_dfbdec_parity(nm, slug, nlev):
    ref = _load(f"dfb_{slug}_n{nlev}")
    y = pc.dfbdec(ref["x"], nm, nlev)
    assert len(y) == 2 ** nlev
    for k in range(2 ** nlev):
        _assert_close(
            y[k], ref[f"y_{k+1}"],
            atol=1e-9, rtol=1e-9,
            name=f"dfbdec({nm}, n={nlev}) y[{k}]",
        )
    rec = pc.dfbrec(y, nm)
    _assert_close(rec, ref["rec"], atol=1e-9, rtol=1e-9, name=f"dfbrec({nm}, n={nlev})")


# -----------------------------------------------------------------------------
# PDFB end-to-end
# -----------------------------------------------------------------------------

def test_pdfbdec_pdfbrec_parity():
    ref = _load("pdfb_9_7_pkva_2_3")
    nlevs = [int(v) for v in ref["nlevs"].ravel()]
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", nlevs)
    _assert_close(y[0], ref["lowpass"], name="pdfbdec lowpass")
    for L in range(1, len(y)):
        for k in range(len(y[L])):
            _assert_close(
                y[L][k],
                ref[f"layer_{L}_dir_{k+1}"],
                name=f"pdfbdec layer={L} dir={k}",
            )
    rec = pc.pdfbrec(y, "9-7", "pkva")
    _assert_close(rec, ref["rec"], name="pdfbrec")


def test_pdfb2vec_parity():
    ref = _load("pdfb_9_7_pkva_2_3")
    nlevs = [int(v) for v in ref["nlevs"].ravel()]
    y = pc.pdfbdec(ref["x"], "9-7", "pkva", nlevs)
    c, s = pc.pdfb2vec(y)
    _assert_close(c, ref["c"], name="pdfb2vec c")
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
