# examples/database_repository_usage.py
"""
Comprehensive examples of using the new DatabaseErrorRepository.

This file demonstrates the key features and usage patterns of the database-based
error repository system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database_error_repository import DatabaseErrorRepository
from utils.language_utils import set_language, get_current_language, t
import json

def example_basic_usage():
    """Basic usage examples."""
    print("=== Basic Usage Examples ===")
    
    # Create repository instance
    repo = DatabaseErrorRepository()
    
    # Get all categories
    categories = repo.get_all_categories()
    print(f"Available categories: {categories}")
    
    # Get errors for a specific category
    if categories["java_errors"]:
        first_category = categories["java_errors"][0]
        errors = repo.get_category_errors(first_category)
        print(f"\nErrors in '{first_category}': {len(errors)}")
        
        if errors:
            print(f"First error: {errors[0]['error_name']}")
    
    print()

def example_multilingual_support():
    """Demonstrate multilingual support."""
    print("=== Multilingual Support Examples ===")
    
    repo = DatabaseErrorRepository()
    
    # Test English
    set_language("en")
    print(f"Current language: {get_current_language()}")
    categories_en = repo.get_all_categories()
    print(f"Categories (EN): {categories_en['java_errors'][:3]}...")
    
    # Test Chinese
    set_language("zh")
    print(f"\nCurrent language: {get_current_language()}")
    categories_zh = repo.get_all_categories()
    print(f"Categories (ZH): {categories_zh['java_errors'][:3]}...")
    
    # Reset to English
    set_language("en")
    print()

def example_random_error_selection():
    """Demonstrate random error selection."""
    print("=== Random Error Selection Examples ===")
    
    repo = DatabaseErrorRepository()
    categories = repo.get_all_categories()
    
    if categories["java_errors"]:
        # Select random errors from multiple categories
        selected_categories = {
            "java_errors": categories["java_errors"][:3]  # First 3 categories
        }
        
        random_errors = repo.get_random_errors_by_categories(selected_categories, count=5)
        
        print(f"Selected {len(random_errors)} random errors:")
        for i, error in enumerate(random_errors, 1):
            print(f"{i}. {error['category']}: {error['name']}")
    
    print()

def example_llm_integration():
    """Demonstrate LLM integration features."""
    print("=== LLM Integration Examples ===")
    
    repo = DatabaseErrorRepository()
    categories = repo.get_all_categories()
    
    if categories["java_errors"]:
        # Get errors for LLM with different difficulty levels
        selected_categories = {
            "java_errors": categories["java_errors"][:2]
        }
        
        for difficulty in ["easy", "medium", "hard"]:
            errors, descriptions = repo.get_errors_for_llm(
                selected_categories=selected_categories,
                count=3,
                difficulty=difficulty
            )
            
            print(f"\n{difficulty.upper()} difficulty - {len(errors)} errors:")
            for desc in descriptions:
                print(f"  - {desc}")
    
    print()

def example_error_details():
    """Demonstrate getting detailed error information."""
    print("=== Error Details Examples ===")
    
    repo = DatabaseErrorRepository()
    categories = repo.get_all_categories()
    
    if categories["java_errors"]:
        # Get errors from first category
        first_category = categories["java_errors"][0]
        errors = repo.get_category_errors(first_category)
        
        if errors:
            first_error = errors[0]
            error_name = first_error['error_name']
            
            # Get detailed information
            details = repo.get_error_details("java_error", error_name)
            
            if details:
                print(f"Error: {details['error_name']}")
                print(f"Description: {details['description'][:100]}...")
                print(f"Implementation Guide: {details.get('implementation_guide', 'N/A')[:100]}...")
    
    print()

def example_usage_tracking():
    """Demonstrate usage tracking features."""
    print("=== Usage Tracking Examples ===")
    
    repo = DatabaseErrorRepository()
    
    # Simulate error usage tracking
    repo.update_error_usage(
        error_code="logical_off_by_one_error",
        user_id="test-user-123",
        action_type="viewed",
        context={"session_id": "session-456", "difficulty": "medium"}
    )
    
    repo.update_error_usage(
        error_code="syntax_missing_semicolons",
        user_id="test-user-123", 
        action_type="practiced",
        context={"score": 85, "time_spent": 120}
    )
    
    print("Usage tracking completed (simulated)")
    print()

def example_statistics():
    """Demonstrate statistics features."""
    print("=== Statistics Examples ===")
    
    repo = DatabaseErrorRepository()
    stats = repo.get_error_statistics()
    
    if stats:
        print(f"Total categories: {stats.get('total_categories', 0)}")
        print(f"Total errors: {stats.get('total_errors', 0)}")
        
        print("\nErrors by category:")
        for category, count in stats.get('errors_by_category', {}).items():
            print(f"  {category}: {count}")
        
        print("\nMost used errors:")
        for error in stats.get('most_used_errors', []):
            print(f"  {error['name']}: {error['usage_count']} uses")
    
    print()

def example_migration_compatibility():
    """Demonstrate backward compatibility features."""
    print("=== Migration Compatibility Examples ===")
    
    # Show that the new repository maintains the same interface
    repo = DatabaseErrorRepository()
    
    # These methods work exactly like the old JsonErrorRepository
    categories = repo.get_all_categories()
    print(f"✓ get_all_categories() works: {len(categories.get('java_errors', []))} categories")
    
    if categories["java_errors"]:
        errors = repo.get_category_errors(categories["java_errors"][0])
        print(f"✓ get_category_errors() works: {len(errors)} errors")
        
        random_errors = repo.get_random_errors_by_categories(
            {"java_errors": categories["java_errors"][:1]}, 
            count=2
        )
        print(f"✓ get_random_errors_by_categories() works: {len(random_errors)} errors")
        
        if errors:
            details = repo.get_error_details("java_error", errors[0]['error_name'])
            print(f"✓ get_error_details() works: {details is not None}")
    
    print("All legacy methods are fully compatible!")
    print()

def example_advanced_queries():
    """Demonstrate advanced database features."""
    print("=== Advanced Database Features ===")
    
    repo = DatabaseErrorRepository()
    
    # Example of using specific errors for LLM
    specific_errors = [
        {
            t("error_name_variable"): "Off-by-one error",
            t("description"): "An iteration error where a loop iterates one time too many or too few",
            t("category"): "Logical"
        },
        {
            t("error_name_variable"): "Missing semicolons", 
            t("description"): "Forgetting to terminate statements with semicolons",
            t("category"): "Syntax"
        }
    ]
    
    errors, descriptions = repo.get_errors_for_llm(specific_errors=specific_errors)
    
    print(f"Using specific errors for LLM: {len(descriptions)} descriptions")
    for desc in descriptions:
        print(f"  - {desc}")
    
    print()

def run_all_examples():
    """Run all examples."""
    print("🚀 Database Error Repository Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_multilingual_support()
        example_random_error_selection()
        example_llm_integration()
        example_error_details()
        example_usage_tracking()
        example_statistics()
        example_migration_compatibility()
        example_advanced_queries()
        
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()

def show_migration_benefits():
    """Show the benefits of the database approach."""
    print("\n📊 Benefits of Database-Based Repository:")
    print("-" * 40)
    print("✓ Better performance with indexing")
    print("✓ Advanced querying capabilities") 
    print("✓ Usage tracking and analytics")
    print("✓ Easier multilingual management")
    print("✓ Centralized data management")
    print("✓ Scalable for large datasets")
    print("✓ Backup and recovery features")
    print("✓ Concurrent access support")
    print()

if __name__ == "__main__":
    # Check if database tables exist
    try:
        repo = DatabaseErrorRepository()
        categories = repo.get_all_categories()
        
        if not categories or not categories.get("java_errors"):
            print("⚠️ Database tables not found or empty.")
            print("Please run the migration first:")
            print("  python db/enhanced_schema_update.py")
            print("  python migration/repository_migration.py")
            sys.exit(1)
            
    except Exception as e:
        print(f"⚠️ Database connection failed: {str(e)}")
        print("Please ensure:")
        print("1. MySQL is running")
        print("2. Database credentials are correct")
        print("3. Migration has been run")
        sys.exit(1)
    
    # Run examples
    run_all_examples()
    show_migration_benefits()
    
    print("\n🎯 Quick Start for New Projects:")
    print("-" * 30)
    print("from data import DatabaseErrorRepository")
    print("repo = DatabaseErrorRepository()")
    print("categories = repo.get_all_categories()")
    print()
    
    print("📚 For existing projects:")
    print("-" * 25)
    print("1. Run: python migration/repository_migration.py")
    print("2. Test your application")
    print("3. Remove JSON files when satisfied")