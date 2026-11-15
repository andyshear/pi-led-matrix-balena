"""Focused startup checks with a simulated matrix; no GPIO, network, or Pillow.

Run: python3 scripts/test_startup_animation.py
"""
import ast
import contextlib
import io
from pathlib import Path
import queue
import threading
import time
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
RENDERERS = ("load_effect1.py", "load_effect2.py", "load_effect3.py")


class Matrix:
    def __init__(self):
        self.frames = []
        self.frame = {}
        self.shown = threading.Event()
        self.on_show = lambda: None

    def reset(self, color=(0, 0, 0)):
        self.frame = {}

    def pixel(self, position, color):
        self.frame[position] = color

    def show(self):
        self.frames.append(dict(self.frame))
        self.shown.set()
        self.on_show()


class FrameEvent:
    """Advance animation frames without sleeping or changing its drawing code."""
    def __init__(self, matrix, count):
        self.matrix, self.count = matrix, count

    def is_set(self):
        return len(self.matrix.frames) >= self.count

    def wait(self, timeout):
        return self.is_set()


class PendingWaitEvent(threading.Event):
    def __init__(self):
        super().__init__()
        self.waiting = threading.Event()

    def wait(self, timeout=None):
        self.waiting.set()
        return super().wait(1)


class InputPipe:
    def __init__(self):
        self.lines = queue.Queue()
        self.waiting = threading.Event()

    def readline(self):
        self.waiting.set()
        return self.lines.get(timeout=2)

    def input(self, prompt=""):
        line = self.readline()
        if not line:
            raise EOFError
        return line.rstrip("\n")


def load_renderer(filename, width=16, height=16):
    tree = ast.parse((ROOT / filename).read_text())
    # Keep the actual renderer and command/effect lifecycle. Only omit imports
    # that would acquire hardware or require native drawing dependencies.
    body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom)
        and node.module in ("src.led_matrix", "src.led_matrix1", "PIL")
        or isinstance(node, ast.Import)
        and any(alias.name == "numpy" for alias in node.names)
    )]
    instances = []

    def make_matrix():
        matrix = Matrix()
        instances.append(matrix)
        return matrix

    renderer = dict(__name__="startup_test", __file__=str(ROOT / filename),
                    Matrix=make_matrix, pixel_width=width, pixel_height=height)
    exec(compile(ast.Module(body=body, type_ignores=[]), filename, "exec"), renderer)
    assert len(instances) == 1
    main = next(node for node in tree.body if isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__")
    return renderer, compile(ast.Module(body=[main], type_ignores=[]), filename, "exec")


class StartupAnimation(unittest.TestCase):
    def setUp(self):
        self.thread_errors = []
        self.previous_hook = threading.excepthook
        threading.excepthook = self.thread_errors.append

    def tearDown(self):
        threading.excepthook = self.previous_hook
        self.assertFalse(self.thread_errors, self.thread_errors)

    def test_every_panel_border_and_configured_bounds(self):
        dimensions = ((16, 16), (32, 16), (16, 48), (48, 48), (64, 48),
                      (96, 48), (288, 16), (35, 19), (17, 17), (1, 16), (16, 1))
        for filename in RENDERERS:
            for width, height in dimensions:
                with self.subTest(renderer=filename, dimensions=(width, height)):
                    renderer, _ = load_renderer(filename, width, height)
                    matrix = renderer["matrix"]
                    renderer["stop_event"] = FrameEvent(matrix, 60)
                    renderer["set_current_effect"]("boot")
                    renderer["effect_boot"]()
                    expected = {(x, y) for y in range(height) for x in range(width)
                                if x % 16 == 0 or x % 16 == 15 or x == width - 1
                                or y % 16 == 0 or y % 16 == 15 or y == height - 1}
                    visited = set()
                    for frame in matrix.frames:
                        self.assertTrue(set(frame) <= expected)
                        visited.update(frame)
                        for y0 in range(0, height, 16):
                            for x0 in range(0, width, 16):
                                tile = [color for (x, y), color in frame.items()
                                        if x0 <= x < x0 + 16 and y0 <= y < y0 + 16]
                                self.assertTrue(tile)
                                if x0 + 16 <= width and y0 + 16 <= height:
                                    self.assertEqual(len(tile), 12)
                                    self.assertEqual(tile.count((195, 240, 255)), 1)
                        self.assertTrue(all(0 <= component <= 255
                                            for color in frame.values() for component in color))
                    self.assertEqual(visited, expected)
                    self.assertNotEqual(matrix.frames[0], matrix.frames[1])

    def test_operational_effects_join_boot_before_drawing(self):
        for filename in RENDERERS:
            renderer, _ = load_renderer(filename)
            for name in renderer["effects"].keys() - {"boot", "timer"}:
                with self.subTest(renderer=filename, effect=name):
                    renderer, _ = load_renderer(filename)
                    matrix = renderer["matrix"]
                    renderer["stop_event"] = PendingWaitEvent()
                    operational = threading.Event()
                    renderer["effects"][name] = lambda *args: operational.set()
                    renderer["apply_effect"]("boot")
                    self.assertTrue(matrix.shown.wait(1))
                    self.assertTrue(renderer["stop_event"].waiting.wait(1))
                    boot = renderer["current_effect_thread"]
                    # A long pending frame wait must be interrupted by the same
                    # stop_event, rather than delaying a safety command.
                    started = time.monotonic()
                    renderer["apply_effect"](name)
                    self.assertLess(time.monotonic() - started, 0.2)
                    self.assertFalse(boot.is_alive())
                    self.assertTrue(operational.wait(1))
                    frame_count = len(matrix.frames)
                    time.sleep(0.01)
                    self.assertEqual(len(matrix.frames), frame_count)
                    renderer["current_effect_thread"].join(timeout=1)

    def run_main(self, filename, lines, expected_effect, initial_effect=None):
        renderer, main = load_renderer(filename)
        pipe = InputPipe()
        renderer["sys"] = SimpleNamespace(stdin=pipe, argv=[filename] + (
            [initial_effect] if initial_effect else []))
        renderer["input"] = pipe.input
        renderer["__name__"] = "__main__"
        taken_over = threading.Event()
        received = []
        original_boot = renderer["effects"]["boot"]

        def operation(*args):
            received.append((renderer["get_current_effect"](), args))
            taken_over.set()

        for name in renderer["effects"].keys() - {"boot", "timer"}:
            renderer["effects"][name] = operation
        self.assertIs(renderer["effects"]["boot"], original_boot)
        errors = []

        def run():
            try:
                exec(main, renderer)
            except EOFError:
                pass
            except BaseException as error:
                errors.append(error)

        runner = threading.Thread(target=run, daemon=True)
        with contextlib.redirect_stdout(io.StringIO()):
            runner.start()
            try:
                self.assertTrue(pipe.waiting.wait(1))
                if initial_effect:
                    self.assertTrue(taken_over.wait(1))
                else:
                    self.assertTrue(renderer["matrix"].shown.wait(1))
                    first_count = len(renderer["matrix"].frames)
                    time.sleep(0.15)
                    self.assertGreater(len(renderer["matrix"].frames), first_count)
                    self.assertEqual(renderer["get_current_effect"](), "boot")
                for line in lines:
                    pipe.lines.put(line + "\n")
                if expected_effect != "boot":
                    self.assertTrue(taken_over.wait(1))
                    self.assertEqual(renderer["get_current_effect"](), expected_effect)
                else:
                    time.sleep(0.1)
                    self.assertEqual(renderer["get_current_effect"](), "boot")
            finally:
                pipe.lines.put("")
                runner.join(timeout=1)
                renderer["stop_event"].set()
                effect_thread = renderer["current_effect_thread"]
                if effect_thread:
                    effect_thread.join(timeout=1)
        self.assertFalse(runner.is_alive())
        self.assertFalse(renderer["current_effect_thread"].is_alive())
        self.assertFalse(errors)
        return renderer, received

    def test_plain_safety_and_local_offline_commands(self):
        for filename in RENDERERS:
            commands = ("caution", "medical", "clear", "off", "error")
            if filename == "load_effect1.py":
                commands += ("red", "startGateCountdown")
            for command in commands:
                with self.subTest(renderer=filename, command=command):
                    self.run_main(filename, [command], command)

    def test_json_operational_commands_and_payloads(self):
        cases = (
            ('{"effect":"times","riderData":"__CLEAR__"}', "times", "__CLEAR__"),
            ('{"effect":"times","riderData":{"riderId":"27","lapTime":"1:23"}}',
             "times", {"riderId": "27", "lapTime": "1:23"}),
            ('{"effect":"startGateDisplay","bigMode":"timerDown","timerEndMs":1234}',
             "startGateDisplay", {"effect": "startGateDisplay", "bigMode": "timerDown", "timerEndMs": 1234}),
            ('{"effect":"caution"}', "caution", None),
            ('{"effect":"timer","startMs":1234,"label":"Practice"}', "times", None),
        )
        for filename in RENDERERS[1:]:
            for command, effect, payload in cases:
                with self.subTest(renderer=filename, command=command):
                    renderer, received = self.run_main(filename, [command], effect)
                    self.assertEqual(received[0], (effect, (payload,)))
                    if effect == "times" and payload is not None:
                        if filename == "load_effect2.py" or isinstance(payload, str):
                            self.assertEqual(renderer["times_queue"].get_nowait(), payload)
                        else:
                            # Start-gate timing retains its existing legacy
                            # string queue; the initial payload is still passed.
                            self.assertTrue(renderer["times_queue"].empty())
                    if '"startMs"' in command:
                        self.assertEqual(renderer["race_timer_start_ms"], 1234)
                        self.assertEqual(renderer["race_timer_label"], "Practice")

    def test_metadata_and_unknown_commands_do_not_end_boot(self):
        for filename in RENDERERS:
            commands = ["", "unknown"]
            if filename != "load_effect1.py":
                commands += ['{"effect":"unknown"}', '{"effect":"timer","startMs":null}']
            with self.subTest(renderer=filename):
                self.run_main(filename, commands, "boot")

    def test_initial_safety_effect_takes_priority(self):
        self.run_main("load_effect1.py", [], "caution", initial_effect="caution")

    def test_idle_eof_stops_boot_thread(self):
        for filename in RENDERERS:
            with self.subTest(renderer=filename):
                self.run_main(filename, [], "boot")


if __name__ == "__main__":
    unittest.main()
