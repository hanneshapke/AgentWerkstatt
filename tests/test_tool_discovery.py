import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from agentwerkstatt.tools.discovery import ToolRegistry
from agentwerkstatt.tools.base import BaseTool


class MockTool(BaseTool):
    def get_name(self) -> str:
        return "mock_tool"

    def get_description(self) -> str:
        return "A mock tool."

    def get_schema(self) -> dict:
        return {}

    def execute(self, **kwargs):
        pass


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tools_dir = Path(self.temp_dir.name)
        self.registry = ToolRegistry(str(self.tools_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("agentwerkstatt.tools.discovery.importlib.import_module")
    def test_discover_tools(self, mock_import):
        # Create a dummy tool file
        tool_file = self.tools_dir / "my_tool.py"
        tool_file.write_text(
            "from agentwerkstatt.tools.base import BaseTool\n"
            "class MyTool(BaseTool):\n"
            "    def get_name(self):\n"
            "        return 'my_tool'\n"
            "    def get_description(self):\n"
            "        return 'My tool.'\n"
            "    def get_schema(self):\n"
            "        return {}\n"
            "    def execute(self, **kwargs):\n"
            "        pass"
        )

        # Mock the module to return our MockTool
        mock_module = MagicMock()
        mock_module.MyTool = MockTool
        mock_import.return_value = mock_module

        # Create a new registry that will use the mocked import
        new_registry = ToolRegistry(str(self.tools_dir))
        self.assertEqual(len(new_registry.get_tools()), 1)
        self.assertIsNotNone(new_registry.get_tool_by_name("mock_tool"))

    def test_get_tool_by_name_not_found(self):
        self.assertIsNone(self.registry.get_tool_by_name("non_existent_tool"))


if __name__ == "__main__":
    unittest.main()
