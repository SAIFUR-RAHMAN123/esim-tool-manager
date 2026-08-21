import unittest
from unittest.mock import patch

from tool_manager import dependency_checker


SAMPLE_TOOL_CONFIG = {
    "description": "test tool",
    "apt_package": "sometool",
    "choco_package": "sometool",
    "check_command": ["sometool", "--version"],
    "version_regex": r"(\d+\.\d+)",
    "required_dependencies": ["gcc", "make"],
}


class TestDependencyChecker(unittest.TestCase):
    @patch("tool_manager.dependency_checker.check_binary")
    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=True)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_all_dependencies_satisfied(self, mock_pm, mock_pm_avail, mock_check_binary):
        mock_check_binary.return_value = True

        report = dependency_checker.check_dependencies("sometool", SAMPLE_TOOL_CONFIG)

        self.assertTrue(report.all_satisfied)
        self.assertEqual(report.missing, [])

    @patch("tool_manager.dependency_checker.check_binary")
    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=True)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_missing_dependency_detected(self, mock_pm, mock_pm_avail, mock_check_binary):
        # gcc present, make missing
        mock_check_binary.side_effect = lambda name: name != "make"

        report = dependency_checker.check_dependencies("sometool", SAMPLE_TOOL_CONFIG)

        self.assertFalse(report.all_satisfied)
        self.assertEqual(report.missing, ["make"])

    @patch("tool_manager.platform_utils.is_package_manager_available", return_value=False)
    @patch("tool_manager.platform_utils.get_package_manager", return_value="apt")
    def test_package_manager_missing_fails_overall(self, mock_pm, mock_pm_avail):
        report = dependency_checker.check_dependencies(
            "sometool", {**SAMPLE_TOOL_CONFIG, "required_dependencies": []}
        )
        self.assertFalse(report.all_satisfied)


if __name__ == "__main__":
    unittest.main()
