import unittest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from agentwerkstatt.config import AgentConfig, PersonaConfig, ConfigValidator


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = Path(self.temp_dir.name) / "test_config.yaml"
        self.persona_file = Path(self.temp_dir.name) / "test.md"
        self.persona_file.write_text("persona content")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_from_yaml_success(self):
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

        config = AgentConfig.from_yaml(str(self.config_file))
        self.assertEqual(config.model, "test-model")
        self.assertEqual(len(config.personas), 1)

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
        with self.assertRaises(ValueError):
            AgentConfig.from_yaml(str(self.config_file))

    def test_persona_config_post_init(self):
        with patch("pathlib.Path.read_text", return_value="persona content"):
            persona = PersonaConfig(
                id="test", name="Test", description="Test persona", file="test.md"
            )
            self.assertEqual(persona.file, "test.md")


class TestConfigValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tools_dir = Path(self.temp_dir.name) / "tools"
        self.tools_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_valid_config(self):
        """Test validation passes for a valid config"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model",
            tools_dir=str(self.tools_dir),
            personas=[persona],
            default_persona="test",
        )
        errors = self.validator.validate(config)
        self.assertEqual(errors, [])

    def test_validate_missing_model(self):
        """Test validation fails for missing model"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="", tools_dir=str(self.tools_dir), personas=[persona], default_persona="test"
        )
        errors = self.validator.validate(config)
        self.assertIn("Model name is required", errors)

    def test_validate_missing_tools_dir(self):
        """Test validation fails for missing tools directory"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model", tools_dir="", personas=[persona], default_persona="test"
        )
        errors = self.validator.validate(config)
        self.assertIn("Tools directory is required", errors)

    def test_validate_nonexistent_tools_dir(self):
        """Test validation fails for non-existent tools directory"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model",
            tools_dir="/nonexistent/path",
            personas=[persona],
            default_persona="test",
        )
        errors = self.validator.validate(config)
        self.assertTrue(any("Tools directory does not exist" in error for error in errors))

    def test_validate_missing_personas(self):
        """Test validation fails for missing personas"""
        config = AgentConfig(
            model="test-model", tools_dir=str(self.tools_dir), personas=[], default_persona="test"
        )
        errors = self.validator.validate(config)
        self.assertIn("Agent personas are required but none are defined.", errors)

    def test_validate_invalid_default_persona(self):
        """Test validation fails for invalid default persona"""
        persona = PersonaConfig(
            id="other", name="Other", description="Other persona", file="content"
        )
        config = AgentConfig(
            model="test-model",
            tools_dir=str(self.tools_dir),
            personas=[persona],
            default_persona="nonexistent",
        )
        errors = self.validator.validate(config)
        self.assertTrue(any("Default persona 'nonexistent' not found" in error for error in errors))

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_langfuse_missing_env_vars(self):
        """Test validation fails for Langfuse with missing env vars"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model",
            tools_dir=str(self.tools_dir),
            personas=[persona],
            default_persona="test",
            langfuse_enabled=True,
        )
        errors = self.validator.validate(config)
        self.assertTrue(any("LANGFUSE_PUBLIC_KEY" in error for error in errors))
        self.assertTrue(any("LANGFUSE_SECRET_KEY" in error for error in errors))

    @patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "test", "LANGFUSE_SECRET_KEY": "test"})
    def test_validate_langfuse_with_env_vars(self):
        """Test validation passes for Langfuse with env vars"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model",
            tools_dir=str(self.tools_dir),
            personas=[persona],
            default_persona="test",
            langfuse_enabled=True,
        )
        errors = self.validator.validate(config)
        langfuse_errors = [e for e in errors if "LANGFUSE" in e]
        self.assertEqual(langfuse_errors, [])

    def test_validate_memory_config(self):
        """Test memory validation"""
        persona = PersonaConfig(id="test", name="Test", description="Test persona", file="content")
        config = AgentConfig(
            model="test-model",
            tools_dir=str(self.tools_dir),
            personas=[persona],
            default_persona="test",
            memory_enabled=True,
            memory_server_url="invalid-url",
        )
        errors = self.validator.validate(config)
        # Should validate memory config (specific validation depends on implementation)
        # For now just ensure it doesn't crash
        self.assertIsInstance(errors, list)


if __name__ == "__main__":
    unittest.main()
