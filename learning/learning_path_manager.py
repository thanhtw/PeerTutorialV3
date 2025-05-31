import logging
from typing import Dict, List, Optional, Any
from db.mysql_connection import MySQLConnection # Assuming this is the correct path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class LearningPathManager:
    """
    Manages learning paths, user enrollment, and progress tracking.
    """

    def __init__(self):
        """
        Initializes the LearningPathManager with a database connection.
        """
        try:
            self.db = MySQLConnection()
            if self.db.connection is None or not self.db.connection.is_connected():
                logger.error("Failed to establish database connection in LearningPathManager.")
                self.db = None # Ensure db is None if connection fails
            else:
                logger.debug("LearningPathManager initialized with database connection.")
        except Exception as e:
            logger.error(f"Error during LearningPathManager initialization: {e}")
            self.db = None

    def get_all_paths(self) -> List[Dict[str, Any]]:
        """
        Retrieves all active learning paths, ordered by path_order.

        Returns:
            A list of dictionaries, each representing an active learning path, 
            or an empty list if no paths are found or a DB error occurs.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error("Cannot fetch learning paths: Database connection is not active.")
            return []

        query = """
            SELECT id, path_name, description_en, description_zh, difficulty_level, 
                   estimated_hours, prerequisites, skills_learned, path_order, is_active, created_at
            FROM learning_paths 
            WHERE is_active = TRUE 
            ORDER BY path_order ASC
        """
        try:
            results = self.db.execute_query(query)
            if results:
                # Assuming results from db.execute_query is already List[Dict[str, Any]]
                # If not, conversion will be needed.
                logger.debug(f"Successfully fetched {len(results)} active learning paths.")
                return results
            else:
                logger.debug("No active learning paths found.")
                return []
        except Exception as e:
            logger.error(f"Database error while fetching all learning paths: {e}")
            return []
    
    
    def get_path_steps(self, path_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves all steps for a specific learning path, ordered by step_order.

        Args:
            path_id: The ID of the learning path.

        Returns:
            A list of dictionaries, each representing a step in the path,
            or an empty list if no steps are found or a DB error occurs.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error(f"Cannot fetch steps for path_id {path_id}: Database connection is not active.")
            return []

        query = """
            SELECT id, path_id, step_order, title, description_md, 
                   step_type, content_reference, estimated_time_minutes, created_at
            FROM learning_path_steps
            WHERE path_id = %s
            ORDER BY step_order ASC
        """
        try:
            results = self.db.execute_query(query, (path_id,))
            if results:
                # Assuming results from db.execute_query is already List[Dict[str, Any]]
                logger.debug(f"Successfully fetched {len(results)} steps for path_id {path_id}.")
                return results
            else:
                logger.debug(f"No steps found for path_id {path_id}.")
                return []
        except Exception as e:
            logger.error(f"Database error while fetching steps for path_id {path_id}: {e}")
            return []
    
    
    def get_user_enrollment(self, user_id: str, path_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the enrollment status for a specific user and learning path.

        Args:
            user_id: The ID of the user.
            path_id: The ID of the learning path.

        Returns:
            A dictionary containing the enrollment details, or None if not enrolled or DB error.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error(f"Cannot fetch enrollment for user_id {user_id}, path_id {path_id}: DB not active.")
            return None

        query = """
            SELECT id, user_id, path_id, status, current_step_id, total_steps, 
                   progress_percentage, started_at, completed_at, updated_at
            FROM user_learning_paths
            WHERE user_id = %s AND path_id = %s
        """
        try:
            result = self.db.execute_query(query, (user_id, path_id), fetch_one=True)
            if result:
                # Assuming result from db.execute_query is already Dict[str, Any] or None
                logger.debug(f"Enrollment details found for user_id {user_id}, path_id {path_id}.")
                return result
            else:
                logger.debug(f"No enrollment found for user_id {user_id}, path_id {path_id}.")
                return None
        except Exception as e:
            logger.error(f"DB error fetching enrollment for user_id {user_id}, path_id {path_id}: {e}")
            return None
    
    
    def enroll_user(self, user_id: str, path_id: int) -> bool:
        """
        Enrolls a user in a learning path.

        Args:
            user_id: The ID of the user.
            path_id: The ID of the learning path.

        Returns:
            True if enrollment was successful or user already enrolled, False otherwise.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error(f"Cannot enroll user_id {user_id} in path_id {path_id}: DB not active.")
            return False

        # Check if already enrolled
        existing_enrollment = self.get_user_enrollment(user_id, path_id)
        if existing_enrollment:
            logger.debug(f"User_id {user_id} is already enrolled in path_id {path_id}.")
            # Consider what status means 'already successfully enrolled' vs 're-enrollable'
            # For now, if enrollment exists, assume it's fine.
            return True

        # Get path steps to calculate total_steps and find first_step_id
        path_steps = self.get_path_steps(path_id)
        total_steps = len(path_steps)
        first_step_id: Optional[int] = None
        initial_status = 'in_progress' # Default status

        if total_steps > 0:
            # Ensure path_steps[0] is a dictionary and has 'id'
            if isinstance(path_steps[0], dict) and 'id' in path_steps[0]:
                first_step_id = path_steps[0]['id']
            else:
                logger.error(f"First step of path_id {path_id} is not a dict or has no 'id'. Cannot enroll.")
                return False # Critical error in path data
        else:
            logger.warning(f"Path_id {path_id} has no steps. Enrolling user {user_id} and marking as completed.")
            initial_status = 'completed' # Path with no steps is considered completed upon enrollment
            # For 'completed' status, progress_percentage should be 100
            # current_step_id remains None as there are no steps

        insert_query = """
            INSERT INTO user_learning_paths 
            (user_id, path_id, status, current_step_id, total_steps, progress_percentage, started_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        try:
            progress_percentage = 100.0 if initial_status == 'completed' else 0.0
            self.db.execute_query(insert_query, (user_id, path_id, initial_status, first_step_id, total_steps, progress_percentage))
            logger.debug(f"Successfully enrolled user_id {user_id} in path_id {path_id} with status '{initial_status}' and {total_steps} steps. First step ID: {first_step_id}")
            return True
        except Exception as e:
            # Consider specific exception handling for duplicate entry if UNIQUE constraint is violated
            # although get_user_enrollment should prevent this.
            logger.error(f"DB error enrolling user_id {user_id} in path_id {path_id}: {e}")
            return False

    
    def complete_step(self, user_id: str, path_id: int, completed_step_id: int) -> bool:
        """
        Marks a step as completed for a user in a learning path and advances to the next step.

        Args:
            user_id: The ID of the user.
            path_id: The ID of the learning path.
            completed_step_id: The ID of the step that was completed.

        Returns:
            True if the step was successfully marked completed and progress updated, False otherwise.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error(f"Cannot complete step for user {user_id}, path {path_id}: DB not active.")
            return False

        enrollment = self.get_user_enrollment(user_id, path_id)
        if not enrollment:
            logger.warning(f"User {user_id} not enrolled in path {path_id}. Cannot complete step.")
            return False
        
        if enrollment['status'] == 'completed':
            # If the path is already marked as completed, and the step being completed is the current_step_id (which should be None)
            # or if current_step_id is the completed_step_id (meaning this is a re-completion of the last step)
            # it's arguably fine / a no-op. For now, let's assume this is okay.
            if enrollment.get('current_step_id') is None or enrollment.get('current_step_id') == completed_step_id:
                 logger.debug(f"Path {path_id} already completed by user {user_id} and this step completion is consistent or a re-completion of the last step.")
                 return True
            else:
                logger.warning(f"Path {path_id} already completed by user {user_id}, but trying to complete step {completed_step_id} which is not the recorded last step ({enrollment.get('current_step_id')}).")
                return False


        # Phase 1: Assuming steps are completed in order.
        # The 'current_step_id' in enrollment table is the step the user IS CURRENTLY ON / EXPECTED TO COMPLETE.
        if enrollment.get('current_step_id') != completed_step_id:
            logger.warning(f"User {user_id} in path {path_id} is trying to complete step {completed_step_id}, but is expected to complete step {enrollment.get('current_step_id')}.")
            return False
        
        path_steps = self.get_path_steps(path_id)
        if not path_steps:
            logger.error(f"No steps found for path {path_id}. Cannot complete step {completed_step_id}.")
            return False

        current_step_index = -1
        for i, step in enumerate(path_steps):
            if step.get('id') == completed_step_id: # use .get for safety
                current_step_index = i
                break
        
        if current_step_index == -1:
            logger.error(f"Completed_step_id {completed_step_id} not found in path_steps for path {path_id}.")
            return False

        next_step_id: Optional[int] = None
        new_status = enrollment['status'] # Default to current status, usually 'in_progress'
        
        if current_step_index + 1 < len(path_steps):
            next_step_data = path_steps[current_step_index + 1]
            if isinstance(next_step_data, dict) and 'id' in next_step_data:
                next_step_id = next_step_data['id']
                new_status = 'in_progress' # Explicitly set as in_progress
            else:
                logger.error(f"Next step data for path {path_id} is malformed. Step data: {next_step_data}")
                return False # Data integrity issue
        else: # This was the last step
            new_status = 'completed'
            next_step_id = None # No next step

        total_steps = enrollment.get('total_steps')
        if total_steps is None or total_steps == 0: # Fallback if total_steps wasn't set correctly during enrollment
            logger.warning(f"total_steps for user {user_id}, path {path_id} is {total_steps}. Using len(path_steps).")
            total_steps = len(path_steps)
            if total_steps == 0: # Should not happen if path_steps is not empty
                 progress_percentage = 100.0
                 if new_status != 'completed': # Path with no steps should be completed
                    new_status = 'completed'
                    next_step_id = None
            else:
                progress_percentage = ((current_step_index + 1) / total_steps) * 100.0
        else:
            progress_percentage = ((current_step_index + 1) / total_steps) * 100.0
        
        if new_status == 'completed':
            progress_percentage = 100.0 # Ensure it's exactly 100 for completed paths

        update_query = """
            UPDATE user_learning_paths
            SET status = %s, current_step_id = %s, progress_percentage = %s, 
                completed_at = IF(%s = 'completed', NOW(), completed_at), 
                updated_at = NOW()
            WHERE user_id = %s AND path_id = %s AND (status != 'completed' OR current_step_id = %s OR current_step_id IS NULL)
        """
        # The WHERE clause addition (status != 'completed' OR current_step_id = %s) is to prevent accidental updates
        # if this method is somehow called again for an already completed path for a *different* step.
        # It allows re-completing the *actual* last step of an already completed path (e.g. to trigger something).
        try:
            self.db.execute_query(update_query, (
                new_status, 
                next_step_id, 
                round(progress_percentage, 2),
                new_status, # For the IF condition regarding completed_at
                user_id, 
                path_id,
                completed_step_id # For the WHERE clause condition
            ))
            logger.debug(f"User {user_id} completed step {completed_step_id} in path {path_id}. New current_step_id: {next_step_id}, Status: {new_status}, Progress: {progress_percentage:.2f}%")
            return True
        except Exception as e:
            logger.error(f"DB error updating step completion for user {user_id}, path {path_id}: {e}")
            return False

    def get_user_enrolled_paths_with_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all learning paths a user is enrolled in, along with their progress.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of dictionaries, each representing an enrolled path with its details
            and user's progress, or an empty list if none found or DB error.
        """
        if not self.db or not self.db.connection or not self.db.connection.is_connected():
            logger.error(f"Cannot fetch enrolled paths for user {user_id}: DB not active.")
            return []

        query = """
            SELECT 
                lp.id AS path_id,
                lp.path_name,
                lp.description_en, 
                lp.difficulty_level,
                lp.estimated_hours,
                lp.skills_learned,
                lp.path_order,
                ulp.status,
                ulp.current_step_id,
                ulp.total_steps,
                ulp.progress_percentage,
                ulp.started_at AS enrollment_started_at,
                ulp.completed_at AS enrollment_completed_at,
                ulp.updated_at AS enrollment_updated_at
            FROM user_learning_paths ulp
            JOIN learning_paths lp ON ulp.path_id = lp.id
            WHERE ulp.user_id = %s
            ORDER BY lp.path_order ASC, ulp.started_at DESC 
        """
        # Added lp.path_order to the SELECT and ORDER BY for consistent path ordering
        try:
            results = self.db.execute_query(query, (user_id,))
            if results:
                # Assuming results from db.execute_query is already List[Dict[str, Any]]
                logger.debug(f"Successfully fetched {len(results)} enrolled paths for user {user_id}.")
                return results
            else:
                logger.debug(f"No enrolled paths found for user {user_id}.")
                return []
        except Exception as e:
            logger.error(f"DB error fetching enrolled paths for user {user_id}: {e}")
            return []

if __name__ == '__main__':
    # Basic test (optional, for development)
    logger.debug("Attempting to instantiate LearningPathManager for basic test...")
    manager = LearningPathManager()
    if manager.db and manager.db.connection and manager.db.connection.is_connected():
        logger.debug("LearningPathManager instantiated and connected for basic test.")
    else:
        logger.error("LearningPathManager failed to instantiate or connect for basic test.")
