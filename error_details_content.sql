INSERT INTO error_details (error_code, language, title, detailed_description_md, example_good_code_md, example_bad_code_md, before_after_comparison_md, common_misconceptions_md, importance_explanation_md) VALUES (
    'NULL_POINTER',
    'Java',
    'Null Pointer Exception',
    'A NullPointerException (NPE) occurs when you try to access a member (like a method or field) of an object that is currently `null`. Since `null` means ''no object'', there are no members to access.',
    '```java
String text = "Hello";
if (text != null) {
    System.out.println(text.length());
}
// Or, ensure ''text'' is initialized
String text2 = "World";
System.out.println(text2.length());
```',
    '```java
String text = null;
System.out.println(text.length()); // Throws NullPointerException
```',
    '**Before (Problem):**
```java
String name = getSomeNameWhichMightBeNull();
System.out.println(name.toUpperCase());
```
**After (Fix):**
```java
String name = getSomeNameWhichMightBeNull();
if (name != null) {
    System.out.println(name.toUpperCase());
} else {
    System.out.println("Name is not available.");
}
```',
    '- That checking for `null` everywhere is always the best solution (sometimes it''s better to prevent `null` values earlier).\n- That an NPE always means your variable is `null`; it could be an object within a chain, like `a.b.c` where `b` is `null`.',
    'NPEs are one of the most common runtime exceptions in Java. They can crash your application or lead to unexpected behavior if not handled properly. Proactive checks and good initialization practices are key to preventing them.'
);

INSERT INTO error_details (error_code, language, title, detailed_description_md, example_good_code_md, example_bad_code_md, before_after_comparison_md, common_misconceptions_md, importance_explanation_md) VALUES (
    'ARRAY_INDEX_OUT_OF_BOUNDS',
    'Java',
    'Array Index Out Of Bounds Exception',
    'This exception occurs when you try to access an array element using an index that is outside the valid range of indices for that array. For an array of length `n`, valid indices are `0` to `n-1`.',
    '```java
int[] numbers = {10, 20, 30};
for (int i = 0; i < numbers.length; i++) {
    System.out.println(numbers[i]);
}
if (numbers.length > 0) {
    System.out.println(numbers[0]); // Accessing first element safely
}
```',
    '```java
int[] numbers = {10, 20, 30};
System.out.println(numbers[3]); // Throws ArrayIndexOutOfBoundsException (valid indices are 0, 1, 2)
System.out.println(numbers[-1]); // Throws ArrayIndexOutOfBoundsException
```',
    '**Before (Problem):**
```java
int[] data = new int[5];
for (int i = 0; i <= data.length; i++) { // Error: i <= data.length
    data[i] = i * 2;
}
```
**After (Fix):**
```java
int[] data = new int[5];
for (int i = 0; i < data.length; i++) { // Corrected: i < data.length
    data[i] = i * 2;
}
```',
    '- Confusing array length with the maximum valid index (max index is `length - 1`).\n- Off-by-one errors in loop conditions are a very common cause.',
    'Accessing invalid array indices can lead to program crashes or incorrect data manipulation. It often indicates a logical flaw in how data or loops are being handled.'
);
