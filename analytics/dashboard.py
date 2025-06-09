# analytics/dashboard.py
"""
Educational Analytics Dashboard for Java Peer Review Training System.

This module provides comprehensive analytics and insights for instructors
to understand student learning patterns and system effectiveness.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from analytics.behavior_tracker import behavior_tracker
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EducationalAnalyticsDashboard:
    """
    Comprehensive analytics dashboard for educational insights.
    """
    
    def __init__(self):
        """Initialize the analytics dashboard."""
        self.db = behavior_tracker.db
        
    def render_dashboard(self):
        """Render the complete analytics dashboard."""
        st.title("📊 Educational Analytics Dashboard")
        st.markdown("### Comprehensive insights into student learning patterns and system effectiveness")
        
        # Sidebar controls
        self._render_sidebar_controls()
        
        # Main dashboard content
        time_range = st.session_state.get("analytics_time_range", 30)
        
        # Overview metrics
        self._render_overview_metrics(time_range)
        
        # Detailed analytics tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Engagement", "🎯 Learning Progress", "🔍 Error Analysis", 
            "🚀 Feature Usage", "👥 Student Insights"
        ])
        
        with tab1:
            self._render_engagement_analytics(time_range)
        
        with tab2:
            self._render_learning_progress_analytics(time_range)
        
        with tab3:
            self._render_error_analysis(time_range)
        
        with tab4:
            self._render_feature_usage_analytics(time_range)
        
        with tab5:
            self._render_student_insights(time_range)
    
    def _render_sidebar_controls(self):
        """Render sidebar controls for filtering and options."""
        st.sidebar.markdown("## 🎛️ Dashboard Controls")
        
        # Time range selector
        time_range = st.sidebar.selectbox(
            "📅 Time Range",
            options=[7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Last {x} days",
            key="analytics_time_range"
        )
        
        # Refresh data button
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Export options
        st.sidebar.markdown("## 📤 Export Options")
        
        export_format = st.sidebar.selectbox(
            "Export Format",
            options=["CSV", "JSON", "PDF Report"],
            key="export_format"
        )
        
        if st.sidebar.button("📥 Export Data", use_container_width=True):
            self._export_analytics_data(time_range, export_format)
        
        # Settings
        st.sidebar.markdown("## ⚙️ Settings")
        
        st.sidebar.checkbox("Show individual student data", key="show_individual_data")
        st.sidebar.checkbox("Include practice sessions only", key="practice_only")
        st.sidebar.checkbox("Real-time updates", key="realtime_updates")
    
    def _render_overview_metrics(self, time_range: int):
        """Render high-level overview metrics."""
        st.markdown("## 📊 Overview Metrics")
        
        # Get overview data
        overview_data = self._get_overview_data(time_range)
        
        # Create metric columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Active Students",
                overview_data.get("active_students", 0),
                delta=overview_data.get("active_students_delta", 0),
                help="Students who have logged in within the time period"
            )
        
        with col2:
            st.metric(
                "Total Sessions",
                overview_data.get("total_sessions", 0),
                delta=overview_data.get("sessions_delta", 0),
                help="Total learning sessions started"
            )
        
        with col3:
            completion_rate = overview_data.get("completion_rate", 0)
            st.metric(
                "Completion Rate",
                f"{completion_rate:.1f}%",
                delta=f"{overview_data.get('completion_delta', 0):.1f}%",
                help="Percentage of workflows completed successfully"
            )
        
        with col4:
            avg_accuracy = overview_data.get("avg_accuracy", 0)
            st.metric(
                "Average Accuracy",
                f"{avg_accuracy:.1f}%",
                delta=f"{overview_data.get('accuracy_delta', 0):.1f}%",
                help="Average accuracy across all reviews"
            )
        
        with col5:
            practice_adoption = overview_data.get("practice_adoption", 0)
            st.metric(
                "Practice Adoption",
                f"{practice_adoption:.1f}%",
                delta=f"{overview_data.get('practice_delta', 0):.1f}%",
                help="Percentage of students using practice mode"
            )
    
    def _render_engagement_analytics(self, time_range: int):
        """Render student engagement analytics."""
        st.markdown("## 📈 Student Engagement Analysis")
        
        # Session patterns
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily activity heatmap
            activity_data = self._get_daily_activity_data(time_range)
            if activity_data:
                fig = self._create_activity_heatmap(activity_data)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Session duration distribution
            duration_data = self._get_session_duration_data(time_range)
            if duration_data:
                fig = self._create_duration_distribution(duration_data)
                st.plotly_chart(fig, use_container_width=True)
        
        # Engagement trends
        st.markdown("### 📅 Engagement Trends")
        
        engagement_trends = self._get_engagement_trends(time_range)
        if engagement_trends:
            fig = self._create_engagement_trends_chart(engagement_trends)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top engaged students (if enabled)
        if st.session_state.get("show_individual_data", False):
            st.markdown("### 🏆 Most Engaged Students")
            top_students = self._get_top_engaged_students(time_range)
            if top_students:
                st.dataframe(top_students, use_container_width=True)
    
    def _render_learning_progress_analytics(self, time_range: int):
        """Render learning progress analytics."""
        st.markdown("## 🎯 Learning Progress Analysis")
        
        # Mastery levels across categories
        mastery_data = self._get_mastery_data(time_range)
        if mastery_data:
            fig = self._create_mastery_chart(mastery_data)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Learning curve analysis
            learning_curves = self._get_learning_curves(time_range)
            if learning_curves:
                fig = self._create_learning_curves_chart(learning_curves)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Difficulty progression
            difficulty_progress = self._get_difficulty_progression(time_range)
            if difficulty_progress:
                fig = self._create_difficulty_progression_chart(difficulty_progress)
                st.plotly_chart(fig, use_container_width=True)
        
        # Progress summary table
        st.markdown("### 📊 Category-wise Progress Summary")
        progress_summary = self._get_progress_summary(time_range)
        if progress_summary:
            st.dataframe(progress_summary, use_container_width=True)
    
    def _render_error_analysis(self, time_range: int):
        """Render error identification analysis."""
        st.markdown("## 🔍 Error Identification Analysis")
        
        # Most challenging errors
        challenging_errors = self._get_challenging_errors(time_range)
        if challenging_errors:
            fig = self._create_challenging_errors_chart(challenging_errors)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Error category performance
            category_performance = self._get_category_performance(time_range)
            if category_performance:
                fig = self._create_category_performance_chart(category_performance)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Time to identify trends
            time_trends = self._get_identification_time_trends(time_range)
            if time_trends:
                fig = self._create_time_trends_chart(time_trends)
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed error statistics
        st.markdown("### 📋 Detailed Error Statistics")
        error_stats = self._get_detailed_error_stats(time_range)
        if error_stats:
            st.dataframe(error_stats, use_container_width=True)
    
    def _render_feature_usage_analytics(self, time_range: int):
        """Render feature usage analytics."""
        st.markdown("## 🚀 Feature Usage Analysis")
        
        # Feature adoption rates
        feature_adoption = self._get_feature_adoption(time_range)
        if feature_adoption:
            fig = self._create_feature_adoption_chart(feature_adoption)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tab navigation patterns
            tab_patterns = self._get_tab_navigation_patterns(time_range)
            if tab_patterns:
                fig = self._create_tab_patterns_chart(tab_patterns)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Workflow vs Practice usage
            usage_comparison = self._get_usage_comparison(time_range)
            if usage_comparison:
                fig = self._create_usage_comparison_chart(usage_comparison)
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_student_insights(self, time_range: int):
        """Render individual student insights."""
        st.markdown("## 👥 Student Insights")
        
        if not st.session_state.get("show_individual_data", False):
            st.info("Enable 'Show individual student data' in the sidebar to view this section.")
            return
        
        # Student selector
        students = self._get_student_list()
        selected_student = st.selectbox(
            "Select Student",
            options=[s['uid'] for s in students],
            format_func=lambda x: next((s['email'] for s in students if s['uid'] == x), x),
            key="selected_student"
        )
        
        if selected_student:
            # Individual student analytics
            student_analytics = self._get_student_analytics(selected_student, time_range)
            
            # Student performance summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Sessions", student_analytics.get("session_count", 0))
            with col2:
                st.metric("Avg Accuracy", f"{student_analytics.get('avg_accuracy', 0):.1f}%")
            with col3:
                st.metric("Mastery Level", f"{student_analytics.get('overall_mastery', 0):.2f}")
            
            # Individual charts
            self._render_individual_student_charts(selected_student, time_range)
    
    def _get_overview_data(self, time_range: int) -> Dict[str, Any]:
        """Get overview metrics data."""
        try:
            start_date = datetime.now() - timedelta(days=time_range)
            
            # Active students
            active_students_query = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM user_sessions 
            WHERE session_start >= %s
            """
            active_result = self.db.execute_query(active_students_query, (start_date,), fetch_one=True)
            active_students = active_result['count'] if active_result else 0
            
            # Total sessions
            sessions_query = """
            SELECT COUNT(*) as count
            FROM user_sessions 
            WHERE session_start >= %s
            """
            sessions_result = self.db.execute_query(sessions_query, (start_date,), fetch_one=True)
            total_sessions = sessions_result['count'] if sessions_result else 0
            
            # Completion rate
            completion_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM workflow_tracking 
            WHERE started_at >= %s
            """
            completion_result = self.db.execute_query(completion_query, (start_date,), fetch_one=True)
            completion_rate = 0
            if completion_result and completion_result['total'] > 0:
                completion_rate = (completion_result['completed'] / completion_result['total']) * 100
            
            # Average accuracy
            accuracy_query = """
            SELECT AVG(JSON_EXTRACT(final_results, '$.accuracy')) as avg_accuracy
            FROM workflow_tracking 
            WHERE started_at >= %s AND status = 'completed'
            """
            accuracy_result = self.db.execute_query(accuracy_query, (start_date,), fetch_one=True)
            avg_accuracy = accuracy_result['avg_accuracy'] if accuracy_result and accuracy_result['avg_accuracy'] else 0
            
            # Practice adoption
            practice_query = """
            SELECT 
                COUNT(DISTINCT user_id) as practice_users,
                (SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE session_start >= %s) as total_users
            FROM practice_sessions 
            WHERE started_at >= %s
            """
            practice_result = self.db.execute_query(practice_query, (start_date, start_date), fetch_one=True)
            practice_adoption = 0
            if practice_result and practice_result['total_users'] > 0:
                practice_adoption = (practice_result['practice_users'] / practice_result['total_users']) * 100
            
            return {
                "active_students": active_students,
                "total_sessions": total_sessions,
                "completion_rate": completion_rate,
                "avg_accuracy": avg_accuracy,
                "practice_adoption": practice_adoption,
                # Deltas would require historical comparison - simplified for now
                "active_students_delta": 0,
                "sessions_delta": 0,
                "completion_delta": 0,
                "accuracy_delta": 0,
                "practice_delta": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting overview data: {str(e)}")
            return {}
    
    def _get_daily_activity_data(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get daily activity data for heatmap."""
        try:
            start_date = datetime.now() - timedelta(days=time_range)
            
            query = """
            SELECT 
                DATE(session_start) as date,
                HOUR(session_start) as hour,
                COUNT(*) as session_count
            FROM user_sessions 
            WHERE session_start >= %s
            GROUP BY DATE(session_start), HOUR(session_start)
            ORDER BY date, hour
            """
            
            results = self.db.execute_query(query, (start_date,))
            if results:
                return pd.DataFrame(results)
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily activity data: {str(e)}")
            return None
    
    def _create_activity_heatmap(self, data: pd.DataFrame) -> go.Figure:
        """Create activity heatmap."""
        try:
            # Pivot data for heatmap
            heatmap_data = data.pivot(index='hour', columns='date', values='session_count').fillna(0)
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Blues',
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Daily Activity Heatmap",
                xaxis_title="Date",
                yaxis_title="Hour of Day",
                height=400
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating activity heatmap: {str(e)}")
            return go.Figure()
    
    def _get_student_list(self) -> List[Dict[str, str]]:
        """Get list of students."""
        try:
            query = "SELECT uid, email FROM users ORDER BY email"
            results = self.db.execute_query(query)
            return results if results else []
        except Exception as e:
            logger.error(f"Error getting student list: {str(e)}")
            return []
    
    def _export_analytics_data(self, time_range: int, format_type: str):
        """Export analytics data in specified format."""
        try:
            if format_type == "CSV":
                # Get overview data and convert to CSV
                overview_data = self._get_overview_data(time_range)
                df = pd.DataFrame([overview_data])
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            elif format_type == "JSON":
                import json
                overview_data = self._get_overview_data(time_range)
                json_data = json.dumps(overview_data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            else:
                st.info("PDF export functionality would be implemented here")
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            st.error("Error exporting data. Please try again.")
    
    # Placeholder methods for additional chart creation
    # These would be implemented with actual data queries and Plotly charts
    
    def _get_session_duration_data(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get session duration data.""" 
        # Implementation would query session durations and return DataFrame
        return None
    
    def _create_duration_distribution(self, data: pd.DataFrame) -> go.Figure:
        """Create session duration distribution chart."""
        return go.Figure()
    
    def _get_engagement_trends(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get engagement trends over time."""
        return None
    
    def _create_engagement_trends_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create engagement trends chart."""
        return go.Figure()
    
    def _get_top_engaged_students(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get most engaged students."""
        return None
    
    def _get_mastery_data(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get mastery level data."""
        return None
    
    def _create_mastery_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create mastery levels chart."""
        return go.Figure()
    
    def _get_learning_curves(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get learning curve data."""
        return None
    
    def _create_learning_curves_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create learning curves chart."""
        return go.Figure()
    
    def _get_difficulty_progression(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get difficulty progression data."""
        return None
    
    def _create_difficulty_progression_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create difficulty progression chart."""
        return go.Figure()
    
    def _get_progress_summary(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get progress summary data."""
        return None
    
    def _get_challenging_errors(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get most challenging errors data."""
        return None
    
    def _create_challenging_errors_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create challenging errors chart."""
        return go.Figure()
    
    def _get_category_performance(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get category performance data."""
        return None
    
    def _create_category_performance_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create category performance chart."""
        return go.Figure()
    
    def _get_identification_time_trends(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get identification time trends."""
        return None
    
    def _create_time_trends_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create time trends chart."""
        return go.Figure()
    
    def _get_detailed_error_stats(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get detailed error statistics."""
        return None
    
    def _get_feature_adoption(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get feature adoption data."""
        return None
    
    def _create_feature_adoption_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create feature adoption chart."""
        return go.Figure()
    
    def _get_tab_navigation_patterns(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get tab navigation patterns."""
        return None
    
    def _create_tab_patterns_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create tab patterns chart."""
        return go.Figure()
    
    def _get_usage_comparison(self, time_range: int) -> Optional[pd.DataFrame]:
        """Get usage comparison data."""
        return None
    
    def _create_usage_comparison_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create usage comparison chart."""
        return go.Figure()
    
    def _get_student_analytics(self, student_id: str, time_range: int) -> Dict[str, Any]:
        """Get individual student analytics."""
        return behavior_tracker.get_user_analytics(student_id, time_range)
    
    def _render_individual_student_charts(self, student_id: str, time_range: int):
        """Render charts for individual student."""
        st.info("Individual student charts would be implemented here with specific student data.")

# Convenience function for easy integration
def render_analytics_dashboard():
    """Render the analytics dashboard."""
    dashboard = EducationalAnalyticsDashboard()
    dashboard.render_dashboard()