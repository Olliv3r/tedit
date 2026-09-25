import tempfile
import unittest
from pathlib import Path

from tedit.modern import create, load_state, set_feature, set_language, render_init


class ModernPresetTests(unittest.TestCase):
    def test_create_generates_isolated_config(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "tedit-nvim-tedit-modern"
            state = create(root)
            self.assertTrue((root / "init.lua").is_file())
            self.assertTrue((root / ".tedit-modern.json").is_file())
            self.assertIn("completion", state["features"])
            self.assertIn('require("lazy").setup', (root / "init.lua").read_text())

    def test_feature_and_language_toggle_regenerate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "modern"
            create(root)
            set_feature(root, "terminal", False)
            set_language(root, "rust", True)
            state = load_state(root)
            self.assertNotIn("terminal", state["features"])
            self.assertIn("rust", state["languages"])
            lua = (root / "init.lua").read_text()
            self.assertNotIn("toggleterm.nvim", lua)
            self.assertIn("rust_analyzer", lua)

    def test_render_uses_modern_lsp_api(self):
        lua = render_init({"features": [], "languages": ["python"], "theme": "tokyo-night"})
        self.assertIn("vim.lsp.enable", lua)
        self.assertNotIn("require('lspconfig')", lua)


if __name__ == "__main__":
    unittest.main()
