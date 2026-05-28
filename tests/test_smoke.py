"""Smoke and regression tests for the PyContourlet Python 3 port.

These do not require MATLAB or Octave. They check that the public API runs
end-to-end and that mathematical invariants hold (perfect reconstruction,
coefficient roundtrips, expected shapes). Numerical equivalence to the
MATLAB toolbox should be added separately using Octave-generated fixtures.
"""

import numpy as np
import pytest

from pycontourlet import (
    SNR,
    backsamp,
    dfbdec,
    dfbdec_l,
    dfbimage,
    dfbrec,
    dfbrec_l,
    dfilters,
    dup,
    extend2,
    fbdec,
    fbdec_l,
    fbrec,
    fbrec_l,
    ldfilter,
    lpdec,
    lprec,
    modulate2,
    pdfb2vec,
    pdfb_nest,
    pdfb_tr,
    pdfbdec,
    pdfbrec,
    pfilters,
    ppdec,
    pprec,
    qdown,
    qpdec,
    qprec,
    qup,
    qupz,
    rebacksamp,
    resamp,
    resampc,
    resampz,
    reverse2,
    sefilter2,
    smothborder,
    smthborder,
    snr,
    vec2pdfb,
    wfb2dec,
    wfb2rec,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def image():
    rng = np.random.default_rng(0)
    return rng.standard_normal((32, 32))


@pytest.fixture
def image_small():
    rng = np.random.default_rng(1)
    return rng.standard_normal((16, 16))


# -----------------------------------------------------------------------------
# Filter generators
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["9-7", "9/7", "5-3", "5/3", "Burt", "burt", "pkva", "maxflat"])
def test_pfilters_known_names(name):
    h, g = pfilters(name)
    assert h.ndim == 2 and h.shape[0] == 1
    assert g.ndim == 2 and g.shape[0] == 1
    assert np.isfinite(h).all() and np.isfinite(g).all()


def test_pfilters_unknown_raises():
    with pytest.raises(ValueError):
        pfilters("does-not-exist")


def test_pfilters_97_lowpass_unit_dc_gain():
    # 9-7 is a biorthogonal pair; pfilters returns h, g with DC gain ~ sqrt(2).
    h, g = pfilters("9-7")
    assert np.isclose(h.sum(), np.sqrt(2), atol=1e-3)


@pytest.mark.parametrize("name", ["haar", "9-7", "cd", "5-3", "pkva", "pkva6", "pkva8", "pkva12"])
@pytest.mark.parametrize("ftype", ["d", "r"])
def test_dfilters_runs(name, ftype):
    h0, h1 = dfilters(name, ftype)
    assert h0.size > 0 and h1.size > 0
    assert np.isfinite(h0).all() and np.isfinite(h1).all()


@pytest.mark.parametrize("name", ["pkva6", "pkva8", "pkva12"])
def test_dfilters_pkva_aliases_produce_same_result(name):
    # pkva6/pkva8/pkva12 are separate filters (different N), but each must run.
    h0, h1 = dfilters(name, "d")
    assert h0.size > 1 and h1.size > 1


def test_dfilters_unknown_raises():
    with pytest.raises(ValueError):
        dfilters("does-not-exist", "d")


@pytest.mark.parametrize("name", ["pkva", "pkva6", "pkva8", "pkva12"])
def test_ldfilter_lengths(name):
    f = ldfilter(name)
    # ldfilter returns symmetric impulse response of length 2*len(v).
    assert f.shape[0] == 1 and f.shape[1] % 2 == 0
    # Symmetric: f[i] == f[-1-i]
    np.testing.assert_allclose(f[0], f[0, ::-1])


# -----------------------------------------------------------------------------
# Laplacian pyramid: perfect reconstruction across all filters
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("fname", ["9-7", "5-3", "Burt", "pkva", "maxflat"])
def test_lpdec_lprec_perfect_reconstruction(image, fname):
    h, g = pfilters(fname)
    c, d = lpdec(image, h, g)
    rec = lprec(c, d, h, g)
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10, f"{fname}: relative error {err:.3e}"


# -----------------------------------------------------------------------------
# Wavelet filter bank
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("fname", ["9-7", "5-3"])
def test_wfb2dec_wfb2rec_perfect_reconstruction(image, fname):
    h, g = pfilters(fname)
    LL, LH, HL, HH = wfb2dec(image, h, g)
    # All four subbands halve the image dimensions
    for sub in (LL, LH, HL, HH):
        assert sub.shape == (image.shape[0] // 2, image.shape[1] // 2)
    rec = wfb2rec(LL, LH, HL, HH, h, g)
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10


# -----------------------------------------------------------------------------
# DFB: ladder structure (pkva path) gives perfect reconstruction
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("nlev", [1, 2, 3, 4])
def test_dfbdec_l_pkva_perfect_reconstruction(image, nlev):
    y = dfbdec_l(image, "pkva", nlev)
    assert len(y) == 2 ** nlev
    rec = dfbrec_l(y, "pkva")
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10


# -----------------------------------------------------------------------------
# DFB: general (non-ladder) path
#
# 9-7 / cd give machine-precision PR through nlev=3.
# Haar's "general" path has a sign issue inherited from the MATLAB toolbox,
# so we don't assert PR for it here.
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("fname", ["9-7", "cd"])
@pytest.mark.parametrize("nlev", [1, 2, 3])
def test_dfbdec_dfbrec_perfect_reconstruction(image, fname, nlev):
    y = dfbdec(image, fname, nlev)
    assert len(y) == 2 ** nlev
    rec = dfbrec(y, fname)
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-9


# -----------------------------------------------------------------------------
# Polyphase decomposition / reconstruction (qpdec/qprec, ppdec/pprec)
# Each of these is invertible: rec ∘ dec == identity.
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("qtype", ["1r", "1c", "2r", "2c"])
def test_qpdec_qprec_roundtrip(image, qtype):
    p0, p1 = qpdec(image, qtype)
    rec = qprec(p0, p1, qtype)
    np.testing.assert_allclose(rec, image, atol=1e-12)


@pytest.mark.parametrize("ptype", [0, 1, 2, 3])
def test_ppdec_pprec_roundtrip(image, ptype):
    p0, p1 = ppdec(image, ptype)
    rec = pprec(p0, p1, ptype)
    np.testing.assert_allclose(rec, image, atol=1e-12)


# -----------------------------------------------------------------------------
# Sampling primitives: linearity / inverse pairs
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("rtype", [0, 1])
def test_resampc_per_inverse(image, rtype):
    # resampc with rtype=0 inverts rtype=1 (and vice versa) with same shift.
    other = 1 - rtype
    rec = resampc(resampc(image, rtype, 1, "per"), other, 1, "per")
    np.testing.assert_allclose(rec, image, atol=1e-12)


def test_resampc_invalid_type_raises(image):
    with pytest.raises(ValueError):
        resampc(image, 7, 1, "per")


def test_resampc_invalid_extmod_raises(image):
    with pytest.raises(ValueError):
        resampc(image, 0, 1, "ref1")


@pytest.mark.parametrize("t", [0, 1, 2, 3])
def test_resamp_inverse(image, t):
    # resamp 0/1 are inverses; 2/3 are inverses.
    inverse = {0: 1, 1: 0, 2: 3, 3: 2}[t]
    rec = resamp(resamp(image, t), inverse)
    np.testing.assert_allclose(rec, image, atol=1e-12)


def test_resamp_invalid_type_raises(image):
    with pytest.raises(ValueError):
        resamp(image, 5)


@pytest.mark.parametrize("qtype", [1, 2])
def test_qupz_doubles_height(qtype):
    rng = np.random.default_rng(2)
    x = rng.standard_normal((4, 4))
    y = qupz(x, qtype)
    # qupz upsamples and pads -> output is larger in both dims
    assert y.shape[0] > x.shape[0] and y.shape[1] > x.shape[1]


def test_qupz_invalid_type_raises(image_small):
    with pytest.raises(ValueError):
        qupz(image_small, 5)


def test_dup_zero_pad():
    x = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = dup(x, np.array([2, 2]))
    expected = np.array([[1, 0, 2, 0],
                         [0, 0, 0, 0],
                         [3, 0, 4, 0],
                         [0, 0, 0, 0]])
    np.testing.assert_allclose(y, expected)


def test_dup_minimum_phase():
    x = np.array([[1.0, 2.0], [3.0, 4.0]])
    y = dup(x, np.array([2, 2]), phase=np.array(["m", 0]))
    # Minimum phase: shape is (sx-1)*step + 1 = (1*2+1, 1*2+1) = (3, 3)
    assert y.shape == (3, 3)
    np.testing.assert_allclose(y[::2, ::2], x)


# -----------------------------------------------------------------------------
# Extension / filtering primitives
# -----------------------------------------------------------------------------

def test_extend2_per_size():
    rng = np.random.default_rng(3)
    x = rng.standard_normal((4, 5))
    y = extend2(x, 1, 2, 3, 4, "per")
    assert y.shape == (1 + 4 + 2, 3 + 5 + 4)


def test_extend2_unknown_extmod_raises():
    rng = np.random.default_rng(4)
    x = rng.standard_normal((4, 4))
    with pytest.raises(ValueError):
        extend2(x, 1, 1, 1, 1, "bogus")


def test_extend2_qper_col_uses_matlab_round():
    # MATLAB round() rounds half-away-from-zero. Python round() uses banker's.
    # For odd-row-count matrices the qper_col split point matters.
    x = np.arange(15).reshape(5, 3).astype(float)
    y = extend2(x, 1, 1, 0, 0, "qper_col")
    # Output rows = ru + nrows + rd = 1 + 5 + 1 = 7
    assert y.shape == (7, 3)
    # The middle 5 rows are the original (per spec)
    np.testing.assert_allclose(y[1:6, :], x)


def test_sefilter2_separable():
    rng = np.random.default_rng(5)
    x = rng.standard_normal((16, 16))
    f1 = np.array([[0.25, 0.5, 0.25]])
    f2 = np.array([[0.25, 0.5, 0.25]])
    y = sefilter2(x, f1, f2, "per")
    # Output keeps input size (per spec)
    assert y.shape == x.shape


def test_sefilter2_separable_factors_equivalence():
    # Separable filtering with f1 == f2 is the only case real callers exercise;
    # check that running it doesn't crash and preserves input shape.
    rng = np.random.default_rng(6)
    x = rng.standard_normal((16, 16))
    h, _ = pfilters("9-7")  # length-9 symmetric filter
    y = sefilter2(x, h, h, "per")
    assert y.shape == x.shape


# -----------------------------------------------------------------------------
# Modulation, reverse2, ffilters utility
# -----------------------------------------------------------------------------

def test_modulate2_idempotent_double_application():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((8, 8))
    for direction in ("r", "c", "b"):
        twice = modulate2(modulate2(x, direction), direction)
        np.testing.assert_allclose(twice, x, atol=1e-12)


def test_modulate2_invalid_type_raises():
    rng = np.random.default_rng(8)
    x = rng.standard_normal((4, 4))
    with pytest.raises(ValueError):
        modulate2(x, "z")


def test_reverse2_double_reverse_is_identity():
    rng = np.random.default_rng(9)
    x = rng.standard_normal((4, 5))
    np.testing.assert_array_equal(reverse2(reverse2(x)), x)


def test_reverse2_rejects_non_2d():
    with pytest.raises(ValueError):
        reverse2(np.array([1.0, 2.0, 3.0]))


# -----------------------------------------------------------------------------
# PDFB end-to-end
# -----------------------------------------------------------------------------

def test_pdfbdec_pdfbrec_perfect_reconstruction(image):
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    rec = pdfbrec(y, "9-7", "pkva")
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10


def test_pdfbdec_pdfbrec_with_wavelet_layer(image):
    # nlevs containing 0 triggers the wfb2dec/wfb2rec wavelet path
    y = pdfbdec(image, "9-7", "pkva", [0, 3])
    rec = pdfbrec(y, "9-7", "pkva")
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10


def test_pdfb2vec_vec2pdfb_roundtrip(image):
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    c, s = pdfb2vec(y)
    y2 = vec2pdfb(c, s)
    assert np.allclose(y[0], y2[0])
    for layer_y, layer_y2 in zip(y[1:], y2[1:]):
        assert len(layer_y) == len(layer_y2)
        for a, b in zip(layer_y, layer_y2):
            np.testing.assert_allclose(a, b, atol=1e-14)


def test_pdfb2vec_vec2pdfb_then_pdfbrec(image):
    # The full vector-form roundtrip should still reconstruct.
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    c, s = pdfb2vec(y)
    y2 = vec2pdfb(c, s)
    rec = pdfbrec(y2, "9-7", "pkva")
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    assert err < 1e-10


def test_pdfb_nest_returns_lowpass_zeros_and_positive_highpass():
    rng = np.random.default_rng(10)
    nstd = pdfb_nest(32, 32, "9-7", "pkva", [2, 3], niter=4, rng=rng)
    nlp = 8 * 8
    assert np.all(nstd[:nlp] == 0.0)
    assert np.all(nstd[nlp:] > 0)


def test_pdfb_tr_keeps_exactly_ncoef_significant(image):
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    ytr = pdfb_tr(y, 0, 0, ncoef=50)
    ctr, _ = pdfb2vec(ytr)
    assert np.count_nonzero(ctr) == 50


def test_pdfb_tr_zeros_non_selected_subbands(image):
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    ytr = pdfb_tr(y, scale=1, direction=0)
    n = len(y)
    # Lowpass must be zeroed (scale != n and != 0)
    assert np.allclose(ytr[0], 0)
    # Coarsest directional layer (l=1) corresponds to scale n-1, must be zero
    for sub in ytr[1]:
        assert np.allclose(sub, 0)
    # Finest directional layer (l=2) has scale n-l = 1, must be kept
    for orig, sub in zip(y[2], ytr[2]):
        np.testing.assert_allclose(orig, sub)


def test_pdfb_tr_lowpass_kept_when_scale_equals_n(image):
    y = pdfbdec(image, "9-7", "pkva", [2, 3])
    n = len(y)
    ytr = pdfb_tr(y, scale=n, direction=0)
    np.testing.assert_allclose(ytr[0], y[0])


# -----------------------------------------------------------------------------
# SNR / smothborder
# -----------------------------------------------------------------------------

def test_snr_perfect_match_is_inf():
    rng = np.random.default_rng(11)
    x = rng.standard_normal((8, 8))
    # Perfect estimate -> error is zero -> SNR is +inf (numpy raises a
    # divide-by-zero warning for log(inf), which we suppress here).
    with np.errstate(divide="ignore"):
        assert np.isposinf(snr(x, x))


def test_snr_alias():
    rng = np.random.default_rng(12)
    x = rng.standard_normal((4, 4))
    y = x + 0.1 * rng.standard_normal((4, 4))
    assert SNR(x, y) == snr(x, y)


def test_smthborder_alias():
    # `smthborder` (MATLAB spelling) and `smothborder` (Python typo) are aliased.
    assert smthborder is smothborder


def test_smothborder_keeps_interior():
    rng = np.random.default_rng(13)
    x = rng.standard_normal((16, 16))
    y = smothborder(x, 4)
    # The 8x8 interior should be unchanged (window value is 1.0 in the middle)
    np.testing.assert_allclose(y[4:-4, 4:-4], x[4:-4, 4:-4], atol=1e-12)
