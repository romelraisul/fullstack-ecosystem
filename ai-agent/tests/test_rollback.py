import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))
from robust_rollback import RollbackEngine

class TestRollbackOrchestrator(unittest.TestCase):
    def setUp(self):
        self.engine = RollbackEngine()
        # Mock the state for testing
        self.engine.state = {
            "active_env": "blue",
            "environments": {
                "blue": {"port": 3001, "version": "1.0.0", "path": "/tmp/blue"},
                "green": {"port": 3002, "version": "1.1.0", "path": "/tmp/green"}
            },
            "history": []
        }

    @patch('subprocess.run')
    @patch('requests.get')
    def test_successful_rollback(self, mock_get, mock_run):
        """Scenario: Blue is active, Green is healthy. Rollback to Green."""
        # Setup mocks
        mock_run.return_value = MagicMock(stdout=json.dumps([
            {"name": "hostamar-green", "pm2_env": {"status": "online"}}
        ]), returncode=0)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        # Execute
        result = self.engine.rollback_to_previous()
        
        # Verify
        self.assertTrue(result)
        self.assertEqual(self.engine.state["active_env"], "green")
        mock_get.assert_called()

    @patch('subprocess.run')
    def test_partial_rollback_failure(self, mock_run):
        """Scenario: Target PM2 process is missing and fails to start."""
        mock_run.side_effect = Exception("PM2 Error")
        
        result = self.engine.rollback_to_previous()
        
        self.assertFalse(result)
        self.assertEqual(self.engine.state["active_env"], "blue") # Should not change

    @patch('subprocess.run')
    @patch('requests.get')
    def test_health_check_failure(self, mock_get, mock_run):
        """Scenario: Traffic switched but health check fails."""
        mock_run.return_value = MagicMock(stdout=json.dumps([
            {"name": "hostamar-green", "pm2_env": {"status": "online"}}
        ]), returncode=0)
        
        mock_get.side_effect = Exception("Connection Timeout")
        
        result = self.engine.rollback_to_previous()
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
