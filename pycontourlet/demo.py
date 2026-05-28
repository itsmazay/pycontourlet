"""decdemo.py -- contourlet decomposition + nonlinear-approximation demo.

Python port of the MATLAB toolbox demos `decdemo.m` and `nlademo.m`.

Loads a grayscale image, runs the pyramidal directional filter bank,
verifies perfect reconstruction, then demonstrates nonlinear approximation
by retaining a small percentage of the most significant coefficients and
comparing the reconstruction quality (SNR) against the original.

Run interactively:

    python -m pycontourlet [--image PATH] [--no-show] [--out-dir PATH]

By default uses the bundled barbara.png and shows three plots
(input/coefficients/reconstruction). `--no-show` saves PNGs without opening
display windows -- useful for CI / headless environments.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib import resources
from pathlib import Path

import matplotlib
import numpy as np

import pycontourlet as pc

DEFAULT_IMAGE = "barbara.png"
DEFAULT_PFILTER = "9-7"
DEFAULT_DFILTER = "pkva"
DEFAULT_NLEVELS = (0, 0, 4, 5)  # mirrors nlademo.m: coarse-to-fine

NLA_FRACTIONS = (0.05, 0.025, 0.01)  # 5%, 2.5%, 1% of coefficients


def _load_bundled_image(name: str) -> np.ndarray:
    """Load a PNG bundled with the package and return it as float in [0, 1]."""
    import matplotlib.image as mpimg

    with resources.as_file(resources.files("pycontourlet").joinpath("data", name)) as p:
        arr = mpimg.imread(str(p))
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    return arr.astype(np.float64)


def _load_user_image(path: str) -> np.ndarray:
    import matplotlib.image as mpimg

    arr = mpimg.imread(path)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    return arr.astype(np.float64)


def _normalize(im: np.ndarray) -> np.ndarray:
    """matplotlib loads PNGs as 0..1 (float) or 0..255 (uint8). Normalize."""
    if im.max() > 1.5:
        return im / 255.0
    return im


def _pad_to_multiple(im: np.ndarray, factor: int) -> np.ndarray:
    """PDFB requires image dims divisible by 2**max(nlevels). Mirror-pad if not."""
    h, w = im.shape
    new_h = ((h + factor - 1) // factor) * factor
    new_w = ((w + factor - 1) // factor) * factor
    if (new_h, new_w) == (h, w):
        return im
    return np.pad(im, ((0, new_h - h), (0, new_w - w)), mode="reflect")


def _print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _coefficient_count(coeffs: list) -> int:
    """Total scalar coefficients in a PDFB output."""
    n = coeffs[0].size
    for layer in coeffs[1:]:
        for sub in layer:
            n += sub.size
    return n


def _save_or_show(fig, out_path: Path | None, show: bool) -> None:
    if out_path is not None:
        fig.savefig(str(out_path), dpi=120, bbox_inches="tight")
        print(f"  saved {out_path}")
    if show:
        import matplotlib.pyplot as plt

        plt.show()
    else:
        import matplotlib.pyplot as plt

        plt.close(fig)


def run_demo(
    image: np.ndarray,
    pfilter: str = DEFAULT_PFILTER,
    dfilter: str = DEFAULT_DFILTER,
    nlevels: tuple[int, ...] = DEFAULT_NLEVELS,
    nla_fractions: tuple[float, ...] = NLA_FRACTIONS,
    out_dir: Path | None = None,
    show: bool = False,
) -> dict:
    """Run the full decompose / reconstruct / NLA pipeline.

    Returns a dict with the original, reconstructed image, and per-fraction
    NLA reconstructions plus their SNRs.
    """
    import matplotlib.pyplot as plt

    if not show:
        matplotlib.use("Agg", force=True)

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    image = _normalize(image)
    factor = 2 ** max(nlevels) if max(nlevels) > 0 else 2
    image = _pad_to_multiple(image, factor)

    _print_header("PyContourlet decomposition demo")
    print(f"  pfilter:  {pfilter}")
    print(f"  dfilter:  {dfilter}")
    print(f"  nlevels:  {nlevels}")
    print(f"  image:    {image.shape}, range [{image.min():.3f}, {image.max():.3f}]")

    _print_header("1. Forward PDFB")
    coeffs = pc.pdfbdec(image, pfilter, dfilter, list(nlevels))
    n_layers = len(coeffs)
    n_coeffs = _coefficient_count(coeffs)
    n_pixels = image.size
    print(f"  {n_layers} pyramidal layers (1 lowpass + {n_layers - 1} bandpass)")
    print(f"  {n_coeffs} coefficients vs {n_pixels} pixels "
          f"(redundancy {n_coeffs / n_pixels:.3f}x)")
    for i, layer in enumerate(coeffs):
        if i == 0:
            print(f"  layer 0 (lowpass): {layer.shape}")
        else:
            print(f"  layer {i}: {len(layer)} subbands, "
                  f"first shape {layer[0].shape}")

    _print_header("2. Inverse PDFB (perfect reconstruction)")
    rec = pc.pdfbrec(coeffs, pfilter, dfilter)
    err = np.linalg.norm(image - rec) / np.linalg.norm(image)
    print(f"  relative reconstruction error: {err:.3e}")
    print(f"  SNR(input, reconstruction):    {pc.snr(image, rec):.2f} dB")

    _print_header("3. Nonlinear approximation (keep N most significant)")
    nla_results = []
    for frac in nla_fractions:
        n_keep = int(round(n_coeffs * frac))
        coeffs_again = pc.pdfbdec(image, pfilter, dfilter, list(nlevels))
        truncated = pc.pdfb_tr(coeffs_again, 0, 0, ncoef=n_keep)
        nla_rec = pc.pdfbrec(truncated, pfilter, dfilter)
        nla_snr = pc.snr(image, nla_rec)
        print(f"  retained {n_keep:>6d} coefs ({frac*100:5.2f}%):  "
              f"SNR = {nla_snr:6.2f} dB")
        nla_results.append({"frac": frac, "n_keep": n_keep,
                            "rec": nla_rec, "snr": nla_snr})

    _print_header("4. Plotting")
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Input")
    axes[0].axis("off")
    axes[1].imshow(rec, cmap="gray", vmin=0, vmax=1)
    axes[1].set_title(f"Reconstructed (rel.err. {err:.1e})")
    axes[1].axis("off")
    fig.tight_layout()
    _save_or_show(fig, out_dir / "reconstruction.png" if out_dir else None, show)

    fig, axes = plt.subplots(1, len(nla_fractions) + 1, figsize=(4 * (len(nla_fractions) + 1), 4))
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Original")
    axes[0].axis("off")
    for ax, result in zip(axes[1:], nla_results):
        ax.imshow(result["rec"], cmap="gray", vmin=0, vmax=1)
        ax.set_title(
            f"NLA {result['frac']*100:.1f}% ({result['n_keep']} coefs)\n"
            f"SNR {result['snr']:.2f} dB"
        )
        ax.axis("off")
    fig.tight_layout()
    _save_or_show(fig, out_dir / "nla_comparison.png" if out_dir else None, show)

    return {
        "image": image,
        "coeffs": coeffs,
        "rec": rec,
        "rel_err": err,
        "nla": nla_results,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pycontourlet-demo",
        description="Demonstrate the contourlet transform on an image.",
    )
    parser.add_argument(
        "--image", default=None,
        help="Path to a grayscale or RGB image. Defaults to the bundled barbara.png.",
    )
    parser.add_argument(
        "--pfilter", default=DEFAULT_PFILTER,
        help="Pyramidal filter name (default: %(default)s).",
    )
    parser.add_argument(
        "--dfilter", default=DEFAULT_DFILTER,
        help="Directional filter name (default: %(default)s).",
    )
    parser.add_argument(
        "--nlevels", default=",".join(str(n) for n in DEFAULT_NLEVELS),
        help="Comma-separated DFB levels per pyramidal level, coarse to fine "
             "(default: %(default)s).",
    )
    parser.add_argument(
        "--out-dir", default=None,
        help="Directory to save plots into. If omitted, no PNGs are written.",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Open interactive matplotlib windows. Default off (good for CI).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.image:
        image = _load_user_image(args.image)
    else:
        image = _load_bundled_image(DEFAULT_IMAGE)
    nlevels = tuple(int(x) for x in args.nlevels.split(","))
    out_dir = Path(args.out_dir) if args.out_dir else None
    run_demo(
        image=image,
        pfilter=args.pfilter,
        dfilter=args.dfilter,
        nlevels=nlevels,
        out_dir=out_dir,
        show=args.show,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
