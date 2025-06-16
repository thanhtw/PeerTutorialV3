# ui/components/workflow_progress.py - FIXED VERSION
"""
FIXED: Workflow Progress Indicator Component that properly renders HTML.
The issue was with HTML structure and unsafe_allow_html parameter.
"""

import streamlit as st
import logging
from utils.language_utils import t

logger = logging.getLogger(__name__)

class WorkflowProgressIndicator:
    """FIXED: Visual progress indicator that properly renders HTML."""
    
    @staticmethod
    def render_progress_bar():
        """FIXED: Render workflow progress bar with proper HTML rendering."""
        try:
            # Get workflow context safely
            try:
                from utils.workflow_state_manager import WorkflowStateManager
                context = WorkflowStateManager.get_workflow_context()
                status = context.get("status", "not_started")
            except (ImportError, Exception) as e:
                logger.debug(f"WorkflowStateManager not available: {str(e)}, using default status")
                status = "not_started"
            
            # Define workflow steps with proper translations
            steps = [
                {
                    "id": "generate", 
                    "label": t("generate_code") if hasattr(st, 'session_state') else "Generate Code", 
                    "icon": "🔧",
                    "description": t("create_practice_challenge") if hasattr(st, 'session_state') else "Create a practice challenge"
                },
                {
                    "id": "review", 
                    "label": t("review_code") if hasattr(st, 'session_state') else "Review Code", 
                    "icon": "📋",
                    "description": t("analyze_and_find_errors") if hasattr(st, 'session_state') else "Analyze and find errors"
                },
                {
                    "id": "feedback", 
                    "label": t("get_feedback") if hasattr(st, 'session_state') else "Get Feedback", 
                    "icon": "📊",
                    "description": t("view_results_and_learn") if hasattr(st, 'session_state') else "View results and learn"
                }
            ]
            
            # Determine current step
            step_map = {
                "not_started": 0,
                "code_generated": 1,
                "review_in_progress": 1,
                "review_completed": 2
            }
            current_step = step_map.get(status, 0)
            
            # FIXED: Build proper HTML structure with corrected syntax
            progress_html_parts = []
            
            # CSS styles embedded (in case external CSS fails)
            progress_html_parts.append("""
            <style>
            .workflow-progress-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin: 1rem 0 2rem 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .progress-header h4 {
                text-align: center;
                margin: 0 0 1rem 0;
                font-weight: 600;
                color: white;
            }
            .progress-steps {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 1rem;
                flex-wrap: wrap;
            }
            .progress-step {
                display: flex;
                flex-direction: column;
                align-items: center;
                min-width: 80px;
                opacity: 0.6;
                transition: all 0.3s ease;
            }
            .progress-step.active {
                opacity: 1;
                transform: scale(1.1);
            }
            .progress-step.completed {
                opacity: 0.9;
            }
            .step-circle {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: rgba(255,255,255,0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 0.5rem;
            }
            .progress-step.active .step-circle {
                background: rgba(255,255,255,0.3);
                box-shadow: 0 0 20px rgba(255,255,255,0.4);
            }
            .progress-step.completed .step-circle {
                background: rgba(40,167,69,0.8);
            }
            .step-icon {
                font-size: 1.5rem;
            }
            .step-label {
                font-size: 0.8rem;
                text-align: center;
                font-weight: 500;
            }
            .step-number {
                font-size: 0.7rem;
                opacity: 0.8;
                margin-top: 0.25rem;
            }
            .step-connector {
                width: 40px;
                height: 3px;
                background: rgba(255,255,255,0.3);
                border-radius: 2px;
            }
            .step-connector.completed {
                background: rgba(255,255,255,0.7);
            }
            </style>
            """)
            
            # Container start
            journey_title = t('your_learning_journey') if hasattr(st, 'session_state') else "Your Learning Journey"
            progress_html_parts.append(f"""
            <div class="workflow-progress-container">
                <div class="progress-header">
                    <h4>{journey_title}</h4>
                </div>
                <div class="progress-steps">
            """)
            
            # Generate steps
            for i, step in enumerate(steps):
                # Determine step state
                if i < current_step:
                    step_class = "completed"
                    step_icon = "✅"
                elif i == current_step:
                    step_class = "active"
                    step_icon = step["icon"]
                else:
                    step_class = "pending"
                    step_icon = step["icon"]
                
                # Add step HTML
                progress_html_parts.append(f"""
                    <div class="progress-step {step_class}" title="{step['description']}">
                        <div class="step-circle">
                            <span class="step-icon">{step_icon}</span>
                        </div>
                        <div class="step-label">{step['label']}</div>
                        <div class="step-number">{i+1}</div>
                    </div>
                """)
                
                # Add connector between steps
                if i < len(steps) - 1:
                    connector_class = "completed" if i < current_step else "pending"
                    progress_html_parts.append(f'<div class="step-connector {connector_class}"></div>')
            
            # Container end
            progress_html_parts.append("""
                </div>
            </div>
            """)
            
            # FIXED: Join all parts and render with unsafe_allow_html=True
            complete_html = "".join(progress_html_parts)
            st.markdown(complete_html, unsafe_allow_html=True)
            
            logger.debug("Workflow progress bar rendered successfully")
            
        except Exception as e:
            logger.error(f"Error rendering workflow progress: {str(e)}")
            # FIXED: Fallback to simple text-based progress indicator
            try:
                journey_title = t('your_learning_journey') if hasattr(st, 'session_state') else "Your Learning Journey"
                st.info(f"🎯 {journey_title}")
                
                # Simple text-based progress
                steps = ["🔧 Generate Code", "📋 Review Code", "📊 Get Feedback"]
                current_step = 0
                
                progress_text = " → ".join([
                    f"**{step}**" if i == current_step else f"~~{step}~~" if i < current_step else step
                    for i, step in enumerate(steps)
                ])
                
                st.markdown(progress_text)
                
            except Exception as fallback_error:
                logger.error(f"Fallback progress indicator also failed: {str(fallback_error)}")
                # Ultimate fallback - just show a simple message
                st.info("🎯 Learning Progress: Generate → Review → Feedback")
    
    @staticmethod
    def render_context_guidance():
        """FIXED: Render contextual guidance with proper error handling."""
        try:
            # Try to get workflow context
            try:
                from utils.workflow_state_manager import WorkflowStateManager
                context = WorkflowStateManager.get_workflow_context()
                action_type, message = WorkflowStateManager.get_next_recommended_action()
                
                if context.get("should_show_review_guidance", False):
                    next_step = t('next_step') if hasattr(st, 'session_state') else "Next Step"
                    st.info(f"👉 **{next_step}:** {message}")
                elif context.get("should_show_completion", False):
                    completed = t('completed') if hasattr(st, 'session_state') else "Completed"
                    st.success(f"🎉 **{completed}:** {message}")
                    
            except (ImportError, Exception) as e:
                logger.debug(f"Context guidance not available: {str(e)}")
                # No guidance shown if WorkflowStateManager is not available
                pass
                
        except Exception as e:
            logger.error(f"Error rendering context guidance: {str(e)}")
            # Fail silently for guidance component

# ALTERNATIVE: Simple Progress Indicator (if above still fails)
class SimpleProgressIndicator:
    """Simplified progress indicator using only Streamlit components."""
    
    @staticmethod
    def render_simple_progress():
        """Render progress using only Streamlit native components."""
        try:
            # Header
            st.markdown("### 🎯 Your Learning Journey")
            
            # Get status safely
            try:
                from utils.workflow_state_manager import WorkflowStateManager
                status = WorkflowStateManager.get_workflow_status()
            except:
                status = "not_started"
            
            # Progress steps
            steps = [
                ("🔧", "Generate Code", "not_started"),
                ("📋", "Review Code", "code_generated"), 
                ("📊", "Get Feedback", "review_completed")
            ]
            
            # Create columns for progress
            cols = st.columns(len(steps))
            
            for i, (icon, label, required_status) in enumerate(steps):
                with cols[i]:
                    if status == required_status or (required_status == "code_generated" and status in ["code_generated", "review_in_progress", "review_completed"]) or (required_status == "review_completed" and status == "review_completed"):
                        # Current step
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: rgba(40,167,69,0.1); border-radius: 8px; border: 2px solid #28a745;">
                            <div style="font-size: 2rem;">{icon}</div>
                            <div style="font-weight: bold; color: #28a745;">{label}</div>
                            <div style="font-size: 0.8rem; color: #28a745;">Active</div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif i < steps.index(next((s for s in steps if s[2] == status), steps[0])):
                        # Completed step
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: rgba(40,167,69,0.05); border-radius: 8px;">
                            <div style="font-size: 2rem;">✅</div>
                            <div style="font-weight: bold; color: #155724;">{label}</div>
                            <div style="font-size: 0.8rem; color: #155724;">Completed</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Pending step
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: rgba(108,117,125,0.05); border-radius: 8px;">
                            <div style="font-size: 2rem; opacity: 0.5;">{icon}</div>
                            <div style="color: #6c757d;">{label}</div>
                            <div style="font-size: 0.8rem; color: #6c757d;">Pending</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        except Exception as e:
            logger.error(f"Error in simple progress indicator: {str(e)}")
            # Ultimate fallback
            st.info("🎯 **Learning Progress:** Generate Code → Review Code → Get Feedback")