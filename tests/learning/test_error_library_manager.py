import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
# This is to ensure that the module 'learning.error_library_manager' can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from learning.error_library_manager import ErrorLibraryManager

class TestErrorLibraryManager(unittest.TestCase):

    @patch('learning.error_library_manager.MySQLConnection')
    def test_get_all_error_codes_and_titles_fetches_all(self, mock_mysql_connection_class):
        # Configure the mock for MySQLConnection().connection.is_connected()
        mock_db_instance = MagicMock()
        mock_db_instance.connection = MagicMock()
        mock_db_instance.connection.is_connected.return_value = True
        mock_mysql_connection_class.return_value = mock_db_instance

        # Sample data that db.execute_query will return
        raw_sample_data = [
            {"error_code": "ERR001", "title": "Null Pointer", "other_field": "some_value"},
            {"error_code": "ERR002", "title": "Array Index Out Of Bounds", "other_field": "another_value"}
        ]
        mock_db_instance.execute_query.return_value = raw_sample_data

        # Expected data after processing by get_all_error_codes_and_titles
        expected_processed_data = [
            {"error_code": "ERR001", "title": "Null Pointer"},
            {"error_code": "ERR002", "title": "Array Index Out Of Bounds"}
        ]

        # Instantiate the manager (MySQLConnection will be mocked)
        manager = ErrorLibraryManager()
        
        # Call the method under test
        result = manager.get_all_error_codes_and_titles()

        # Assertions
        expected_query = "SELECT error_code, title FROM error_details ORDER BY title ASC"
        
        # Check that execute_query was called
        mock_db_instance.execute_query.assert_called_once()
        
        # Retrieve the arguments with which execute_query was called
        call_args = mock_db_instance.execute_query.call_args
        
        # Ensure call_args is not None (it would be if not called)
        self.assertIsNotNone(call_args, "execute_query was not called")

        # Unpack arguments and keyword arguments
        args, kwargs = call_args
        
        # Check the query string (first positional argument)
        self.assertEqual(args[0], expected_query)
        
        # Check that 'fetch_one=True' was NOT passed.
        # If 'fetch_all' is the default for fetching all, then 'fetch_one' should not be present.
        # Or, if there's a 'fetch_all' param, it should be True (or absent if default is True)
        self.assertNotIn('fetch_one', kwargs, "fetch_one=True should not be passed for fetching all results.")
        
        # Depending on the implementation of execute_query, 
        # it might expect fetch_all=True explicitly or by default.
        # The prompt implies that default is fetch_all=True if fetch_one is not specified.
        # If there's an explicit fetch_all, assert it:
        # self.assertTrue(kwargs.get('fetch_all', False) or not kwargs , "fetch_all should be True or default")
        # For this specific task, we are ensuring 'fetch_one' is NOT used.
        # And we are assuming the default behavior of execute_query (when fetch_one=False) is to fetch all.

        # Check that the processed result is as expected
        self.assertEqual(result, expected_processed_data)

if __name__ == '__main__':
    unittest.main()
