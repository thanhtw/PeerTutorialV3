import logging
from typing import Dict, List, Optional, Any
from db.mysql_connection import MySQLConnection # Assuming this is the correct path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ErrorLibraryManager:
    """
    Manages fetching detailed information about programming errors from the database.
    """

    def __init__(self):
        """
        Initializes the ErrorLibraryManager with a database connection.
        """
        try:
            self.db = MySQLConnection()
            if self.db.connection is None or not self.db.connection.is_connected():
                logger.error("Failed to establish database connection in ErrorLibraryManager.")
                # Potentially raise an exception or set a flag
                self.db = None # Ensure db is None if connection fails
            else:
                logger.info("ErrorLibraryManager initialized with database connection.")
        except Exception as e:
            logger.error(f"Error during ErrorLibraryManager initialization: {e}")
            self.db = None # Ensure db is None if connection fails

    def get_error_detail(self, error_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a specific error code.

        Args:
            error_code: The unique code for the error (e.g., "NULL_POINTER").

        Returns:
            A dictionary containing all fields for the error, or None if not found or DB error.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error("Cannot fetch error detail: Database connection is not active.")
            return None

        query = """
            SELECT id, error_code, language, title, detailed_description_md, 
                   example_good_code_md, example_bad_code_md, before_after_comparison_md, 
                   common_misconceptions_md, importance_explanation_md, 
                   created_at, updated_at 
            FROM error_details 
            WHERE error_code = %s
        """
        try:
            # Assuming execute_query with fetch_one=True returns a dict-like object or None
            result = self.db.execute_query(query, (error_code,), fetch_one=True)
            if result:
                logger.info(f"Successfully fetched details for error_code: {error_code}")
                return result 
            else:
                logger.info(f"No details found for error_code: {error_code}")
                return None
        except Exception as e:
            logger.error(f"Database error while fetching details for error_code {error_code}: {e}")
            return None

    def get_all_error_codes_and_titles(self) -> List[Dict[str, str]]:
        """
        Retrieves a list of all error codes and their titles.

        Returns:
            A list of dictionaries, each with "error_code" and "title", 
            or an empty list if no errors are found or DB error.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error("Cannot fetch error codes and titles: Database connection is not active.")
            return []

        query = "SELECT error_code, title FROM error_details ORDER BY title ASC"
        try:
            results = self.db.execute_query(query)
            if results:
                # Assuming results is a list of dict-like objects (e.g., from a DictCursor)
                # This comprehension ensures we only process dicts and they have the required keys.
                processed_results = [
                    {"error_code": row["error_code"], "title": row["title"]} 
                    for row in results 
                    if isinstance(row, dict) and "error_code" in row and "title" in row
                ]
                if not processed_results and results: # If results were not empty, but processing yielded empty
                    logger.warning("Fetched data for error codes/titles was not in the expected format (list of dicts).")
                    return []
                logger.info(f"Successfully fetched {len(processed_results)} error codes and titles.")
                return processed_results
            else:
                logger.info("No error codes and titles found in the database.")
                return []
        except Exception as e:
            logger.error(f"Database error while fetching all error codes and titles: {e}")
            return []

if __name__ == '__main__':
    # Basic test (optional, for development)
    # This part will be expanded later or removed if not needed for automated tests
    logger.info("Attempting to instantiate ErrorLibraryManager for basic test...")
    manager = ErrorLibraryManager()
    if manager.db and manager.db.connection and manager.db.connection.is_connected():
        logger.info("ErrorLibraryManager instantiated and connected for basic test.")
    else:
        logger.error("ErrorLibraryManager failed to instantiate or connect for basic test.")
