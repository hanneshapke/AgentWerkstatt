import unittest

from agentwerkstatt import llms


class TestLLMsIntegration(unittest.TestCase):
    def test_llms_modules_can_be_imported(self):
        """Test that all LLM modules can be imported without error."""
        self.assertTrue(hasattr(llms, "create_claude_llm"))
        self.assertTrue(hasattr(llms, "create_ollama_llm"))
        self.assertTrue(hasattr(llms, "create_lmstudio_llm"))
        self.assertTrue(hasattr(llms, "MockLLM"))
