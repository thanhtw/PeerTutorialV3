import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import get_current_language, t

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove the entire CodeGeneratorUI class as it's duplicated and should only exist in code_generator.py