CREATE TABLE error_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_code VARCHAR(50) NOT NULL UNIQUE,
    language VARCHAR(20) NOT NULL DEFAULT 'Java',
    title VARCHAR(255) NOT NULL,
    detailed_description_md TEXT,
    example_good_code_md TEXT,
    example_bad_code_md TEXT,
    before_after_comparison_md TEXT,
    common_misconceptions_md TEXT,
    importance_explanation_md TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
