"""One convention for every raster figure in the study.

The gallery shows figures at about 720 CSS pixels wide. Every figure is drawn
7.6 inches wide at 170 dpi (1292 px) and scaled by 0.56 for display, so the
sizes below give on-screen text of roughly 14 to 16 px, the same as the SVG
figures and the page body.
"""
import matplotlib as mpl

WIDTH_IN = 7.6
DPI = 170

mpl.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
    "figure.titlesize": 13,
    "savefig.dpi": DPI,
})


def size(w, h):
    """Rescale a (w, h) inch request to the standard width, keeping its aspect."""
    return (WIDTH_IN, WIDTH_IN * h / w)
