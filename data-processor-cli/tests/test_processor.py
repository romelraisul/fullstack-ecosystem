import unittest
import os
import sys
import tempfile
import csv

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from processor import DataProcessor
from validator import ValidationError

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory and processor instance before each test."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.processor = DataProcessor(output_dir=self.test_dir.name)
        
    def tearDown(self):
        """Clean up temporary directory."""
        self.test_dir.cleanup()

    def create_dummy_csv(self, filename, content):
        """Helper to create a CSV file in the temp directory."""
        path = os.path.join(self.test_dir.name, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(content)
        return path

    def test_process_valid_csv(self):
        """Test processing a valid CSV file."""
        data = [['id', 'name'], ['1', 'Item A'], ['2', 'Item B']]
        path = self.create_dummy_csv('valid.csv', data)
        
        result = self.processor.process_file(path)
        self.assertTrue(result, "Processor should return True for valid CSV")

    def test_process_missing_columns(self):
        """Test processing a CSV missing required columns."""
        data = [['id', 'value'], ['1', '100']] # Missing 'name'
        path = self.create_dummy_csv('invalid.csv', data)
        
        # We expect process_file to catch the error and return False (Graceful Failure)
        result = self.processor.process_file(path)
        self.assertFalse(result, "Processor should return False for schema violation")

    def test_process_nonexistent_file(self):
        """Test processing a file that doesn't exist."""
        path = os.path.join(self.test_dir.name, "ghost.csv")
        result = self.processor.process_file(path)
        self.assertFalse(result, "Processor should return False for missing file")

    def test_batch_processing(self):
        """Test processing a batch of mixed files."""
        good_path = self.create_dummy_csv('good.csv', [['id', 'name'], ['1', 'A']])
        bad_path = self.create_dummy_csv('bad.csv', [['wrong', 'header']])
        
        # Capture stdout to avoid cluttering test output
        from io import StringIO
        from contextlib import redirect_stdout
        
        with redirect_stdout(StringIO()):
            self.processor.process_batch([good_path, bad_path])
        
        # Logs are handled by the logger module, verification would check logs ideally
        # Here we just ensure it ran without crashing

if __name__ == '__main__':
    unittest.main()
