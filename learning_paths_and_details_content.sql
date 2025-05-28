-- A. Content for error_details for 'STRING_COMPARE_REF'
INSERT INTO error_details (error_code, language, title, detailed_description_md, example_good_code_md, example_bad_code_md, before_after_comparison_md, common_misconceptions_md, importance_explanation_md) VALUES (
    'STRING_COMPARE_REF',
    'Java',
    'String Comparison by Reference',
    'In Java, using `==` to compare strings checks if they are the exact same object in memory (reference equality). It does not check if their contents (character sequences) are the same (value equality). This often leads to bugs because two strings can have identical content but be different objects. Always use `.equals()` for value comparison of strings. Also, be mindful of `null` strings when calling `.equals()`.',
    '```java
String s1 = "hello";
String s2 = new String("hello");
String s3 = null;

// Correct way using .equals()
if (s1.equals(s2)) { System.out.println("s1 and s2 have same content."); }

// Safe way with potential nulls
if ("hello".equals(s1)) { /* ... */ }
if (s1 != null && s1.equals(s3)) { /* ... */ } else if (s1 == null && s3 == null) { /* Both null considered equal */ }
```',
    '```java
String s1 = "test";
String s2 = new String("test");
String s3 = "test";

if (s1 == s2) { System.out.println("s1 == s2 is TRUE"); } else { System.out.println("s1 == s2 is FALSE"); } // Usually FALSE
if (s1 == s3) { System.out.println("s1 == s3 is TRUE"); } else { System.out.println("s1 == s3 is FALSE"); } // Often TRUE due to string interning, but unreliable
```',
    '**Before (Problem):**
```java
String command = getCommand();
if (command == "LOGIN") {
    // Attempt login
}
```
**After (Fix):**
```java
String command = getCommand();
if ("LOGIN".equals(command)) { // Handles command being null safely
    // Attempt login
}
// Or: if (command != null && command.equals("LOGIN"))
```',
    '- That `==` works for strings because it sometimes appears to (due to string interning for literals).\n- Forgetting to check for `null` before calling `.equals()` on a variable that might be null.',
    'Incorrect string comparison can lead to unpredictable behavior, security vulnerabilities (if used for checks), and logic errors that are hard to track down because the code might seem to work in some specific cases (due to interning) but fail in others.'
);

-- B. Steps for "Java Error Fundamentals" (path_id=1)
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    1, 1, 'Deep Dive: NullPointerExceptions', 'Learn what causes NullPointerExceptions and how to prevent them by understanding object initialization and null checks. This module covers common scenarios where NPEs occur and best practices for writing robust code.', 'ERROR_DETAIL_STUDY', 'NULL_POINTER', 20
);
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    1, 2, 'Game: Spot the Missing Null Check', 'Practice identifying code patterns that are likely to cause NullPointerExceptions. This interactive game will test your ability to find missing null checks before accessing object members.', 'PATTERN_GAME', 'missing_null_check', 15
);
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    1, 3, 'Deep Dive: ArrayIndexOutOfBoundsExceptions', 'Explore array indexing in Java, the causes of ArrayIndexOutOfBoundsExceptions, and how to use loops and access array elements safely.', 'ERROR_DETAIL_STUDY', 'ARRAY_INDEX_OUT_OF_BOUNDS', 20
);
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    1, 4, 'Game: Spot the Array Boundary Error', 'Practice identifying common off-by-one errors and other incorrect array indexing patterns that lead to ArrayIndexOutOfBoundsExceptions.', 'PATTERN_GAME', 'array_out_of_bounds', 15
);

-- C. Steps for "Java String Handling Essentials" (path_id=2)
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    2, 1, 'Deep Dive: String Comparison Pitfalls', 'Understand why using `==` to compare strings can lead to bugs. Learn the difference between reference equality and value equality for String objects.', 'ERROR_DETAIL_STUDY', 'STRING_COMPARE_REF', 20
);
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    2, 2, 'Game: Spot Incorrect String Comparisons', 'Practice identifying code where strings are incorrectly compared using `==` instead of `.equals()`. This game will help you recognize this common pitfall.', 'PATTERN_GAME', 'string_comparison_by_ref', 15
);
INSERT INTO learning_path_steps (path_id, step_order, title, description_md, step_type, content_reference, estimated_time_minutes) VALUES (
    2, 3, 'Recap: Correct String Comparisons', 'Review the key principles for accurately comparing strings in Java, including using `.equals()` and handling potential null values to prevent NullPointerExceptions.', 'ERROR_DETAIL_STUDY', 'STRING_COMPARE_REF', 10
);
