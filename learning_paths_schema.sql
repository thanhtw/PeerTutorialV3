-- Refined learning_paths Table
CREATE TABLE IF NOT EXISTS learning_paths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    path_name VARCHAR(100) NOT NULL,
    description_en TEXT,
    description_zh TEXT,
    difficulty_level VARCHAR(20) NOT NULL, /* e.g., 'Beginner', 'Intermediate', 'Advanced' */
    estimated_hours INT DEFAULT 0,
    prerequisites JSON, /* e.g., {"completed_paths": [1, 2], "min_level": "intermediate"} */
    skills_learned JSON, /* e.g., ["NULL_POINTER", "ARRAY_INDEX_OUT_OF_BOUNDS"] */
    path_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- New learning_path_steps Table
CREATE TABLE IF NOT EXISTS learning_path_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    path_id INT NOT NULL,
    step_order INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description_md TEXT, /* General instructions or introductory text for the step */
    step_type VARCHAR(50) NOT NULL, 
        /* Examples: 'ERROR_DETAIL_STUDY', 'PATTERN_GAME', 'GUIDED_PRACTICE', 'QUIZ', 'VIDEO', 'EXTERNAL_LINK' */
    content_reference VARCHAR(255) NULL, 
        /* Links to specific content: error_code for ERROR_DETAIL_STUDY, 
           error_type for PATTERN_GAME, exercise_id for GUIDED_PRACTICE, etc. */
    estimated_time_minutes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE
);

-- Refined user_learning_paths Table
CREATE TABLE IF NOT EXISTS user_learning_paths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    path_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started', /* e.g., 'not_started', 'in_progress', 'completed' */
    current_step_id INT NULL, /* FK to learning_path_steps.id */
    total_steps INT DEFAULT 0, /* Should be set upon enrollment based on path definition */
    progress_percentage FLOAT DEFAULT 0.0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE,
    FOREIGN KEY (current_step_id) REFERENCES learning_path_steps(id) ON DELETE SET NULL, /* If a step is deleted, nullify here */
    UNIQUE KEY (user_id, path_id)
);
