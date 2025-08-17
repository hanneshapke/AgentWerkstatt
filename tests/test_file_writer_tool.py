import unittest
import os
from agentwerkstatt.tools.file_writer import FileWriterTool


class TestFileWriterTool(unittest.TestCase):
    def setUp(self):
        self.tool = FileWriterTool()
        self.test_filename = "test_file.md"

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_execute_success(self):
        content = "This is a test."
        result = self.tool.execute(self.test_filename, content)
        self.assertEqual(result, {"success": f"Successfully wrote to {self.test_filename}"})
        with open(self.test_filename) as f:
            self.assertEqual(f.read(), content)

    def test_execute_invalid_filename(self):
        result = self.tool.execute("test_file.txt", "content")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Filename must end with .md")

    def test_get_name(self):
        self.assertEqual(self.tool.get_name(), "file_writer")

    def test_get_description(self):
        self.assertIn("Writes content to a markdown file", self.tool.get_description())

    def test_get_schema(self):
        schema = self.tool.get_schema()
        self.assertEqual(schema["name"], "file_writer")
        self.assertIn("input_schema", schema)
        self.assertIn("filename", schema["input_schema"]["properties"])
        self.assertIn("content", schema["input_schema"]["properties"])

    def test_execute_overwrite(self):
        initial_content = "Initial content."
        with open(self.test_filename, "w") as f:
            f.write(initial_content)

        new_content = "New content."
        self.tool.execute(self.test_filename, new_content)
        with open(self.test_filename) as f:
            self.assertEqual(f.read(), new_content)

    def test_execute_error(self):
        with unittest.mock.patch("builtins.open", side_effect=OSError("Test error")):
            result = self.tool.execute(self.test_filename, "content")
            self.assertIn("error", result)
            self.assertIn("An unexpected error occurred", result["error"])


if __name__ == "__main__":
    unittest.main()
