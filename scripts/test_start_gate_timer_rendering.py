"""Offline timer bounds check using real Pillow glyphs; no matrix/GPIO imports.

Run: python3 scripts/test_start_gate_timer_rendering.py
"""
import ast
from functools import lru_cache
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = {
    "safe_load_font", "safe_load_mono_font", "text_bbox",
    "fit_start_gate_timer_font", "draw_text_centered_fixed", "render_start_gate_frame",
}
source = ast.parse((ROOT / "load_effect3.py").read_text())
definitions = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
assert len(definitions) == len(FUNCTIONS)
NOW = 1_000_000_000
renderer = dict(
    os=os, lru_cache=lru_cache, BASE_DIR=str(ROOT),
    Image=Image, ImageDraw=ImageDraw, ImageFont=ImageFont,
    time=SimpleNamespace(time=lambda: NOW / 1000),
    matrix=SimpleNamespace(set_enhance=lambda value: None), CENTER_Y_OFFSET=-4,
)
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(ROOT / "load_effect3.py"), "exec"), renderer)
production_loader = renderer["safe_load_mono_font"]
FONT_LOADERS = [("production", production_loader),
                ("bundled proportional fallback", lambda size: ImageFont.truetype(str(ROOT / "fonts/dosis.ttf"), size))]
for candidate in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                  "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"]:
    if os.path.exists(candidate):
        FONT_LOADERS.append((candidate, lambda size, filename=candidate: ImageFont.truetype(filename, size)))


class StartGateTimerRendering(unittest.TestCase):
    def test_timer_bounds_and_size_transitions(self):
        # Includes the repository default, typical tiled displays, and wider overrides.
        dimensions = [(16, 16), (32, 32), (48, 48), (64, 48), (96, 48), (288, 16)]
        times = ["0:00", "5:17", "15:00", "59:59", "99:59", "120:00",
                 "999:59", "1200:00", "10000:00", "123456789:59"]
        for label, loader in FONT_LOADERS:
            renderer["safe_load_mono_font"] = loader
            renderer["fit_start_gate_timer_font"].cache_clear()
            for width, height in dimensions:
                renderer.update(pixel_width=width, pixel_height=height)
                top, region_height = 4, min(22, height - 4)
                sizes = {}
                for mode in ["timer", "timerDown"]:
                    for value in times:
                        minutes, seconds = map(int, value.split(":"))
                        total_seconds = minutes * 60 + seconds
                        text = value if mode == "timer" else f"{minutes:02d}:{seconds:02d}"
                        payload = dict(mode="raceInfo", bigMode=mode, showTimer=True,
                                       timerStartMs=NOW - total_seconds * 1000 if mode == "timer" else NOW - 1000,
                                       timerEndMs=NOW + total_seconds * 1000)
                        with self.subTest(font=label, dimensions=(width, height), mode=mode, text=text):
                            frame = renderer["render_start_gate_frame"](payload)
                            bounds = frame.getbbox()
                            self.assertIsNotNone(bounds)
                            left, ink_top, right, bottom = bounds
                            self.assertGreaterEqual(left, 2)
                            self.assertLessEqual(right, width - 2)
                            self.assertGreaterEqual(ink_top, top)
                            self.assertLessEqual(bottom, top + region_height)
                            self.assertLessEqual(abs(left + right - width), 1)
                            self.assertLessEqual(abs(ink_top + bottom - (2 * top + region_height)), 1)
                            shape = "".join("0" if ch.isdigit() else ch for ch in text)
                            font, _ = renderer["fit_start_gate_timer_font"](shape, width, region_height)
                            sizes[(mode, value)] = getattr(font, "size", None)
                            bboxes = {ch: font.getbbox(ch) for ch in "0123456789:"}
                            digit_width = max(bboxes[ch][2] - bboxes[ch][0] for ch in "0123456789")
                            measured_width = (len(text) - 1) * digit_width + bboxes[":"][2] - bboxes[":"][0]
                            measured_height = max(b[3] for b in bboxes.values()) - min(b[1] for b in bboxes.values())
                            self.assertLessEqual(measured_width, width - 4)
                            self.assertLessEqual(measured_height, region_height)
                            # Every larger supported size must exceed the format's
                            # measured width or height, including the widest digit.
                            for size in range(font.size + 1, 37):
                                larger = font.font_variant(size=size)
                                bboxes = {ch: larger.getbbox(ch) for ch in "0123456789:"}
                                digit_width = max(bboxes[ch][2] - bboxes[ch][0] for ch in "0123456789")
                                required_width = (len(text) - 1) * digit_width + bboxes[":"][2] - bboxes[":"][0]
                                required_height = max(b[3] for b in bboxes.values()) - min(b[1] for b in bboxes.values())
                                self.assertTrue(required_width > width - 4 or required_height > region_height)
                for mode in ["timer", "timerDown"]:
                    self.assertGreaterEqual(sizes[(mode, "5:17")], sizes[(mode, "120:00")])
                # Stable font objects for changing glyphs; only a format/dimension
                # change selects a new size, in either countdown or count-up order.
                for values in [["5:17", "9:59", "0:00"], ["15:00", "59:59", "99:59"],
                               ["120:00", "999:59", "100:00"]]:
                    fonts = [renderer["fit_start_gate_timer_font"](
                        "".join("0" if ch.isdigit() else ch for ch in value), width, region_height)[0]
                             for value in values]
                    self.assertTrue(all(font is fonts[0] for font in fonts))


if __name__ == "__main__":
    unittest.main()
