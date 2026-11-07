"""Render layout images with KLayout (batch mode) from the project venv.

render([(component, out_png, box_or_None), ...]) writes each component to a
temporary GDS, writes gdsfactory's KLayout layer colours (.lyp) next to it, and runs
klayout_render.py inside KLayout. Set KLAYOUT to the executable if it is not at the
default macOS location or on PATH.
"""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

import gdsfactory as gf
from gdsfactory.technology import LayerViews

HERE = pathlib.Path(__file__).parent.resolve()


def _klayout() -> str:
    for c in (os.environ.get("KLAYOUT"), "/Applications/KLayout/klayout.app/Contents/MacOS/klayout",
              shutil.which("klayout")):
        if c and pathlib.Path(c).exists():
            return c
    raise RuntimeError("KLayout not found: set KLAYOUT to its executable")


def render(items, width: int = 1600, margin: float = 0.04) -> None:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="klayout_render_"))
    lyp = tmp / "layers.lyp"
    LayerViews(filepath=gf.get_active_pdk().layer_views).to_lyp(lyp)
    jobs = []
    for k, (comp, out, box) in enumerate(items):
        gds = tmp / f"cell{k}.gds"
        comp.write_gds(gds)
        b = comp.dbbox(); bb = ((b.left, b.bottom), (b.right, b.top))
        if box is None:
            (x1, y1), (x2, y2) = bb
            dx, dy = (x2 - x1) * margin, (y2 - y1) * margin
            d = max(dx, dy, 1.0)
            box = [x1 - d, y1 - d, x2 + d, y2 + d]
        w = box[2] - box[0]; h = box[3] - box[1]
        height = int(min(1400, max(300, width * h / w)))
        jobs.append({"gds": str(gds), "out": str(pathlib.Path(out).resolve()), "lyp": str(lyp),
                     "width": width, "height": height, "box": box})
    jf = tmp / "jobs.json"
    jf.write_text(json.dumps(jobs))
    r = subprocess.run([_klayout(), "-b", "-r", str(HERE / "klayout_render.py"), "-rd", f"jobs={jf}"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
