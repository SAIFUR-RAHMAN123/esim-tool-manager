import unittest
from unittest.mock import patch, MagicMock

from tool_manager import installer


SAMPLE_TOOL_CONFIG = {
    "apt_package": "ngspice",
    "choco_package": "ngspice",
    "check_command": ["ngspice", "-v"],
    "version_regex": r"ngspice-(\d+)",
    "required_dependencies": [],
}


class TestInstaller(unittest.TestCase):
    @patch("tool_manager.version_utils.get_installed_version", return_value="42")
    @patch("tool_manager.version_utils.is_installed", return_value=True)
    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=True)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_already_installed_is_skipped(self, mock_pm, mock_avail, mock_installed, mock_version):
        result = installer.install_tool("ngspice", SAMPLE_TOOL_CONFIG)
        self.assertTrue(result.success)
        self.assertIn("already installed", result.message)
        self.assertEqual(result.version, "42")

    @patch("tool_manager.platform_utils.get_package_manager", return_value=None)
    def test_unsupported_os_fails(self, mock_pm):
        result = installer.install_tool("ngspice", SAMPLE_TOOL_CONFIG)
        self.assertFalse(result.success)
        self.assertIn("Unsupported OS", result.message)

    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=False)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_package_manager_unavailable_fails(self, mock_pm, mock_avail):
        result = installer.install_tool("ngspice", SAMPLE_TOOL_CONFIG)
        self.assertFalse(result.success)
        self.assertIn("not available", result.message)

    @patch("tool_manager.version_utils.get_installed_version", return_value="42")
    @patch("subprocess.run")
    @patch("tool_manager.version_utils.is_installed", return_value=False)
    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=True)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_successful_install(
        self, mock_pm, mock_avail, mock_installed, mock_run, mock_version
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = installer.install_tool("ngspice", SAMPLE_TOOL_CONFIG)
        self.assertTrue(result.success)
        self.assertEqual(result.version, "42")

    @patch("subprocess.run")
    @patch("tool_manager.version_utils.is_installed", return_value=False)
    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=True)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_failed_install_command(self, mock_pm, mock_avail, mock_installed, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="E: package not found")
        result = installer.install_tool("ngspice", SAMPLE_TOOL_CONFIG)
        self.assertFalse(result.success)
        self.assertIn("exited with code 1", result.message)


if __name__ == "__main__":
    unittest.main()
