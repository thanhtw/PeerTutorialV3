import streamlit as st
import os
import logging
import time
import json
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from data.mysql_connection import MySQLConnection


logger = logging.getLogger(__name__)

class UserPracticeTracker:
    """Class to track user practice progress on individual errors."""
    
    def __init__(self):
        self.db = MySQLConnection()
    
    def get_user_practice_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive practice data for a user."""
        if not user_id:
            return {"practiced_errors": [], "unpracticed_errors": [], "practice_stats": {}}
        
        try:
            # Get practiced errors with statistics
            practiced_query = """
            SELECT 
                uep.*,
                je.difficulty_level,
                ec.name_en as category_name_en,
                ec.name_zh as category_name_zh
            FROM user_error_practice uep
            JOIN java_errors je ON uep.error_code = je.error_code
            JOIN error_categories ec ON je.category_id = ec.id
            WHERE uep.user_id = %s AND uep.practice_count > 0
            ORDER BY uep.last_practiced DESC
            """
            practiced_errors = self.db.execute_query(practiced_query, (user_id,)) or []
            
            # Get all available errors
            all_errors_query = """
            SELECT 
                je.error_code,
                je.error_name_en,
                je.error_name_zh,
                je.description_en,
                je.description_zh,
                je.implementation_guide_en,
                je.implementation_guide_zh,
                je.difficulty_level,
                ec.name_en as category_name_en,
                ec.name_zh as category_name_zh
            FROM java_errors je
            JOIN error_categories ec ON je.category_id = ec.id
            ORDER BY ec.sort_order, je.error_name_en
            """
            all_errors = self.db.execute_query(all_errors_query) or []
            
            # Separate practiced and unpracticed
            practiced_codes = {error['error_code'] for error in practiced_errors}
            unpracticed_errors = [error for error in all_errors if error['error_code'] not in practiced_codes]
            
            # Get overall practice statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_practiced,
                SUM(CASE WHEN completion_status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN completion_status = 'mastered' THEN 1 ELSE 0 END) as mastered_count,
                AVG(best_accuracy) as avg_accuracy,
                SUM(total_time_spent) as total_time,
                MAX(last_practiced) as last_session
            FROM user_error_practice 
            WHERE user_id = %s
            """
            stats_result = self.db.execute_query(stats_query, (user_id,), fetch_one=True)
            practice_stats = stats_result or {}
            
            return {
                "practiced_errors": practiced_errors,
                "unpracticed_errors": unpracticed_errors,
                "practice_stats": practice_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user practice data: {str(e)}")
            return {"practiced_errors": [], "unpracticed_errors": [], "practice_stats": {}}
    
    def start_practice_session(self, user_id: str, error_data: Dict[str, Any]) -> None:
        """Record the start of a practice session."""
        if not user_id:
            return
            
        try:
            error_code = error_data.get('error_code', '')
            error_name_en = error_data.get('error_name', '')
            error_name_zh = error_data.get('error_name_zh', error_name_en)
            category = error_data.get('category', '')
            
            # Insert or update practice record
            upsert_query = """
            INSERT INTO user_error_practice 
            (user_id, error_code, error_name_en, error_name_zh, category_name, 
             practice_count, total_attempts, completion_status, last_practiced)
            VALUES (%s, %s, %s, %s, %s, 1, 1, 'in_progress', NOW())
            ON DUPLICATE KEY UPDATE
                practice_count = practice_count + 1,
                total_attempts = total_attempts + 1,
                completion_status = CASE 
                    WHEN completion_status = 'not_started' THEN 'in_progress'
                    ELSE completion_status 
                END,
                last_practiced = NOW(),
                updated_at = NOW()
            """
            
            self.db.execute_query(upsert_query, (
                user_id, error_code, error_name_en, error_name_zh, category
            ))
            
            logger.debug(f"Started practice session for user {user_id}, error {error_code}")
            
        except Exception as e:
            logger.error(f"Error starting practice session: {str(e)}")
    
    def complete_practice_session(self, user_id: str, error_code: str, 
                                session_data: Dict[str, Any]) -> None:
        """Record the completion of a practice session with results."""
        if not user_id or not error_code:
            return
            
        try:
            accuracy = session_data.get('accuracy', 0.0)
            time_spent = session_data.get('time_spent_seconds', 0)
            successful = session_data.get('successful_completion', False)
            
            # Determine completion status based on performance
            if accuracy >= 90:
                status = 'mastered'
                mastery_level = min(100.0, accuracy)
            elif accuracy >= 70:
                status = 'completed'
                mastery_level = accuracy
            else:
                status = 'in_progress'
                mastery_level = accuracy * 0.8  # Partial mastery
            
            update_query = """
            UPDATE user_error_practice SET
                successful_completions = CASE WHEN %s THEN successful_completions + 1 ELSE successful_completions END,
                best_accuracy = GREATEST(best_accuracy, %s),
                total_time_spent = total_time_spent + %s,
                completion_status = CASE 
                    WHEN %s >= 90 THEN 'mastered'
                    WHEN %s >= 70 THEN 'completed'
                    ELSE completion_status
                END,
                mastery_level = GREATEST(mastery_level, %s),
                last_practiced = NOW(),
                updated_at = NOW()
            WHERE user_id = %s AND error_code = %s
            """
            
            self.db.execute_query(update_query, (
                successful, accuracy, time_spent, accuracy, accuracy, 
                mastery_level, user_id, error_code
            ))
            
            logger.debug(f"Completed practice session for user {user_id}, error {error_code}, accuracy: {accuracy}%")
            
        except Exception as e:
            logger.error(f"Error completing practice session: {str(e)}")