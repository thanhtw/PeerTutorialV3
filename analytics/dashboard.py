# analytics/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from analytics.behavior_tracker import behavior_tracker

def render_instructor_analytics():
    """Render instructor analytics dashboard."""
    st.title("📊 Student Behavior Analytics")
    
    # Time range selector
    days = st.selectbox("Time Range", [7, 14, 30, 90], index=2)
    
    # Get all users (you'll need to implement this query)
    users_query = "SELECT uid, email FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"
    users = behavior_tracker.db.execute_query(users_query, (days,))
    
    if not users:
        st.info("No user activity in the selected time range.")
        return
    
    # Overall statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Users", len(users))
    
    with col2:
        # Total sessions
        session_query = """
        SELECT COUNT(*) as count FROM user_sessions 
        WHERE session_start >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        result = behavior_tracker.db.execute_query(session_query, (days,), fetch_one=True)
        st.metric("Total Sessions", result['count'] if result else 0)
    
    with col3:
        # Practice sessions
        practice_query = """
        SELECT COUNT(*) as count FROM practice_sessions 
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        result = behavior_tracker.db.execute_query(practice_query, (days,), fetch_one=True)
        st.metric("Practice Sessions", result['count'] if result else 0)
    
    with col4:
        # Completion rate
        completion_query = """
        SELECT 
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*) * 100 as rate
        FROM workflow_tracking 
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        result = behavior_tracker.db.execute_query(completion_query, (days,), fetch_one=True)
        rate = result['rate'] if result and result['rate'] else 0
        st.metric("Completion Rate", f"{rate:.1f}%")
    
    # Individual user analytics
    st.subheader("Individual User Analytics")
    
    selected_user = st.selectbox(
        "Select User",
        options=[user['uid'] for user in users],
        format_func=lambda x: next((u['email'] for u in users if u['uid'] == x), x)
    )
    
    if selected_user:
        user_analytics = behavior_tracker.get_user_analytics(selected_user, days)
        
        # Display user analytics
        st.json(user_analytics)

# Add to your main navigation
if st.session_state.auth.get("user_level") == "instructor":
    if st.sidebar.button("📊 View Analytics"):
        render_instructor_analytics()