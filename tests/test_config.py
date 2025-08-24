import unittest
import tempfile
import yaml
from pathlib import Path

from pydantic import ValidationError

from agentwerkstatt.config import AgentConfig


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "test_config.yaml"
        self.tools_dir = Path(self.temp_dir.name) / "tools"
        self.tools_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_from_yaml_success(self):
        config_data = {
            "llm": {"provider": "claude", "model": "test-model"},
            "tools_dir": str(self.tools_dir),
            "task_objective": "Test task objective",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)

        config = AgentConfig.from_yaml(str(self.config_file))
        self.assertEqual(config.task_objective, "Test task objective")
        self.assertEqual(config.llm.model, "test-model")
        self.assertEqual(config.llm.provider, "claude")
        self.assertEqual(str(config.tools_dir), str(self.tools_dir))

    def test_from_yaml_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            AgentConfig.from_yaml("non_existent_file.yaml")

    def test_from_yaml_invalid_yaml(self):
        with open(self.config_file, "w") as f:
            f.write("invalid yaml")
        with self.assertRaises(ValueError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_missing_llm_config(self):
        config_data = {
            "tools_dir": str(self.tools_dir),
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_missing_tools_dir(self):
        config_data = {
            "llm": {"provider": "claude", "model": "test-model"},
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_nonexistent_tools_dir(self):
        config_data = {
            "llm": {"provider": "claude", "model": "test-model"},
            "tools_dir": "/nonexistent/path",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    # @patch.dict(os.environ, {}, clear=True)
    # def test_langfuse_enabled_missing_env_vars(self):
    #     config_data = {
    #         "llm": {"provider": "claude", "model": "test-model"},
    #         "tools_dir": str(self.tools_dir),
    #         "langfuse": {"enabled": True},
    #         "task_objective": "Test task objective",
    #     }
    #     with open(self.config_file, "w") as f:
    #         yaml.dump(config_data, f)
    #     with self.assertRaises(ValueError) as cm:
    #         AgentConfig.from_yaml(str(self.config_file))
    #     self.assertIn("LANGFUSE_PUBLIC_KEY environment variable is required", str(cm.exception))

    # @patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test", "LANGFUSE_SECRET_KEY": "test"})
    # def test_langfuse_enabled_with_env_vars(self):
    #     config_data = {
    #         "llm": {"provider": "claude", "model": "test-model"},
    #         "tools_dir": str(self.tools_dir),
    #         "langfuse": {"enabled": True},
    #         "task_objective": "Test task objective",
    #     }
    #     with open(self.config_file, "w") as f:
    #         yaml.dump(config_data, f)

    #     # Should not raise
    #     AgentConfig.from_yaml(str(self.config_file))


if __name__ == "__main__":
    unittest.main()
