"""
Repository Factory module for managing error repository instances.
"""

import logging
from typing import Union
from data.json_error_repository import JsonErrorRepository
from data.database_error_repository import DatabaseErrorRepository

logger = logging.getLogger(__name__)

class RepositoryFactory:
    """Factory class for creating appropriate repository instances."""
    
    _instance = None
    _repository = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_repository(self, force_database: bool = True) -> Union[JsonErrorRepository, DatabaseErrorRepository]:
        """
        Get an appropriate repository instance.
        
        Args:
            force_database: If True, prefer database repository
            
        Returns:
            Repository instance
        """
        if self._repository is None:
            if force_database:
                try:
                    # Try database repository first
                    self._repository = DatabaseErrorRepository()
                    logger.debug("Using DatabaseErrorRepository")
                except Exception as e:
                    logger.warning(f"Database repository failed, falling back to JSON: {str(e)}")
                    self._repository = JsonErrorRepository()
            else:
                # Use JSON repository (now database-backed)
                self._repository = JsonErrorRepository()
                logger.debug("Using JsonErrorRepository (database-backed)")
        
        return self._repository
    
    def reset_repository(self):
        """Reset the repository instance."""
        self._repository = None

# Global factory instance
repository_factory = RepositoryFactory()

def get_error_repository() -> Union[JsonErrorRepository, DatabaseErrorRepository]:
    """
    Get the error repository instance.
    
    Returns:
        Error repository instance
    """
    return repository_factory.get_repository()
