# analytics/monitoring.py
"""
Real-time Monitoring and Performance Optimization for Student Behavior Tracking.

This module provides real-time monitoring capabilities, performance optimization,
and automated alerts for the educational analytics system.
"""

import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from analytics.behavior_tracker import behavior_tracker
from data.mysql_connection import MySQLConnection
import threading
import queue
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Real-time performance monitoring for the behavior tracking system.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.db = MySQLConnection()
        self.metrics_queue = queue.Queue()
        self.alert_thresholds = {
            "high_error_rate": 0.1,  # 10% error rate
            "slow_response_time": 5.0,  # 5 seconds
            "high_session_count": 100,  # 100 concurrent sessions
            "low_completion_rate": 0.3  # 30% completion rate
        }
        self.monitoring_active = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def start_monitoring(self):
        """Start real-time monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.executor.submit(self._monitoring_loop)
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics every 30 seconds
                metrics = self._collect_metrics()
                
                # Check for alerts
                alerts = self._check_alerts(metrics)
                
                # Store metrics
                self._store_metrics(metrics)
                
                # Process alerts
                for alert in alerts:
                    self._process_alert(alert)
                
                time.sleep(30)  # Wait 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            now = datetime.now()
            five_minutes_ago = now - timedelta(minutes=5)
            
            # Active sessions
            session_query = """
            SELECT COUNT(*) as active_sessions
            FROM user_sessions 
            WHERE session_start >= %s AND (session_end IS NULL OR session_end >= %s)
            """
            session_result = self.db.execute_query(
                session_query, (five_minutes_ago, five_minutes_ago), fetch_one=True
            )
            active_sessions = session_result['active_sessions'] if session_result else 0
            
            # Error rate
            error_query = """
            SELECT 
                COUNT(*) as total_interactions,
                SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) as error_count
            FROM user_interactions 
            WHERE timestamp >= %s
            """
            error_result = self.db.execute_query(error_query, (five_minutes_ago,), fetch_one=True)
            
            error_rate = 0
            if error_result and error_result['total_interactions'] > 0:
                error_rate = error_result['error_count'] / error_result['total_interactions']
            
            # Average response time
            response_query = """
            SELECT AVG(time_spent_seconds) as avg_response_time
            FROM user_interactions 
            WHERE timestamp >= %s AND time_spent_seconds > 0
            """
            response_result = self.db.execute_query(response_query, (five_minutes_ago,), fetch_one=True)
            avg_response_time = response_result['avg_response_time'] if response_result else 0
            
            # Completion rate (last hour)
            one_hour_ago = now - timedelta(hours=1)
            completion_query = """
            SELECT 
                COUNT(*) as total_workflows,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_workflows
            FROM workflow_tracking 
            WHERE started_at >= %s
            """
            completion_result = self.db.execute_query(completion_query, (one_hour_ago,), fetch_one=True)
            
            completion_rate = 0
            if completion_result and completion_result['total_workflows'] > 0:
                completion_rate = completion_result['completed_workflows'] / completion_result['total_workflows']
            
            return {
                "timestamp": now.isoformat(),
                "active_sessions": active_sessions,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "completion_rate": completion_rate,
                "total_interactions": error_result['total_interactions'] if error_result else 0
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}
    
    def _check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against alert thresholds."""
        alerts = []
        
        try:
            # High error rate alert
            if metrics.get("error_rate", 0) > self.alert_thresholds["high_error_rate"]:
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"Error rate is {metrics['error_rate']:.2%}",
                    "value": metrics["error_rate"],
                    "threshold": self.alert_thresholds["high_error_rate"]
                })
            
            # Slow response time alert
            if metrics.get("avg_response_time", 0) > self.alert_thresholds["slow_response_time"]:
                alerts.append({
                    "type": "slow_response_time", 
                    "severity": "warning",
                    "message": f"Average response time is {metrics['avg_response_time']:.1f}s",
                    "value": metrics["avg_response_time"],
                    "threshold": self.alert_thresholds["slow_response_time"]
                })
            
            # High session count alert
            if metrics.get("active_sessions", 0) > self.alert_thresholds["high_session_count"]:
                alerts.append({
                    "type": "high_session_count",
                    "severity": "info",
                    "message": f"High concurrent sessions: {metrics['active_sessions']}",
                    "value": metrics["active_sessions"],
                    "threshold": self.alert_thresholds["high_session_count"]
                })
            
            # Low completion rate alert
            if metrics.get("completion_rate", 1) < self.alert_thresholds["low_completion_rate"]:
                alerts.append({
                    "type": "low_completion_rate",
                    "severity": "warning", 
                    "message": f"Low completion rate: {metrics['completion_rate']:.1%}",
                    "value": metrics["completion_rate"],
                    "threshold": self.alert_thresholds["low_completion_rate"]
                })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            
        return alerts
    
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process and handle alerts."""
        try:
            # Log alert
            logger.warning(f"ALERT [{alert['type']}]: {alert['message']}")
            
            # Store alert in database
            self._store_alert(alert)
            
            # Send notifications (email, Slack, etc.)
            # Implementation would depend on your notification system
            
        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")


class BatchProcessor:
    """
    Batch processing for analytics data to improve performance.
    """
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 30):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.interaction_batch = []
        self.last_flush = time.time()
        self.lock = threading.Lock()
        self.db = MySQLConnection()
        
    def add_interaction(self, interaction_data: Dict[str, Any]):
        """Add interaction to batch for processing."""
        with self.lock:
            self.interaction_batch.append(interaction_data)
            
            # Check if we need to flush
            if (len(self.interaction_batch) >= self.batch_size or 
                time.time() - self.last_flush > self.flush_interval):
                self._flush_batch()
    
    def _flush_batch(self):
        """Flush current batch to database."""
        if not self.interaction_batch:
            return
            
        try:
            # Prepare batch insert query
            query = """
            INSERT INTO user_interactions 
            (session_id, user_id, interaction_type, interaction_category, component, 
             action, details, time_spent_seconds, success, error_message, context_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepare batch data
            batch_data = []
            for interaction in self.interaction_batch:
                batch_data.append((
                    interaction.get('session_id'),
                    interaction.get('user_id'),
                    interaction.get('interaction_type'),
                    interaction.get('interaction_category'),
                    interaction.get('component'),
                    interaction.get('action'),
                    json.dumps(interaction.get('details')),
                    interaction.get('time_spent_seconds', 0),
                    interaction.get('success', True),
                    interaction.get('error_message'),
                    json.dumps(interaction.get('context_data'))
                ))
            
            # Execute batch insert
            cursor = self.db._get_connection().cursor()
            cursor.executemany(query, batch_data)
            self.db._get_connection().commit()
            cursor.close()
            
            logger.debug(f"Flushed batch of {len(self.interaction_batch)} interactions")
            
            # Clear batch
            self.interaction_batch.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            logger.error(f"Error flushing batch: {str(e)}")
            # Keep interactions in batch to retry later
    
    def force_flush(self):
        """Force flush current batch."""
        with self.lock:
            self._flush_batch()


class CacheManager:
    """
    Caching manager for frequently accessed analytics data.
    """
    
    def __init__(self, cache_ttl: int = 300):  # 5 minutes default TTL
        """Initialize cache manager."""
        self.cache = {}
        self.cache_ttl = cache_ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return value
            else:
                # Cache expired
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        self.cache[key] = (value, time.time())
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern."""
        if pattern:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
        else:
            self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            k for k, (v, ts) in self.cache.items() 
            if current_time - ts >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]


class OptimizedBehaviorTracker:
    """
    Optimized version of BehaviorTracker with performance improvements.
    """
    
    def __init__(self):
        """Initialize optimized behavior tracker."""
        self.db = MySQLConnection()
        self.batch_processor = BatchProcessor()
        self.cache_manager = CacheManager()
        self.performance_monitor = PerformanceMonitor()
        
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
    def log_interaction_optimized(self, 
                                 user_id: str,
                                 interaction_type: str,
                                 interaction_category: str,
                                 component: str,
                                 action: str,
                                 details: Dict[str, Any] = None,
                                 time_spent_seconds: int = 0,
                                 success: bool = True,
                                 error_message: str = None,
                                 context_data: Dict[str, Any] = None) -> None:
        """
        Optimized interaction logging using batch processing.
        """
        try:
            session_id = st.session_state.get("session_id")
            if not session_id:
                return
            
            # Prepare interaction data
            interaction_data = {
                'session_id': session_id,
                'user_id': user_id,
                'interaction_type': interaction_type,
                'interaction_category': interaction_category,
                'component': component,
                'action': action,
                'details': details,
                'time_spent_seconds': time_spent_seconds,
                'success': success,
                'error_message': error_message,
                'context_data': context_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to batch processor
            self.batch_processor.add_interaction(interaction_data)
            
            # Increment session interaction counter
            st.session_state.interaction_count = st.session_state.get("interaction_count", 0) + 1
            
        except Exception as e:
            logger.error(f"Error logging optimized interaction: {str(e)}")
    
    def get_user_analytics_cached(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user analytics with caching."""
        cache_key = f"user_analytics_{user_id}_{days}"
        
        # Try cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get from database
        analytics = behavior_tracker.get_user_analytics(user_id, days)
        
        # Cache result
        self.cache_manager.set(cache_key, analytics)
        
        return analytics
    
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old tracking data to maintain performance."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Tables to clean up with their date columns
            cleanup_tables = [
                ("user_interactions", "timestamp"),         
                ("tab_navigation", "timestamp")
            ]
            
            for table, date_column in cleanup_tables:
                delete_query = f"DELETE FROM {table} WHERE {date_column} < %s"
                deleted_rows = self.db.execute_query(delete_query, (cutoff_date,))
                logger.info(f"Cleaned up {deleted_rows} rows from {table}")
            
            # Optimize tables after cleanup
            for table, _ in cleanup_tables:
                optimize_query = f"OPTIMIZE TABLE {table}"
                self.db.execute_query(optimize_query)
            
            logger.info(f"Completed cleanup of data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


class RealTimeAnalytics:
    """
    Real-time analytics dashboard for live monitoring.
    """
    
    def __init__(self):
        """Initialize real-time analytics."""
        self.db = MySQLConnection()
        
    def render_realtime_dashboard(self):
        """Render real-time analytics dashboard."""
        st.title("📊 Real-Time System Analytics")
        
        # Auto-refresh every 30 seconds
        if st.checkbox("Auto-refresh (30s)", value=True):
            time.sleep(30)
            st.rerun()
        
        # System health overview
        col1, col2, col3, col4 = st.columns(4)
        
        health_data = self._get_realtime_health()
        
        with col1:
            st.metric(
                "Active Sessions",
                health_data.get("active_sessions", 0),
                delta=health_data.get("sessions_delta", 0)
            )
        
        with col2:
            error_rate = health_data.get("error_rate", 0)
            st.metric(
                "Error Rate",
                f"{error_rate:.1%}",
                delta=f"{health_data.get('error_delta', 0):.1%}",
                delta_color="inverse"
            )
        
        with col3:
            response_time = health_data.get("avg_response_time", 0)
            st.metric(
                "Avg Response Time",
                f"{response_time:.1f}s",
                delta=f"{health_data.get('response_delta', 0):.1f}s",
                delta_color="inverse"
            )
        
        with col4:
            completion_rate = health_data.get("completion_rate", 0)
            st.metric(
                "Completion Rate",
                f"{completion_rate:.1%}",
                delta=f"{health_data.get('completion_delta', 0):.1%}"
            )
        
        # Real-time charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Activity timeline
            activity_data = self._get_activity_timeline()
            if activity_data:
                st.line_chart(activity_data)
        
        with col2:
            # Error distribution
            error_data = self._get_error_distribution()
            if error_data:
                st.bar_chart(error_data)
        
       

    
    def _get_activity_timeline(self):
        """Get activity timeline data."""
        # Implementation would return time-series data for charting
        return None
    
    def _get_error_distribution(self):
        """Get error distribution data."""
        # Implementation would return error type distribution
        return None
    

# Global instances
optimized_tracker = OptimizedBehaviorTracker()
realtime_analytics = RealTimeAnalytics()

# Convenience functions
def start_performance_monitoring():
    """Start performance monitoring."""
    optimized_tracker.performance_monitor.start_monitoring()

def stop_performance_monitoring():
    """Stop performance monitoring.""" 
    optimized_tracker.performance_monitor.stop_monitoring()

def cleanup_old_tracking_data(days: int = 90):
    """Clean up old tracking data."""
    optimized_tracker.cleanup_old_data(days)

def render_monitoring_dashboard():
    """Render the monitoring dashboard."""
    realtime_analytics.render_realtime_dashboard()