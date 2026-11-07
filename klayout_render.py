"""Render layout images with KLayout itself, as KLayout shows them.

Runs inside KLayout's batch mode, not in the project venv:

    klayout -b -r klayout_render.py -rd jobs=/abs/path/jobs.json

jobs.json is a list of {"gds", "out", "lyp", "width", "height", "box" (optional,
[x1, y1, x2, y2] in um), "cell" (optional, default: the largest top cell)}.
figures.py and chip.py write the jobs file and call this script.
"""
import json

import pya

for j in json.load(open(jobs)):  # noqa: F821  (`jobs` is passed with -rd)
    lv = pya.LayoutView()
    lv.set_config("background-color", "#ffffff")
    lv.set_config("grid-visible", "true")
    lv.set_config("grid-show-ruler", "true")
    lv.set_config("grid-color", "#d0d4da")
    lv.set_config("grid-ruler-color", "#333333")
    lv.set_config("text-visible", "false")
    idx = lv.load_layout(j["gds"], True)
    layout = lv.cellview(idx).layout()
    tops = [c for c in layout.top_cells() if not c.name.startswith("$$$")]
    cell = next((c for c in tops if c.name == j.get("cell")), None) or max(tops, key=lambda c: c.dbbox().area())
    lv.cellview(idx).cell = cell
    lv.load_layer_props(j["lyp"])
    lv.add_missing_layers()
    lv.max_hier()
    if j.get("box"):
        lv.zoom_box(pya.DBox(*j["box"]))
    else:
        lv.zoom_fit()
    lv.save_image_with_options(j["out"], j.get("width", 1600), j.get("height", 1000), 2, 2, 0, pya.DBox(), False)
    print("rendered", j["out"])
