import subprocess
import unittest
from unittest.mock import patch, MagicMock

from tool_manager import version_utils


SAMPLE_TOOL_CONFIG = {
    "check_command": ["ngspice", "-v"],
    "version_regex": r"ngspice-(\d+(?:\.\d+)?)",
}


class TestVersionUtils(unittest.TestCase):
    @patch("shutil.which", return_value=None)
    def test_not_installed_returns_none(self, mock_which):
        version = version_utils.get_installed_version(SAMPLE_TOOL_CONFIG)
        self.assertIsNone(version)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/ngspice")
    def test_version_parsed_from_stderr(self, mock_which, mock_run):
        # Real ngspice prints its banner (including version) to stderr.
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="******\n** ngspice-42 : Circuit level simulation\n",
            returncode=0,
        )
        version = version_utils.get_installed_version(SAMPLE_TOOL_CONFIG)
        self.assertEqual(version, "42")

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/ngspice")
    def test_unparseable_output_returns_none(self, mock_which, mock_run):
        mock_run.return_value = MagicMock(stdout="garbage", stderr="", returncode=0)
        version = version_utils.get_installed_version(SAMPLE_TOOL_CONFIG)
        self.assertIsNone(version)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ngspice", timeout=10))
    @patch("shutil.which", return_value="/usr/bin/ngspice")
    def test_timeout_raises(self, mock_which, mock_run):
        with self.assertRaises(version_utils.VersionCheckError):
            version_utils.get_installed_version(SAMPLE_TOOL_CONFIG)


if __name__ == "__main__":
    unittest.main()
