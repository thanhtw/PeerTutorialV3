import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from learning.enhanced_tutorial import EnhancedTutorial

class TestEnhancedTutorialNavigation(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        # Mocking dependencies for EnhancedTutorial that are not relevant to _get_navigation_info
        self.mock_llm_manager = MagicMock()
        with patch('learning.enhanced_tutorial.MySQLConnection') as mock_db_connection, \
             patch('learning.enhanced_tutorial.SmartHintSystem') as mock_hint_system:
            self.tutorial = EnhancedTutorial(llm_manager=self.mock_llm_manager)
        
        # Mock progress, not directly used by _get_navigation_info but passed as an arg
        self.mock_progress = {}

    def test_navigation_first_step(self):
        """Test navigation info when on the first step of a multi-step tutorial."""
        self.tutorial.tutorial_structure = {
            "intro": {"step_id": 0, "title": "Introduction"},
            "middle": {"step_id": 1, "title": "Middle Part"},
            "final": {"step_id": 2, "title": "Final Step"}
        }
        nav_info = self.tutorial._get_navigation_info(step_id=0, progress=self.mock_progress)
        
        self.assertTrue(nav_info["is_first_step"])
        self.assertFalse(nav_info["is_last_step"])
        self.assertEqual(nav_info["next_step_id"], 1)
        self.assertIsNone(nav_info["previous_step_id"])
        self.assertEqual(nav_info["total_steps"], 3)

    def test_navigation_middle_step(self):
        """Test navigation info when on a middle step of a multi-step tutorial."""
        self.tutorial.tutorial_structure = {
            "intro": {"step_id": 0, "title": "Introduction"},
            "middle": {"step_id": 1, "title": "Middle Part"},
            "final": {"step_id": 2, "title": "Final Step"}
        }
        nav_info = self.tutorial._get_navigation_info(step_id=1, progress=self.mock_progress)
        
        self.assertFalse(nav_info["is_first_step"])
        self.assertFalse(nav_info["is_last_step"])
        self.assertEqual(nav_info["next_step_id"], 2)
        self.assertEqual(nav_info["previous_step_id"], 0)
        self.assertEqual(nav_info["total_steps"], 3)

    def test_navigation_last_step(self):
        """Test navigation info when on the last step of a multi-step tutorial."""
        self.tutorial.tutorial_structure = {
            "intro": {"step_id": 0, "title": "Introduction"},
            "middle": {"step_id": 1, "title": "Middle Part"},
            "final": {"step_id": 2, "title": "Final Step"}
        }
        nav_info = self.tutorial._get_navigation_info(step_id=2, progress=self.mock_progress)
        
        self.assertFalse(nav_info["is_first_step"])
        self.assertTrue(nav_info["is_last_step"])
        self.assertIsNone(nav_info["next_step_id"])
        self.assertEqual(nav_info["previous_step_id"], 1)
        self.assertEqual(nav_info["total_steps"], 3)

    def test_navigation_single_step_tutorial(self):
        """Test navigation info for a tutorial with only one step."""
        self.tutorial.tutorial_structure = {
            "only_step": {"step_id": 0, "title": "The Only Step"}
        }
        nav_info = self.tutorial._get_navigation_info(step_id=0, progress=self.mock_progress)
        
        self.assertTrue(nav_info["is_first_step"])
        self.assertTrue(nav_info["is_last_step"])
        self.assertIsNone(nav_info["next_step_id"])
        self.assertIsNone(nav_info["previous_step_id"])
        self.assertEqual(nav_info["total_steps"], 1)

if __name__ == '__main__':
    unittest.main()
