#!/usr/bin/env python3
"""Report any <text> in an SVG whose rendered box escapes the viewBox.

Overflowing labels are invisible in a browser and silently wrong in print, and
they are not detectable by reading the source. This measures them.

Run:  python chain/check_svg.py
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

IMG = pathlib.Path(__file__).parent / "img"
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1000, "height": 800})
    for f in sorted(IMG.glob("*.svg")):
        pg.goto(f.as_uri())
        pg.wait_for_timeout(150)
        res = pg.evaluate("""() => {
            const svg = document.querySelector('svg');
            const vb = svg.viewBox.baseVal;
            return [...svg.querySelectorAll('text')].map(t => {
                const bb = t.getBBox();
                return {txt: t.textContent.slice(0, 46),
                        x0: Math.round(bb.x), x1: Math.round(bb.x + bb.width),
                        y1: Math.round(bb.y + bb.height),
                        W: vb.width, H: vb.height};
            }).filter(r => r.x1 > r.W - 2 || r.x0 < 2 || r.y1 > r.H - 2);
        }""")
        if res:
            bad += len(res)
            print(f"\n{f.name}  (viewBox {res[0]['W']} x {res[0]['H']})")
            for r in res:
                print(f"   x {r['x0']}..{r['x1']}, bottom {r['y1']}   \"{r['txt']}\"")
        else:
            print(f"{f.name}: ok")
    b.close()
print(f"\n{bad} overflowing label(s)")
sys.exit(1 if bad else 0)
