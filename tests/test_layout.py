import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tedit.nvim_manager as nm
from tedit.layout import render_runtime_lua
from tedit.modern import render_init


class LayoutTests(unittest.TestCase):
    def test_runtime_shim_targets_known_sidebars(self):
        lua = render_runtime_lua()
        self.assertIn('["neo-tree"] = true', lua)
        self.assertIn('["NvimTree"] = true', lua)
        self.assertIn('vim.o.columns < 100', lua)
        self.assertIn('vim.api.nvim_win_set_width', lua)
        self.assertIn('signcolumn = "number"', lua)
        self.assertIn('numberwidth = 2', lua)
        self.assertIn('foldcolumn = "0"', lua)

    def test_modern_config_is_responsive(self):
        lua = render_init({"features": ["explorer", "telescope"], "languages": [], "theme": "tokyo-night", "layout": "auto"})
        self.assertIn('tedit_layout_mode', lua)
        self.assertIn('math.floor(vim.o.columns * 0.30)', lua)
        self.assertIn('layout_strategy = compact and "vertical" or "flex"', lua)
        self.assertIn('vim.opt.signcolumn = "number"', lua)
        self.assertIn('vim.opt.numberwidth = 2', lua)
        self.assertIn('vim.opt.statuscolumn = ""', lua)

    def test_layout_state_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            state_file = Path(td) / "nvim.json"
            with patch.object(nm, "STATE_FILE", state_file), patch.object(nm, "ensure_dirs"):
                self.assertEqual(nm.set_layout("compact"), "compact")
                self.assertEqual(nm.current_layout(), "compact")

    def test_run_injects_layout_without_editing_preset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            preset = root / "tedit-nvim-astronvim"
            preset.mkdir()
            init = preset / "init.lua"
            init.write_text('-- external preset\n')
            script = root / "layout.lua"
            script.write_text('-- shim\n')
            with patch.object(nm, "_xdg_config_home", return_value=root), \
                 patch.object(nm, "runtime_script_path", return_value=script), \
                 patch.object(nm.shutil, "which", return_value="/usr/bin/nvim"), \
                 patch.object(nm.subprocess, "call", return_value=0) as call:
                rc = nm.run("astronvim", [], "compact")
                self.assertEqual(rc, 0)
                args, kwargs = call.call_args
                self.assertIn("--cmd", args[0])
                self.assertEqual(kwargs["env"]["TEDIT_NVIM_LAYOUT"], "compact")
                self.assertEqual(init.read_text(), '-- external preset\n')


if __name__ == "__main__":
    unittest.main()
