# ui/components/code_simulator.py
"""
Code Simulator with Step-through Debugger for Java Peer Review Training System.

This module provides an interactive code simulator that allows students to:
- Step through code execution line by line
- Visualize memory state and variable changes
- Understand how errors manifest during execution
- Track execution flow and identify problematic paths
"""

import streamlit as st
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from utils.language_utils import t

logger = logging.getLogger(__name__)

@dataclass
class VariableState:
    """Represents the state of a variable at a point in execution."""
    name: str
    value: Any
    type_name: str
    scope: str
    line_created: int
    last_modified: int

@dataclass
class ExecutionFrame:
    """Represents a frame in the execution stack."""
    method_name: str
    line_number: int
    variables: Dict[str, VariableState] = field(default_factory=dict)
    local_scope: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionState:
    """Represents the complete execution state at a point in time."""
    current_line: int
    call_stack: List[ExecutionFrame] = field(default_factory=list)
    heap_objects: Dict[str, Dict] = field(default_factory=dict)
    output_buffer: List[str] = field(default_factory=list)
    error_occurred: bool = False
    error_message: str = ""
    execution_path: List[int] = field(default_factory=list)

class CodeSimulator:
    """
    Interactive code simulator with step-through debugging capabilities.
    """
    
    def __init__(self):
        self.execution_states: List[ExecutionState] = []
        self.current_step = 0
        self.breakpoints: List[int] = []
        
        # Initialize session state
        if "simulator_state" not in st.session_state:
            st.session_state.simulator_state = {
                "loaded_code": None,
                "execution_states": [],
                "current_step": 0,
                "is_running": False,
                "breakpoints": [],
                "watch_variables": [],
                "execution_speed": 1.0
            }
    
    def render(self, code_snippet: str, known_errors: List[str] = None):
        """
        Render the code simulator interface.
        
        Args:
            code_snippet: Java code to simulate
            known_errors: List of known errors in the code
        """
        try:
            st.markdown(f"## 🔬 {t('code_simulator')}")
            st.info(t("simulator_description"))
            
            # Simulator controls
            self._render_simulator_controls(code_snippet)
            
            # Main simulator interface
            col1, col2 = st.columns([2, 1])
            
            with col1:
                self._render_code_view(code_snippet)
            
            with col2:
                self._render_execution_panel()
            
            # Memory and variable visualization
            self._render_memory_visualization()
            
            # Execution flow diagram
            self._render_execution_flow()
            
        except Exception as e:
            logger.error(f"Error rendering code simulator: {str(e)}")
            st.error(f"{t('simulator_error')}: {str(e)}")
    
    def _render_simulator_controls(self, code_snippet: str):
        """Render simulator control panel."""
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("▶️ " + t("start_simulation"), key="start_sim"):
                self._start_simulation(code_snippet)
        
        with col2:
            if st.button("⏸️ " + t("pause"), key="pause_sim"):
                st.session_state.simulator_state["is_running"] = False
        
        with col3:
            if st.button("⏭️ " + t("step_over"), key="step_over"):
                self._step_execution()
        
        with col4:
            if st.button("⏬ " + t("step_into"), key="step_into"):
                self._step_into()
        
        with col5:
            if st.button("🔄 " + t("reset"), key="reset_sim"):
                self._reset_simulation()
        
        # Speed control
        speed = st.slider(
            t("execution_speed"), 
            min_value=0.1, 
            max_value=3.0, 
            value=1.0, 
            step=0.1,
            key="sim_speed"
        )
        st.session_state.simulator_state["execution_speed"] = speed
        
        # Breakpoint management
        self._render_breakpoint_controls()
    
    def _render_code_view(self, code_snippet: str):
        """Render code view with execution highlighting."""
        
        st.subheader(t("code_execution_view"))
        
        if not code_snippet:
            st.info(t("no_code_loaded"))
            return
        
        # Get current execution state
        current_step = st.session_state.simulator_state["current_step"]
        execution_states = st.session_state.simulator_state["execution_states"]
        
        current_line = 0
        if execution_states and current_step < len(execution_states):
            current_line = execution_states[current_step].current_line
        
        # Render code with line numbers and highlighting
        lines = code_snippet.split('\n')
        code_html = self._build_code_html(lines, current_line)
        
        st.markdown(code_html, unsafe_allow_html=True)
        
        # Show current execution context
        if execution_states and current_step < len(execution_states):
            current_state = execution_states[current_step]
            if current_state.error_occurred:
                st.error(f"💥 {t('runtime_error')}: {current_state.error_message}")
    
    def _render_execution_panel(self):
        """Render execution status and controls panel."""
        
        st.subheader(t("execution_status"))
        
        sim_state = st.session_state.simulator_state
        execution_states = sim_state["execution_states"]
        current_step = sim_state["current_step"]
        
        if not execution_states:
            st.info(t("simulation_not_started"))
            return
        
        # Execution progress
        progress = current_step / max(len(execution_states) - 1, 1)
        st.progress(progress)
        
        # Current state info
        if current_step < len(execution_states):
            current_state = execution_states[current_step]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(t("current_line"), current_state.current_line)
            with col2:
                st.metric(t("execution_step"), f"{current_step + 1}/{len(execution_states)}")
            
            # Call stack
            st.subheader(t("call_stack"))
            if current_state.call_stack:
                for i, frame in enumerate(reversed(current_state.call_stack)):
                    indent = "  " * i
                    st.text(f"{indent}📍 {frame.method_name}() : {t('line')} {frame.line_number}")
            else:
                st.info(t("no_active_methods"))
            
            # Output buffer
            if current_state.output_buffer:
                st.subheader(t("program_output"))
                for output in current_state.output_buffer:
                    st.code(output)
    
    def _render_memory_visualization(self):
        """Render memory and variable state visualization."""
        
        st.subheader(t("memory_visualization"))
        
        sim_state = st.session_state.simulator_state
        execution_states = sim_state["execution_states"]
        current_step = sim_state["current_step"]
        
        if not execution_states or current_step >= len(execution_states):
            st.info(t("no_memory_data"))
            return
        
        current_state = execution_states[current_step]
        
        # Variable watch list
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📊 " + t("variable_states"))
            
            # Show variables from current frame
            if current_state.call_stack:
                current_frame = current_state.call_stack[-1]
                
                if current_frame.variables:
                    # Create variable table
                    var_data = []
                    for var_name, var_state in current_frame.variables.items():
                        var_data.append({
                            t("name"): var_name,
                            t("value"): str(var_state.value),
                            t("type"): var_state.type_name,
                            t("scope"): var_state.scope
                        })
                    
                    # Display as table
                    import pandas as pd
                    df = pd.DataFrame(var_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(t("no_variables_in_scope"))
            
            # Heap objects visualization
            if current_state.heap_objects:
                st.markdown("### 🗄️ " + t("heap_objects"))
                
                for obj_id, obj_data in current_state.heap_objects.items():
                    with st.expander(f"Object {obj_id}: {obj_data.get('type', 'Unknown')}"):
                        st.json(obj_data)
        
        with col2:
            st.markdown("### 👁️ " + t("watch_variables"))
            
            # Watch variable input
            new_watch = st.text_input(
                t("add_variable_to_watch"), 
                key="new_watch_var"
            )
            
            if st.button(t("add_watch"), key="add_watch_btn") and new_watch:
                if new_watch not in sim_state["watch_variables"]:
                    sim_state["watch_variables"].append(new_watch)
                    st.rerun()
            
            # Display watched variables
            for var_name in sim_state["watch_variables"]:
                self._render_watch_variable(var_name, current_state)
    
    def _render_execution_flow(self):
        """Render execution flow diagram."""
        
        st.subheader(t("execution_flow"))
        
        sim_state = st.session_state.simulator_state
        execution_states = sim_state["execution_states"]
        current_step = sim_state["current_step"]
        
        if not execution_states:
            st.info(t("no_execution_data"))
            return
        
        # Build execution path
        execution_path = []
        for i, state in enumerate(execution_states[:current_step + 1]):
            execution_path.append(state.current_line)
        
        # Visualize execution path
        if execution_path:
            st.markdown("### 🛤️ " + t("execution_path"))
            
            # Create flow visualization
            path_html = self._build_execution_path_html(execution_path)
            st.markdown(path_html, unsafe_allow_html=True)
            
            # Show branching and loops
            self._analyze_execution_patterns(execution_path)
    
    def _start_simulation(self, code_snippet: str):
        """Start code simulation by generating execution states."""
        
        try:
            # Reset simulation state
            self._reset_simulation()
            
            # Parse and simulate code execution
            execution_states = self._simulate_code_execution(code_snippet)
            
            # Store in session state
            st.session_state.simulator_state.update({
                "loaded_code": code_snippet,
                "execution_states": execution_states,
                "current_step": 0,
                "is_running": True
            })
            
            st.success(f"{t('simulation_started')} - {len(execution_states)} {t('steps_generated')}")
            
        except Exception as e:
            logger.error(f"Error starting simulation: {str(e)}")
            st.error(f"{t('simulation_start_error')}: {str(e)}")
    
    def _step_execution(self):
        """Advance execution by one step."""
        
        sim_state = st.session_state.simulator_state
        execution_states = sim_state["execution_states"]
        current_step = sim_state["current_step"]
        
        if current_step < len(execution_states) - 1:
            sim_state["current_step"] = current_step + 1
            st.rerun()
        else:
            st.info(t("execution_completed"))
    
    def _step_into(self):
        """Step into method calls (detailed execution)."""
        
        # For now, same as step over
        # In full implementation, this would step into method bodies
        self._step_execution()
    
    def _reset_simulation(self):
        """Reset simulation to initial state."""
        
        st.session_state.simulator_state.update({
            "execution_states": [],
            "current_step": 0,
            "is_running": False
        })
    
    def _simulate_code_execution(self, code_snippet: str) -> List[ExecutionState]:
        """
        Simulate code execution and generate execution states.
        This is a simplified simulation for demonstration.
        """
        
        execution_states = []
        lines = code_snippet.split('\n')
        
        # Create initial state
        initial_state = ExecutionState(
            current_line=1,
            call_stack=[ExecutionFrame("main", 1)]
        )
        execution_states.append(initial_state)
        
        # Simulate line-by-line execution
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Create new state for each line
            prev_state = execution_states[-1]
            new_state = ExecutionState(
                current_line=i,
                call_stack=prev_state.call_stack.copy(),
                heap_objects=prev_state.heap_objects.copy(),
                output_buffer=prev_state.output_buffer.copy(),
                execution_path=prev_state.execution_path + [i]
            )
            
            # Simulate line execution effects
            self._simulate_line_execution(line, i, new_state)
            
            execution_states.append(new_state)
            
            # Stop if error occurred
            if new_state.error_occurred:
                break
        
        return execution_states
    
    def _simulate_line_execution(self, line: str, line_number: int, state: ExecutionState):
        """Simulate the execution of a single line of code."""
        
        # This is a simplified simulation
        # In a full implementation, this would parse Java syntax and simulate execution
        
        current_frame = state.call_stack[-1] if state.call_stack else None
        if not current_frame:
            return
        
        # Simulate variable declarations
        if 'int ' in line and '=' in line:
            # Extract variable name and value
            parts = line.split('=')
            if len(parts) == 2:
                var_part = parts[0].replace('int', '').strip()
                value_part = parts[1].strip().rstrip(';')
                
                try:
                    value = int(value_part) if value_part.isdigit() else 0
                    current_frame.variables[var_part] = VariableState(
                        name=var_part,
                        value=value,
                        type_name="int",
                        scope="local",
                        line_created=line_number,
                        last_modified=line_number
                    )
                except:
                    pass
        
        # Simulate array access errors
        if '[' in line and ']' in line and ('array' in line or 'list' in line):
            # Check for potential array bounds errors
            if '<=' in line or '>' in line:
                state.error_occurred = True
                state.error_message = "ArrayIndexOutOfBoundsException: Index out of bounds"
        
        # Simulate null pointer errors
        if '.get' in line or '.set' in line:
            if 'null' in line.lower():
                state.error_occurred = True
                state.error_message = "NullPointerException: Cannot invoke method on null object"
        
        # Simulate output
        if 'System.out.print' in line:
            output_text = f"Output at line {line_number}: [simulated output]"
            state.output_buffer.append(output_text)
    
    def _build_code_html(self, lines: List[str], current_line: int) -> str:
        """Build HTML for code display with highlighting."""
        
        html_parts = ['<div class="code-simulator-view">']
        breakpoints = st.session_state.simulator_state["breakpoints"]
        
        for i, line in enumerate(lines, 1):
            line_class = "code-line"
            
            # Highlight current line
            if i == current_line:
                line_class += " current-line"
            
            # Show breakpoints
            if i in breakpoints:
                line_class += " breakpoint-line"
            
            # Add line number and content
            html_parts.append(f'''
            <div class="{line_class}" onclick="toggleBreakpoint({i})">
                <span class="line-number">{i:3d}</span>
                <span class="line-content">{line}</span>
            </div>
            ''')
        
        html_parts.append('</div>')
        
        # Add CSS
        css = '''
        <style>
        .code-simulator-view {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        }
        .code-line {
            display: flex;
            padding: 2px 0;
            cursor: pointer;
        }
        .code-line:hover {
            background-color: #e9ecef;
        }
        .current-line {
            background-color: #fff3cd !important;
            border-left: 4px solid #ffc107;
        }
        .breakpoint-line {
            background-color: #f8d7da !important;
            border-left: 4px solid #dc3545;
        }
        .line-number {
            color: #6c757d;
            margin-right: 10px;
            user-select: none;
        }
        .line-content {
            white-space: pre;
        }
        </style>
        
        <script>
        function toggleBreakpoint(lineNumber) {
            // This would be handled by Streamlit callbacks in practice
            console.log('Toggle breakpoint at line:', lineNumber);
        }
        </script>
        '''
        
        return css + ''.join(html_parts)
    
    def _render_breakpoint_controls(self):
        """Render breakpoint management controls."""
        
        st.markdown("### 🔴 " + t("breakpoints"))
        
        breakpoints = st.session_state.simulator_state["breakpoints"]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            new_breakpoint = st.number_input(
                t("add_breakpoint_line"), 
                min_value=1, 
                value=1,
                key="new_breakpoint"
            )
        
        with col2:
            if st.button(t("add_breakpoint"), key="add_bp_btn"):
                if new_breakpoint not in breakpoints:
                    breakpoints.append(new_breakpoint)
                    st.rerun()
        
        # Display current breakpoints
        if breakpoints:
            for i, bp in enumerate(breakpoints):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"🔴 {t('line')} {bp}")
                with col2:
                    if st.button("❌", key=f"remove_bp_{i}"):
                        breakpoints.remove(bp)
                        st.rerun()
    
    def _render_watch_variable(self, var_name: str, current_state: ExecutionState):
        """Render a watched variable's current value."""
        
        # Find variable in current frame
        value = "undefined"
        if current_state.call_stack:
            current_frame = current_state.call_stack[-1]
            if var_name in current_frame.variables:
                var_state = current_frame.variables[var_name]
                value = str(var_state.value)
        
        st.text(f"👁️ {var_name}: {value}")
    
    def _build_execution_path_html(self, execution_path: List[int]) -> str:
        """Build HTML visualization of execution path."""
        
        if not execution_path:
            return ""
        
        # Group consecutive lines
        path_segments = []
        current_segment = [execution_path[0]]
        
        for line_num in execution_path[1:]:
            if line_num == current_segment[-1] + 1:
                current_segment.append(line_num)
            else:
                path_segments.append(current_segment)
                current_segment = [line_num]
        
        path_segments.append(current_segment)
        
        # Build HTML representation
        html_parts = ['<div class="execution-path">']
        
        for i, segment in enumerate(path_segments):
            if len(segment) == 1:
                html_parts.append(f'<span class="path-line">L{segment[0]}</span>')
            else:
                html_parts.append(f'<span class="path-segment">L{segment[0]}-{segment[-1]}</span>')
            
            if i < len(path_segments) - 1:
                html_parts.append('<span class="path-arrow">→</span>')
        
        html_parts.append('</div>')
        
        css = '''
        <style>
        .execution-path {
            font-family: monospace;
            background: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .path-line, .path-segment {
            background: #007bff;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            margin: 0 2px;
        }
        .path-arrow {
            color: #6c757d;
            margin: 0 5px;
        }
        </style>
        '''
        
        return css + ''.join(html_parts)
    
    def _analyze_execution_patterns(self, execution_path: List[int]):
        """Analyze execution patterns for loops and branches."""
        
        # Find loops (repeated line numbers)
        line_counts = {}
        for line_num in execution_path:
            line_counts[line_num] = line_counts.get(line_num, 0) + 1
        
        loops = {line: count for line, count in line_counts.items() if count > 1}
        
        if loops:
            st.markdown("#### 🔄 " + t("detected_loops"))
            for line, iterations in loops.items():
                st.text(f"Line {line}: {iterations} iterations")
        
        # Find jumps (non-sequential execution)
        jumps = []
        for i in range(1, len(execution_path)):
            prev_line = execution_path[i-1]
            curr_line = execution_path[i]
            if abs(curr_line - prev_line) > 1:
                jumps.append((prev_line, curr_line))
        
        if jumps:
            st.markdown("#### ↗️ " + t("execution_jumps"))
            for from_line, to_line in jumps:
                jump_type = t("forward_jump") if to_line > from_line else t("backward_jump")
                st.text(f"Line {from_line} → Line {to_line} ({jump_type})")