import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tedit.nvim_manager as nm


class NvimSafetyTests(unittest.TestCase):
    def test_generated_preset_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(nm, "_xdg_config_home", return_value=Path(td)):
                result = nm.install("tedit-modern", dry_run=True)
                self.assertFalse(Path(result["target"]).exists())

    def test_remove_namespace_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "tedit-nvim-tedit-modern"
            target.mkdir()
            (target / "init.lua").write_text("-- test")
            with patch.object(nm, "_xdg_config_home", return_value=root), patch.object(nm, "_write_state"):
                removed = nm.remove("tedit-modern")
                self.assertEqual(removed, target)
                self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
