import unittest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from agentwerkstatt.config import AgentConfig


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "test_config.yaml"
        self.persona_file = Path(self.temp_dir.name) / "test.md"
        self.persona_file.write_text("persona content")
        self.tools_dir = Path(self.temp_dir.name) / "tools"
        self.tools_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_from_yaml_success(self):
        config_data = {
            "model": "test-model",
            "tools_dir": str(self.tools_dir),
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)

        config = AgentConfig.from_yaml(str(self.config_file))
        self.assertEqual(config.model, "test-model")
        self.assertEqual(len(config.personas), 1)
        self.assertEqual(config.personas[0].file, "persona content")

    def test_from_yaml_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            AgentConfig.from_yaml("non_existent_file.yaml")

    def test_from_yaml_invalid_yaml(self):
        with open(self.config_file, "w") as f:
            f.write("invalid yaml")
        with self.assertRaises(ValueError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_missing_model(self):
        config_data = {
            "tools_dir": str(self.tools_dir),
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_missing_tools_dir(self):
        config_data = {
            "model": "test-model",
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_nonexistent_tools_dir(self):
        config_data = {
            "model": "test-model",
            "tools_dir": "/nonexistent/path",
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValidationError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_from_yaml_invalid_default_persona(self):
        config_data = {
            "model": "test-model",
            "tools_dir": str(self.tools_dir),
            "personas": [
                {
                    "id": "other",
                    "name": "Other",
                    "description": "Other persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "nonexistent",
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValueError) as cm:
            AgentConfig.from_yaml(str(self.config_file))
        self.assertIn("Default persona 'nonexistent' not found", str(cm.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_langfuse_enabled_missing_env_vars(self):
        config_data = {
            "model": "test-model",
            "tools_dir": str(self.tools_dir),
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
            "langfuse": {"enabled": True},
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
        with self.assertRaises(ValueError) as cm:
            AgentConfig.from_yaml(str(self.config_file))
        self.assertIn("LANGFUSE_PUBLIC_KEY environment variable is required", str(cm.exception))

    @patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test", "LANGFUSE_SECRET_KEY": "test"})
    def test_langfuse_enabled_with_env_vars(self):
        config_data = {
            "model": "test-model",
            "tools_dir": str(self.tools_dir),
            "personas": [
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Test persona",
                    "file": str(self.persona_file),
                }
            ],
            "default_persona": "test",
            "langfuse": {"enabled": True},
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)

        # Should not raise
        AgentConfig.from_yaml(str(self.config_file))


if __name__ == "__main__":
    unittest.main()
