"""
Comparison Report Renderer Module

This module provides functionality to render comparison reports in a professional 
layout with enhanced styling for Java peer review feedback.
"""

import streamlit as st
import json
import re
import logging
from typing import Dict, Any, Optional
from utils.language_utils import t

logger = logging.getLogger(__name__)

class ComparisonReportRenderer:
    """
    A class responsible for rendering comparison reports with professional styling.
    Handles JSON parsing, data extraction, and formatted display of review feedback.
    """
    
    def __init__(self):
        """Initialize the comparison report renderer."""
        pass
    
    def render_comparison_report(self, comparison_report: str) -> None:
        """
        Extract and render the comparison report JSON with professional layout.
        CSS styles are loaded from external files.
        
        Args:
            comparison_report: The raw comparison report string containing JSON data
        """
        # Extract JSON object from the report
        report_data = self._extract_json_from_report(comparison_report)
        
        if not report_data:
            st.warning("No valid comparison report found.")
            return
        
        # Render the complete comparison report
        self._render_complete_report(report_data)
    
    def _extract_json_from_report(self, comparison_report: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from the comparison report string.
        
        Args:
            comparison_report: The raw comparison report string
            
        Returns:
            Dict containing the parsed report data, or None if parsing fails
        """
        json_text = ""
        
        if "=== RESPONSE ===" in comparison_report:
            # If the report is a full LLM log, extract after marker
            json_text = comparison_report.split("=== RESPONSE ===", 1)[-1].strip()
        else:
            # Otherwise, try to find the first JSON object in the string
            match = re.search(r'\{[\s\S]+\}', comparison_report)
            if match:
                json_text = match.group(0)
            else:
                return None

        # Try to parse JSON
        try:
            report_data = json.loads(json_text)
            logger.debug(f"Parsed comparison report: {report_data}")
            return report_data
        except Exception as e:
            logger.error(f"Failed to parse comparison report: {e}")
            st.error(f"Failed to parse comparison report: {e}")
            st.code(json_text)
            return None
    
    def _render_complete_report(self, report_data: Dict[str, Any]) -> None:
        """
        Render the complete comparison report with all sections.
        
        Args:
            report_data: The parsed report data dictionary
        """
        st.markdown('<div class="comparison-report-container">', unsafe_allow_html=True)
        
        # Render each section
        self._render_performance_summary(report_data)
        self._render_identified_issues(report_data)
        self._render_missed_issues(report_data)
        self._render_improvement_tips(report_data)
        self._render_java_guidance(report_data)
        self._render_encouragement_section(report_data)
        self._render_detailed_feedback(report_data)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_performance_summary(self, report_data: Dict[str, Any]) -> None:
        """Render the performance summary section."""
        summary = report_data.get("performance_summary", {})
        
        # Performance metrics grid
        total_issues = summary.get('total_issues', 0)
        identified_count = summary.get('identified_count', 0)
        accuracy = summary.get('accuracy_percentage', 0)
        missed_count = summary.get('missed_count', 0)
        
        st.markdown(f'''
        <div class="comparison-section-title">📊 {t("review_performance_summary")}</div>
        <div class="comparison-metrics-grid">
            <div class="comparison-metric-card">
                <div class="comparison-metric-value">{total_issues}</div>
                <div class="comparison-metric-label">{t('total_issues')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value success-highlight">{identified_count}</div>
                <div class="comparison-metric-label">{t('identified_count')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value {'success-highlight' if accuracy >= 80 else 'warning-highlight' if accuracy >= 60 else 'error-highlight'}">{accuracy}%</div>
                <div class="comparison-metric-label">{t('accuracy')}</div>
            </div>
            <div class="comparison-metric-card">
                <div class="comparison-metric-value {'success-highlight' if missed_count == 0 else 'error-highlight'}">{missed_count}</div>
                <div class="comparison-metric-label">{t('missed_count')}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Overall assessment card
        overall_assessment = summary.get('overall_assessment', '')
        completion_status = summary.get('completion_status', '')
        if overall_assessment or completion_status:
            st.markdown(f'''
            <div class="comparison-encouragement">
                <strong>{t('overall_assessment')}:</strong> {overall_assessment}<br>
                <strong>{t('completion_status')}:</strong> {completion_status}
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    def _render_identified_issues(self, report_data: Dict[str, Any]) -> None:
        """Render the correctly identified issues section."""
        identified = report_data.get("correctly_identified_issues", [])
        st.markdown(f'<div class="comparison-section-title">✅ {t("correctly_identified_issues")}</div>', unsafe_allow_html=True)
        
        if identified:
            st.markdown('<ul class="comparison-issue-list">', unsafe_allow_html=True)
            for issue in identified:
                desc = issue.get("issue_description", "")
                praise = issue.get("praise_comment", "")
                st.markdown(f'<li class="success-item"><span class="comparison-badge">✅ {t("found")}</span> {desc}<div class="comparison-praise">🌟 {praise}</div></li>', unsafe_allow_html=True)
            st.markdown('</ul>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="comparison-tip">🔍 {t("no_identified_issues")}</div>', unsafe_allow_html=True)
    
    def _render_missed_issues(self, report_data: Dict[str, Any]) -> None:
        """Render the missed issues section."""
        missed = report_data.get("missed_issues", [])
        st.markdown(f'<div class="comparison-section-title">❌ {t("missed_issues")}</div>', unsafe_allow_html=True)
        
        if missed:
            st.markdown('<ul class="comparison-issue-list">', unsafe_allow_html=True)
            for issue in missed:
                desc = issue.get("issue_description", "")
                why = issue.get("why_important", "")
                how = issue.get("how_to_find", "")
                st.markdown(f'<li class="error-item"><span class="comparison-badge">❌ {t("missed")}</span> {desc}<div class="comparison-missed">❗ <strong>{t("why_important")}:</strong> {why}<br>🔍 <strong>{t("how_to_find")}:</strong> {how}</div></li>', unsafe_allow_html=True)
            st.markdown('</ul>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="comparison-encouragement">🎉 {t("all_issues_found")}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    def _render_improvement_tips(self, report_data: Dict[str, Any]) -> None:
        """Render the tips for improvement section."""
        tips = report_data.get("tips_for_improvement", [])
        if tips:
            st.markdown(f'<div class="comparison-section-title">💡 {t("tips_for_improvement")}</div>', unsafe_allow_html=True)
            for tip in tips:
                st.markdown(
                    f'<div class="comparison-tip"><strong>{tip.get("category", "")}:</strong> {tip.get("tip", "")}<br><em>💭 {t("example")}: {tip.get("example", "")}</em></div>',
                    unsafe_allow_html=True
                )
    
    def _render_java_guidance(self, report_data: Dict[str, Any]) -> None:
        """Render the Java-specific guidance section."""
        java_guidance = report_data.get("java_specific_guidance", [])
        if java_guidance:
            st.markdown(f'<div class="comparison-section-title">☕ {t("java_specific_guidance")}</div>', unsafe_allow_html=True)
            for item in java_guidance:
                st.markdown(
                    f'<div class="comparison-tip"><strong>☕ {item.get("topic", "")}:</strong> {item.get("guidance", "")}</div>',
                    unsafe_allow_html=True
                )
    
    def _render_encouragement_section(self, report_data: Dict[str, Any]) -> None:
        """Render the encouragement and next steps section."""
        encouragement = report_data.get("encouragement_and_next_steps", {})
        if encouragement:
            st.markdown(f'<div class="comparison-section-title">🎯 {t("encouragement_and_next_steps")}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="comparison-encouragement">'
                f'<strong>🌟 {t("positive_feedback")}:</strong> {encouragement.get("positive_feedback", "")}<br><br>'
                f'<strong>🎯 {t("next_focus_areas")}:</strong> {encouragement.get("next_focus_areas", "")}<br><br>'
                f'<strong>📚 {t("learning_objectives")}:</strong> {encouragement.get("learning_objectives", "")}'
                f'</div>',
                unsafe_allow_html=True
            )
    
    def _render_detailed_feedback(self, report_data: Dict[str, Any]) -> None:
        """Render the detailed feedback section."""
        detailed = report_data.get("detailed_feedback", {})
        if detailed:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="comparison-section-title">📝 {t("detailed_feedback")}</div>', unsafe_allow_html=True)
            
            strengths = detailed.get("strengths_identified", [])
            patterns = detailed.get("improvement_patterns", [])
            approach = detailed.get("review_approach_feedback", "")
            
            if strengths:
                st.markdown(f'<strong>💪 {t("strengths_identified")}:</strong>', unsafe_allow_html=True)
                st.markdown('<ul class="comparison-feedback-list">' + ''.join(f'<li>✨ {s}</li>' for s in strengths) + '</ul>', unsafe_allow_html=True)
            
            if patterns:
                st.markdown(f'<strong>📈 {t("improvement_patterns")}:</strong>', unsafe_allow_html=True)
                st.markdown('<ul class="comparison-feedback-list">' + ''.join(f'<li>📊 {p}</li>' for p in patterns) + '</ul>', unsafe_allow_html=True)
            
            if approach:
                st.markdown(f'<div class="comparison-tip"><strong>🔍 {t("review_approach_feedback")}:</strong> {approach}</div>', unsafe_allow_html=True)
