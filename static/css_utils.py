"""
CSS utility functions for loading and managing CSS in Streamlit applications.
"""
import os
import streamlit as st

def load_css(css_file=None, css_directory=None):
    """
    Load CSS from file or directory into Streamlit.
    
    Args:
        css_file: Path to single CSS file
        css_directory: Path to directory containing CSS files
        
    Returns:
        List of loaded CSS file names or empty list if none loaded
    """
    css_content = ""
    loaded_files = []
    
    # Load single file if specified
    if css_file and os.path.exists(css_file):
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content += f.read()
                loaded_files.append(os.path.basename(css_file))
        except Exception as e:
            st.error(f"Error loading CSS file {css_file}: {str(e)}")
    
    # Load all CSS files from directory if specified
    if css_directory and os.path.exists(css_directory) and os.path.isdir(css_directory):
        try:
            # First load base.css if it exists
            base_css_path = os.path.join(css_directory, "base.css")
            if os.path.exists(base_css_path):
                with open(base_css_path, 'r', encoding='utf-8') as f:
                    css_content += f.read()
                    loaded_files.append("base.css")
            
            # Then load components.css
            components_css_path = os.path.join(css_directory, "components.css")
            if os.path.exists(components_css_path):
                with open(components_css_path, 'r', encoding='utf-8') as f:
                    css_content += f.read()
                    loaded_files.append("components.css")
            
            # Finally load tabs.css
            tabs_css_path = os.path.join(css_directory, "tabs.css")
            if os.path.exists(tabs_css_path):
                with open(tabs_css_path, 'r', encoding='utf-8') as f:
                    css_content += f.read()
                    loaded_files.append("tabs.css")
            
            # Load any remaining CSS files (except main.css which is now obsolete)
            for filename in sorted(os.listdir(css_directory)):
                if (filename.endswith('.css') and 
                    filename not in ["base.css", "components.css", "tabs.css", "main.css"]):
                    file_path = os.path.join(css_directory, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            css_content += f.read()
                            loaded_files.append(filename)
                    except UnicodeDecodeError as e:
                        # Try with different encodings as fallback
                        try:
                            with open(file_path, 'r', encoding='utf-8-sig') as f:
                                css_content += f.read()
                                loaded_files.append(filename)
                        except UnicodeDecodeError:
                            try:
                                with open(file_path, 'r', encoding='latin1') as f:
                                    css_content += f.read()
                                    loaded_files.append(filename)
                                st.warning(f"CSS file {filename} loaded with latin1 encoding")
                            except Exception as fallback_error:
                                st.error(f"Could not load CSS file {filename}: {str(fallback_error)}")
                    except Exception as e:
                        st.error(f"Error loading CSS file {filename}: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error loading CSS files from directory {css_directory}: {str(e)}")
    
    # Apply CSS if we loaded any
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        return loaded_files
    
    return []


def load_css_safe(css_file=None, css_directory=None, encoding='utf-8'):
    """
    Safe CSS loading function with better error handling and encoding options.
    
    Args:
        css_file: Path to single CSS file
        css_directory: Path to directory containing CSS files
        encoding: Text encoding to use (default: utf-8)
        
    Returns:
        Dictionary with 'success', 'loaded_files', and 'errors' keys
    """
    css_content = ""
    loaded_files = []
    errors = []
    
    def safe_read_file(file_path, filename):
        """Safely read a CSS file with multiple encoding attempts."""
        encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                    if enc != encoding:
                        st.info(f"CSS file {filename} loaded with {enc} encoding")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                errors.append(f"Error reading {filename}: {str(e)}")
                return None
        
        errors.append(f"Could not decode {filename} with any supported encoding")
        return None
    
    # Load single file if specified
    if css_file and os.path.exists(css_file):
        content = safe_read_file(css_file, os.path.basename(css_file))
        if content is not None:
            css_content += content
            loaded_files.append(os.path.basename(css_file))
    
    # Load all CSS files from directory if specified
    if css_directory and os.path.exists(css_directory) and os.path.isdir(css_directory):
        # Define loading order
        priority_files = ["base.css", "components.css", "tabs.css"]
        
        # Load priority files first
        for priority_file in priority_files:
            file_path = os.path.join(css_directory, priority_file)
            if os.path.exists(file_path):
                content = safe_read_file(file_path, priority_file)
                if content is not None:
                    css_content += content
                    loaded_files.append(priority_file)
        
        # Load remaining CSS files (except main.css which is obsolete)
        try:
            for filename in sorted(os.listdir(css_directory)):
                if (filename.endswith('.css') and 
                    filename not in priority_files + ["main.css"]):
                    file_path = os.path.join(css_directory, filename)
                    content = safe_read_file(file_path, filename)
                    if content is not None:
                        css_content += content
                        loaded_files.append(filename)
        except Exception as e:
            errors.append(f"Error listing directory {css_directory}: {str(e)}")
    
    # Apply CSS if we loaded any
    success = False
    if css_content:
        try:
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            success = True
        except Exception as e:
            errors.append(f"Error applying CSS: {str(e)}")
    
    return {
        'success': success,
        'loaded_files': loaded_files,
        'errors': errors
    }