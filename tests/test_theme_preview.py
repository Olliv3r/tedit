import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tedit.theme import list_themes
from tedit.theme_preview import render_terminal_preview, _write_nvim_preview


class ThemePreviewTests(unittest.TestCase):
    def test_every_theme_renders_without_changing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_app = Path(tmp) / "tedit"
            fake_app.mkdir()
            state = fake_app / "state.json"
            state.write_text(json.dumps({"theme": "keep-me"}), encoding="utf-8")
            before = state.read_bytes()
            for name in list_themes():
                output = render_terminal_preview(name)
                self.assertIn(name, output)
                self.assertIn("ThemePreview", output)
            self.assertEqual(before, state.read_bytes())

    def test_nvim_preview_files_stay_inside_temp_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config, demo = _write_nvim_preview(root, "tokyo-night")
            self.assertTrue(config.is_relative_to(root))
            self.assertTrue(demo.is_relative_to(root))
            self.assertTrue((config / "init.lua").is_file())
            self.assertTrue(demo.is_file())
            init = (config / "init.lua").read_text(encoding="utf-8")
            self.assertIn("tedit-preview-tokyo-night", init)
            self.assertIn("nvim_set_hl", init)


if __name__ == "__main__":
    unittest.main()
